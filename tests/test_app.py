from unittest import mock
from unittest.mock import patch, MagicMock
from chalice.test import Client
from app import app
from botocore.exceptions import ClientError
import json

def test_get_users():
    mock_request = MagicMock()
    mock_request.context = {
        'authorizer': {
            'claims': {
                'sub': 'user123',
                'email': 'user@example.com',
                'custom:custom:userRole': 'admin'
            }
        }
    }

    mock_users = [
        {
            "id": 1,
            "name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "document_type": "Cedula",
            "id_number": "123456",
            "client_id": 2,
            "user_role": "Admin"
        }
    ]

    with patch('chalicelib.src.modules.infrastructure.repository.UserRepositoryPostgres.get_all', return_value=mock_users):
        with Client(app) as client:
            response = client.http.get('/users/2')

            assert response.status_code == 200
            response_data = json.loads(response.body)
            assert response_data == mock_users


def test_get_user():
    mock_request = MagicMock()
    mock_request.context = {
        'authorizer': {
            'claims': {
                'sub': 'user123',
                'email': 'user@example.com',
                'custom:custom:userRole': 'admin'
            }
        }
    }

    mock_user = {
        "id": 1,
        "name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "document_type": "Cedula",
        "id_number": "123456",
        "client_id": 2,
        "user_role": "Admin"
    }

    with patch('chalicelib.src.modules.infrastructure.repository.UserRepositoryPostgres.get', return_value=mock_user):
        with Client(app) as client:
            response = client.http.get('/user/72c16f9f-5f13-439b-bf09-7440edd16086')

            assert response.status_code == 200
            response_data = json.loads(response.body)
            assert response_data == mock_user


def test_delete_user():
    with Client(app) as client:
        with patch('chalicelib.src.modules.infrastructure.repository.UserRepositoryPostgres.remove') as mock_remove:
            response = client.http.delete('/user/72c16f9f-5f13-439b-bf09-7440edd16086')

            assert response.status_code == 200
            response_data = json.loads(response.body)
            assert response_data == [{'status': 'success'}, 200]

            mock_remove.assert_called_once_with('72c16f9f-5f13-439b-bf09-7440edd16086')


def test_update_user():
    request_body = {
        "name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "document_type": "Cedula",
        "id_number": "654321",
        "client_id": 2,
        "user_role": "Admin"
    }

    with Client(app) as client:
        with patch('chalicelib.src.modules.infrastructure.repository.UserRepositoryPostgres.update') as mock_update:
            response = client.http.put(
                '/user/72c16f9f-5f13-439b-bf09-7440edd16086',
                headers={'Content-Type': 'application/json'},
                body=json.dumps(request_body)
            )

            assert response.status_code == 200

            response_data = json.loads(response.body)
            assert response_data == [{'status': 'success'}, 200]
            mock_update.assert_called_once_with('72c16f9f-5f13-439b-bf09-7440edd16086', request_body)


def test_create_user():
    request_body = {
        "client_id": 2,
        "document_type": "Cedula",
        "user_role": "Admin",
        "id_number": "123456",
        "name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "cellphone": "1234567890",
        "password": "temporaryPassword123",
        "communication_type": "Email"
    }

    mock_cognito_response = {
        'User': {
            'Attributes': [
                {'Name': 'sub', 'Value': 'user-sub-12345'}
            ]
        }
    }
    mock_cognito_client = MagicMock()
    mock_cognito_client.admin_create_user.return_value = mock_cognito_response
    mock_cognito_client.admin_set_user_password.return_value = {}
    mock_cognito_client.admin_create_user.side_effect = None

    with patch('app.get_cognito_client', return_value=mock_cognito_client):
        with Client(app) as client:
            response = client.http.post(
                '/user',
                headers={'Content-Type': 'application/json'},
                body=json.dumps(request_body)
            )
            from pprint import pprint

            pprint(response.body)
            assert response.status_code == 200
            response_data = json.loads(response.body)
            assert response_data == [{'status': "ok", 'message': "User created successfully", 'cognito_user_sub': 'user-sub-12345'}, 200]


def test_create_user_email_exists():
    request_body = {
        "client_id": 2,
        "document_type": "Cedula",
        "user_role": "Admin",
        "id_number": "123456",
        "name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "cellphone": "1234567890",
        "password": "temporaryPassword123",
        "communication_type": "Email"
    }

    mock_cognito_response = {
        'User': {
            'Attributes': [
                {'Name': 'sub', 'Value': 'user-sub-12345'}
            ]
        }
    }
    error_response = {
        'Error': {
            'Code': 'UsernameExistsException',
            'Message': 'The email is already registered.'
        }
    }
    mock_cognito_client = MagicMock()
    mock_cognito_client.exceptions.UsernameExistsException = Exception
    mock_cognito_client.admin_create_user.return_value = mock_cognito_response
    mock_cognito_client.admin_set_user_password.return_value = {}
    mock_cognito_client.admin_create_user.side_effect = ClientError(error_response, 'admin_create_user')

    with patch('app.get_cognito_client', return_value=mock_cognito_client):
        with Client(app) as client:
            response = client.http.post(
                '/user',
                headers={'Content-Type': 'application/json'},
                body=json.dumps(request_body)
            )

            assert response.status_code == 400
            response_data = json.loads(response.body)
            assert response_data['Message'] == 'The email is already registered.'

            mock_cognito_client.admin_create_user.assert_called_once()

            mock_cognito_client.admin_set_user_password.assert_not_called()


def test_get_user_not_found():
    with patch('chalicelib.src.modules.infrastructure.repository.UserRepositoryPostgres.get', return_value=None):
        with Client(app) as client:
            response = client.http.get('/user/non-existent-user-sub')

            response_data = json.loads(response.body)
            assert response_data['message'] == 'User not found'


def test_delete_user_not_found():
    with patch('chalicelib.src.modules.infrastructure.repository.UserRepositoryPostgres.remove', side_effect=ValueError("User not found")):
        with Client(app) as client:
            response = client.http.delete('/user/non-existent-user-sub')

            from pprint import pprint
            response_data = json.loads(response.body)

            pprint(response_data)

            assert response_data[0]['message'] == 'An error occurred while deleting the user'


def test_create_user_missing_field():
    request_body = {
        "client_id": 2,
        "user_role": "Admin",
        "id_number": "123456",
        "name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "cellphone": "1234567890",
        "communication_type": "Email"
    }

    with Client(app) as client:
        response = client.http.post(
            '/user',
            headers={'Content-Type': 'application/json'},
            body=json.dumps(request_body)
        )

        assert response.status_code == 400
        response_data = json.loads(response.body)
        assert "Missing required field: document_type" in response_data['Message']