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

    mock_cognito_user = {
        "Username": "test_user",
        "UserAttributes": [
            {"Name": "email", "Value": "test_user@example.com"}
        ]
    }

    with patch('chalicelib.src.modules.infrastructure.repository.UserRepositoryPostgres.get', return_value=mock_user):
        with patch('chalicelib.src.modules.infrastructure.cognito_repository.UserCognitoRepository.get',
                   return_value=mock_cognito_user):
            with Client(app) as client:
                response = client.http.get('/user/72c16f9f-5f13-439b-bf09-7440edd16086')

                assert response.status_code == 200
                response_data = json.loads(response.body)
                assert response_data == mock_user


def test_delete_user():
    with Client(app) as client:
        with patch('chalicelib.src.modules.infrastructure.repository.UserRepositoryPostgres.remove') as mock_remove:
            with patch('chalicelib.src.modules.infrastructure.cognito_repository.UserCognitoRepository.remove'):
                response = client.http.delete('/user/72c16f9f-5f13-439b-bf09-7440edd16086')

                assert response.status_code == 200
                response_data = json.loads(response.body)
                assert response_data == {'message': f"Usuario 72c16f9f-5f13-439b-bf09-7440edd16086 eliminado exitosamente"}

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
            with patch('chalicelib.src.modules.infrastructure.cognito_repository.UserCognitoRepository.update'):
                response = client.http.put(
                    '/user/72c16f9f-5f13-439b-bf09-7440edd16086',
                    headers={'Content-Type': 'application/json'},
                    body=json.dumps(request_body)
                )

                assert response.status_code == 200

                response_data = json.loads(response.body)
                assert response_data == {'status': 'success'}
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

    mock_cognito_user = {
        "User": {
            "Username": "test_user",
            "Attributes": [
                {"Name": "sub", "Value": "72c16f9f-5f13-439b-bf09-7440edd16086"},
                {"Name": "email", "Value": "test_user@example.com"},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "custom:custom:userRole", "Value": "Admin"},
                {"Name": "custom:client_id", "Value": "2"}
            ],
            "UserCreateDate": "2024-11-23T12:34:56.000Z",
            "Enabled": True,
            "UserStatus": "FORCE_CHANGE_PASSWORD"
        }
    }

    with patch('app.get_cognito_client', return_value=mock_cognito_client):
        with patch('chalicelib.src.modules.infrastructure.cognito_repository.UserCognitoRepository.add', return_value=mock_cognito_user):
            with Client(app) as client:
                response = client.http.post(
                    '/user',
                    headers={'Content-Type': 'application/json'},
                    body=json.dumps(request_body)
                )

                assert response.status_code == 200
                response_data = json.loads(response.body)
                assert response_data == {'status': "ok", 'message': "User created successfully", 'cognito_user_sub': '72c16f9f-5f13-439b-bf09-7440edd16086'}


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


def test_get_current_user():
    mock_context = {
        'authorizer': {
            'claims': {
                'sub': 'user123',
                'email': 'user@example.com',
                'custom:custom:userRole': 'admin'
            }
        }
    }

    mock_request = MagicMock()
    mock_request.context = mock_context
    mock_request.headers = {
        'Content-Type': 'application/json'
    }

    mock_user = {
        "id": 1,
        "name": "John",
        "last_name": "Doe",
        "document_type": "Cedula",
        "id_number": "123456",
        "client_id": 2
    }

    with patch('chalice.app.Request', return_value=mock_request):
        with patch('chalicelib.src.modules.infrastructure.repository.UserRepositoryPostgres.get', return_value=mock_user):
            with Client(app) as client:
                response = client.http.get('/user/me')

                assert response.status_code == 200
                response_data = json.loads(response.body)
                assert response_data['email'] == 'user@example.com'
                assert response_data['user_role'] == 'admin'
                assert response_data['id'] == mock_user['id']


def test_update_me_success():
    # Mock context for the request
    mock_context = {
        'authorizer': {
            'claims': {
                'sub': 'user123',
                'email': 'user@example.com',
                'custom:custom:userRole': 'admin'
            }
        }
    }

    # Mock request data
    mock_request = MagicMock()
    mock_request.context = mock_context
    mock_request.json_body = {
        "document_type": "Cedula",
        "communication_type": "Email",
        "name": "John"
    }
    mock_request.headers = {
        'Content-Type': 'application/json'
    }

    with patch('chalice.app.Request', return_value=mock_request):
        with patch('chalicelib.src.modules.infrastructure.repository.UserRepositoryPostgres.update'):
            with Client(app) as client:
                response = client.http.put('/user/me', headers={'Content-Type': 'application/json'}, body=json.dumps(mock_request.json_body))

                # Validate response
                assert response.status_code == 200
                response_data = json.loads(response.body)
                assert response_data['status'] == 'success'


def test_update_me_invalid_document_type():
    # Mock context for the request
    mock_context = {
        'authorizer': {
            'claims': {
                'sub': 'user123'
            }
        }
    }

    # Mock invalid request data
    mock_request = MagicMock()
    mock_request.context = mock_context
    mock_request.json_body = {
        "document_type": "InvalidType"
    }
    mock_request.headers = {
        'Content-Type': 'application/json'
    }

    with patch('chalice.app.Request', return_value=mock_request):
        with Client(app) as client:
            response = client.http.put('/user/me', headers={'Content-Type': 'application/json'}, body=json.dumps(mock_request.json_body))

            # Validate response for bad request
            assert response.status_code == 400
            # response_data = json.loads(response.body)
            # assert "Invalid 'document_type'" in response_data['message']


def test_register_success():
    # Mock input data for the endpoint
    request_body = {
        "client_id": "client001",
        "document_type": "Cedula",
        "id_number": "123456789",
        "name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "cellphone": "1234567890",
        "password": "securepassword123",
        "communication_type": "Email"
    }

    mock_context = {
        'authorizer': {
            'claims': {
                'sub': 'user123',
                'email': 'user@example.com'
            }
        }
    }

    mock_request = MagicMock()
    mock_request.json_body = request_body
    mock_request.context = mock_context
    mock_request.headers = {
        'Content-Type': 'application/json'
    }

    # Mock response from the Cognito repository
    mock_cognito_response = {
        "User": {
            "Attributes": [
                {"Name": "sub", "Value": "cognito-user-123"}
            ]
        }
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

    mock_user_created = {
        "client_id": "client001",
        "document_type": "Cedula",
        "id_number": "123456789",
        "name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "cellphone": "1234567890",
        "password": "securepassword123",
        "communication_type": "Email"
    }

    with patch('app.get_cognito_client', return_value=mock_cognito_client):
        with patch('chalicelib.src.modules.infrastructure.repository.UserRepositoryPostgres.add',
                   return_value=mock_user_created):
            with patch('chalicelib.src.modules.infrastructure.cognito_repository.UserCognitoRepository.add', return_value=mock_cognito_response):
                # Mock command execution for creating the DB user
                with Client(app) as client:
                    # Call the register endpoint
                    response = client.http.post('/user/register', headers={'Content-Type': 'application/json'}, body=json.dumps(request_body))

                    # Validate response
                    assert response.status_code == 200
                    response_data = json.loads(response.body)
                    assert response_data['status'] == "ok"
                    assert response_data['message'] == "User created successfully"
                    assert response_data['cognito_user_sub'] == "user-sub-12345"
