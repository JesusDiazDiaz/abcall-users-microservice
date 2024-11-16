import logging
from dataclasses import dataclass

from botocore.client import BaseClient

from chalicelib.src.modules.application.commands.base import CommandBaseHandler
from chalicelib.src.modules.infrastructure.cognito_repository import UserCognitoRepository
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
        repository = self.user_factory.create_object(UserCognitoRepository,
                                                     cognito_client=command.cognito_client,
                                                     user_pool_id=command.user_pool_id)
        return repository.add(command.user_as_json)


@execute_command.register(CreateCognitoUserCommand)
def execute_update_information_command(command: CreateCognitoUserCommand):
    handler = UpdateInformationHandler()
    return handler.handle(command)
