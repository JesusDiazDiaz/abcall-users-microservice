import logging
from dataclasses import dataclass

from botocore.client import BaseClient

from chalicelib.src.modules.application.commands.base import CommandBaseHandler
from chalicelib.src.seedwork.application.commands import execute_command
from chalicelib.src.seedwork.application.commands import Command

LOGGER = logging.getLogger('abcall-users-microservice')


@dataclass
class CreateCognitoUserCommand(Command):
    cognito_client: BaseClient
    user_as_json: dict
    user_pool_id: str


class UpdateInformationHandler(CommandBaseHandler):
    def handle(self, command: CreateCognitoUserCommand):
        LOGGER.info("Handle createCognitoUserCommand")
        response = command.cognito_client.admin_create_user(
            UserPoolId=command.user_pool_id,
            Username=command.user_as_json["email"],
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': command.user_as_json["email"]
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                },
                {
                    'Name': 'custom:custom:userRole',
                    'Value': command.user_as_json["user_role"]
                },
                {
                    'Name': 'custom:client_id',
                    'Value': str(command.user_as_json['client_id'])
                }
            ],
            TemporaryPassword=command.user_as_json["password"],
            MessageAction='SUPPRESS'
        )

        command.cognito_client.admin_set_user_password(
            UserPoolId=command.user_pool_id,
            Username=command.user_as_json["email"],
            Password=command.user_as_json["password"],
            Permanent=True
        )

        return response


@execute_command.register(CreateCognitoUserCommand)
def execute_update_information_command(command: CreateCognitoUserCommand):
    handler = UpdateInformationHandler()
    return handler.handle(command)
