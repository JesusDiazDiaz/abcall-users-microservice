import boto3
import logging
import re
from chalice import Chalice, BadRequestError, CognitoUserPoolAuthorizer, NotFoundError, ChaliceViewError

from chalicelib.src.config.db import init_db
from chalicelib.src.modules.application.commands.create_user import CreateUserCommand
from chalicelib.src.modules.application.commands.delete_user import DeleteUserCommand
from chalicelib.src.modules.application.commands.update_user import UpdateUserCommand
from chalicelib.src.modules.application.queries.get_user import GetUserQuery
from chalicelib.src.modules.application.queries.get_users import GetUsersQuery
from chalicelib.src.seedwork.application.commands import execute_command
from chalicelib.src.seedwork.application.queries import execute_query

app = Chalice(app_name='abcall-users-microservice')
app.debug = True

LOGGER = logging.getLogger('abcall-users-microservice')

authorizer = CognitoUserPoolAuthorizer(
    'AbcPool',
    provider_arns=['arn:aws:cognito-idp:us-east-1:044162189377:userpool/us-east-1_YDIpg1HiU']
)

_COGNITO_CLIENT = None


def get_cognito_client():
    global _COGNITO_CLIENT
    if _COGNITO_CLIENT is None:
        _COGNITO_CLIENT = boto3.client('cognito-idp', region_name='us-east-1')
    return _COGNITO_CLIENT

USER_POOL_ID = 'us-east-1_YDIpg1HiU'
CLIENT_ID = '65sbvtotc1hssqecgusj1p3f9g'


@app.route('/users/{client_id}', cors=True, methods=['GET'])
def index(client_id):
    if client_id is None:
        client_id = ""

    query_result = execute_query(GetUsersQuery(client_id=client_id))
    return query_result.result


@app.route('/user/{user_sub}', cors=True, methods=['GET'])
def user_get(user_sub):
    try:
        query_result = execute_query(GetUserQuery(user_sub=user_sub))
        if not query_result.result:
            return {'status': 'fail', 'message': 'User not found'}

        return query_result.result

    except Exception as e:
        LOGGER.error(f"Error fetching user: {str(e)}")
        return {'status': 'fail', 'message': 'An error occurred while fetching the user'}, 500


@app.route('/user/{user_sub}', cors=True, methods=['DELETE'], authorizer=authorizer)
def user_delete(user_sub):
    if not user_sub:
        return {'status': 'fail', 'message': 'Invalid user subscription'}, 400

    command = DeleteUserCommand(cognito_user_sub=user_sub)

    try:
        execute_command(command)
        return {'status': 'success'}, 200

    except Exception as e:
        LOGGER.error(f"Error fetching user: {str(e)}")
        return {'status': 'fail', 'message': 'An error occurred while deleting the user'}, 400


@app.route('/user/{user_sub}', cors=True, methods=['PUT'], authorizer=authorizer)
def user_update(user_sub):
    if not user_sub:
        return {'status': 'fail', 'message': 'Invalid user subscription'}, 400

    command = UpdateUserCommand(cognito_user_sub=user_sub, user_data=app.current_request.json_body)

    try:
        execute_command(command)
        return {'status': 'success'}, 200

    except Exception as e:
        LOGGER.error(f"Error fetching user: {str(e)}")
        return {'status': 'fail', 'message': 'An error occurred while fetching the user'}, 400


@app.route('/user', cors=True, methods=['POST'], authorizer=authorizer)
def user_post():
    LOGGER.info("Receive create user request")
    user_as_json = app.current_request.json_body
    cognito_client = get_cognito_client()

    required_fields = ["client_id", "document_type", "user_role", "id_number", "name", "last_name", "email",
                       "cellphone",
                       "password", "communication_type"]
    for field in required_fields:
        if field not in user_as_json:
            raise BadRequestError(f"Missing required field: {field}")

    valid_types = ["Cedula", "Passport", "Cedula_Extranjeria"]
    if user_as_json["document_type"] not in valid_types:
        raise BadRequestError(f"Invalid 'type' value. Must be one of {valid_types}")

    valid_types = ['Superadmin', 'Admin', 'Agent', 'Regular']
    if user_as_json["user_role"] not in valid_types:
        raise BadRequestError(f"Invalid 'type' value. Must be one of {valid_types}")

    valid_types = ['Email', 'Telefono', 'Sms', 'Chat']
    if user_as_json["communication_type"] not in valid_types:
        raise BadRequestError(f"Invalid 'communication type' value. Must be one of {valid_types}")

    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, user_as_json["email"]):
        raise BadRequestError("Invalid email format")

    try:
        # TODO: Creo que esto se puedo mover al comando si lo deseamos, para evitar codigo aqui
        response = cognito_client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=user_as_json["email"],
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': user_as_json["email"]
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                },
                {
                    'Name': 'custom:custom:userRole',
                    'Value': user_as_json["user_role"]
                }
            ],
            TemporaryPassword=user_as_json["password"],
            MessageAction='SUPPRESS'
        )

        cognito_client.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=user_as_json["email"],
            Password=user_as_json["password"],
            Permanent=True
        )
    except cognito_client.exceptions.UsernameExistsException:
        raise BadRequestError("The email is already registered.")
    except Exception as e:
        LOGGER.error(f"Error creating user in Cognito: {str(e)}")
        raise BadRequestError("Failed to create user in Cognito.")

    cognito_user_sub = next(attr['Value'] for attr in response['User']['Attributes'] if attr['Name'] == 'sub')

    command = CreateUserCommand(
        cognito_user_sub=cognito_user_sub,
        document_type=user_as_json["document_type"],
        client_id=user_as_json["client_id"],
        id_number=user_as_json["id_number"],
        name=user_as_json["name"],
        last_name=user_as_json["last_name"],
        communication_type=user_as_json["communication_type"],
        user_role=user_as_json["user_role"],
        cellphone=user_as_json["cellphone"] if "cellphone" in user_as_json else None

    )

    execute_command(command)

    return {'status': "ok", 'message': "User created successfully", 'cognito_user_sub': cognito_user_sub}, 200


@app.route('/user/me', cors=True, methods=['GET'], authorizer=authorizer)
def get_current_user():
    LOGGER.info("Find Me User")
    user_info = app.current_request.context['authorizer']['claims']
    user_sub = user_info['sub']

    LOGGER.info(f"User Info: {user_info}")

    try:
        cognito_data = {
            'username': user_info['email'],
            'email': user_info['email'],
            'user_role': user_info['custom:custom:userRole'],
        }

        query_result = execute_query(GetUserQuery(user_sub=user_sub))

        if not query_result.result:
            raise NotFoundError('User not found')

        query_result.result.pop('user_role', None)

        user_data = {
            **cognito_data,
            **query_result.result
        }

        return user_data

    except Exception as e:
        LOGGER.error(f"Error fetching current user: {str(e)}")
        raise ChaliceViewError('An error occurred while fetching the current user')


@app.route('/user/me', cors=True, methods=['PUT'], authorizer=authorizer)
def update_me():
    LOGGER.info("Update Me User")
    user_info = app.current_request.context['authorizer']['claims']
    user_sub = user_info['sub']
    LOGGER.info(f"User Info: {user_info}")

    user_as_json = app.current_request.json_body

    if 'document_type' in user_as_json:
        valid_types = ['Cedula', 'Cedula_Extranjeria', "Passport"]
        if user_as_json["document_type"] not in valid_types:
            raise BadRequestError(f"Invalid 'document_type' value. Must be one of {valid_types}")

    if 'communication_type' in user_as_json:
        valid_types = ['Email', 'Telefono', 'Sms', 'Chat']
        if user_as_json["communication_type"] not in valid_types:
            raise BadRequestError(f"Invalid 'communication_type' value. Must be one of {valid_types}")

    command = UpdateUserCommand(cognito_user_sub=user_sub, user_data=user_as_json)

    try:
        execute_command(command)
        return {'status': 'success'}

    except Exception as e:
        LOGGER.error(f"Error fetching user: {str(e)}")
        raise ChaliceViewError('An error occurred while fetching the user')


@app.route('/user/register', cors=True, methods=['POST'])
def register():
    LOGGER.info("Receive create user request")
    user_as_json = app.current_request.json_body
    cognito_client = get_cognito_client()

    required_fields = ["client_id", "document_type", "id_number", "name", "last_name", "email",
                       "cellphone",
                       "password", "communication_type"]
    for field in required_fields:
        if field not in user_as_json:
            raise BadRequestError(f"Missing required field: {field}")

    valid_types = ["Cedula", "Passport", "Cedula_Extranjeria"]
    if user_as_json["document_type"] not in valid_types:
        raise BadRequestError(f"Invalid 'type' value. Must be one of {valid_types}")

    valid_types = ['Email', 'Telefono', 'Sms', 'Chat']
    if user_as_json["communication_type"] not in valid_types:
        raise BadRequestError(f"Invalid 'communication type' value. Must be one of {valid_types}")

    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, user_as_json["email"]):
        raise BadRequestError("Invalid email format")

    try:
        # TODO: Creo que esto se puedo mover al comando si lo deseamos, para evitar codigo aqui
        response = cognito_client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=user_as_json["email"],
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': user_as_json["email"]
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                },
                {
                    'Name': 'custom:custom:userRole',
                    'Value': 'Regular'
                }
            ],
            TemporaryPassword=user_as_json["password"],
            MessageAction='SUPPRESS'
        )

        cognito_client.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=user_as_json["email"],
            Password=user_as_json["password"],
            Permanent=True
        )
    except cognito_client.exceptions.UsernameExistsException:
        raise BadRequestError("The email is already registered.")
    except Exception as e:
        LOGGER.error(f"Error creating user in Cognito: {str(e)}")
        raise BadRequestError("Failed to create user in Cognito.")

    cognito_user_sub = next(attr['Value'] for attr in response['User']['Attributes'] if attr['Name'] == 'sub')

    command = CreateUserCommand(
        cognito_user_sub=cognito_user_sub,
        document_type=user_as_json["document_type"],
        client_id=user_as_json["client_id"],
        id_number=user_as_json["id_number"],
        name=user_as_json["name"],
        last_name=user_as_json["last_name"],
        communication_type=user_as_json["communication_type"],
        user_role='Regular',
        cellphone=user_as_json["cellphone"] if "cellphone" in user_as_json else None
    )

    execute_command(command)

    return {'status': "ok", 'message': "User created successfully", 'cognito_user_sub': cognito_user_sub}, 200

@app.route('/migrate', methods=['POST'])
def migrate():
    try:
        init_db(migrate=True)
        return {"message": "Tablas creadas con éxito"}
    except Exception as e:
        return {"error": str(e)}
