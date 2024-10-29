import logging

from botocore.client import BaseClient

from chalicelib.src.modules.domain.repository import UserRepository

LOGGER = logging.getLogger('abcall-pqrs-microservice')


class UserCognitoRepository(UserRepository):

    def __init__(self, cognito_client: BaseClient, user_pool_id: str):
        super().__init__()
        self.cognito_client: BaseClient = cognito_client
        self.user_pool_id: str = user_pool_id

    def add(self, entity):
        response = self.cognito_client.admin_create_user(
            UserPoolId=self.user_pool_id,
            Username=entity["email"],
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': entity["email"]
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                },
                {
                    'Name': 'custom:custom:userRole',
                    'Value': entity["user_role"]
                },
                {
                    'Name': 'custom:client_id',
                    'Value': str(entity['client_id'])
                }
            ],
            TemporaryPassword=entity["password"],
            MessageAction='SUPPRESS'
        )

        self.cognito_client.admin_set_user_password(
            UserPoolId=self.user_pool_id,
            Username=entity["email"],
            Password=entity["password"],
            Permanent=True
        )

        return response

    def remove(self, user_sub):
        self.cognito_client.admin_delete_user(
            UserPoolId=self.user_pool_id,
            Username=user_sub
        )

    def get(self, user_sub):
        try:
            response = self.cognito_client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=user_sub
            )
            LOGGER.info(f"User {user_sub} retrieved successfully")
            return response
        except self.cognito_client.exceptions.UserNotFoundException:
            LOGGER.warning(f"User {user_sub} not found in pool {self.user_pool_id}")
            return None
        except Exception as e:
            LOGGER.error(f"Error retrieving user {user_sub}: {e}")
            raise RuntimeError("Error retrieving user") from e

    def update(self, user_sub, attributes):
        try:
            user_attributes = [{'Name': key, 'Value': value} for key, value in attributes.items()]
            self.cognito_client.admin_update_user_attributes(
                UserPoolId=self.user_pool_id,
                Username=user_sub,
                UserAttributes=user_attributes
            )
            LOGGER.info(f"User {user_sub} updated successfully with attributes {attributes}")
        except self.cognito_client.exceptions.UserNotFoundException:
            LOGGER.warning(f"User {user_sub} not found for update")
            raise ValueError("User not found for update")
        except Exception as e:
            LOGGER.error(f"Error updating user {user_sub}: {e}")
            raise RuntimeError("Error updating user") from e

    def get_all(self, client_id=None):
        users = []
        try:
            response = self.cognito_client.list_users(UserPoolId=self.user_pool_id)

            for user in response['Users']:
                user_attributes = {attr['Name']: attr['Value'] for attr in user['Attributes']}

                if client_id is None or user_attributes.get('custom:client_id') == str(client_id):
                    users.append({
                        'Username': user['Username'],
                        'Attributes': user_attributes,
                        'Enabled': user['Enabled'],
                        'UserStatus': user['UserStatus']
                    })

        except self.cognito_client.exceptions.ClientError as e:
            LOGGER.error(f"Failed to retrieve users: {e}")
            raise RuntimeError("An error occurred while retrieving users.")

        return users