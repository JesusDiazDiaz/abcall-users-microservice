import logging
from dataclasses import dataclass

from botocore.client import BaseClient

from chalicelib.src.modules.application.commands.base import CommandBaseHandler
from chalicelib.src.modules.infrastructure.cognito_repository import UserCognitoRepository
from chalicelib.src.seedwork.application.commands import execute_command
from chalicelib.src.seedwork.application.commands import Command

LOGGER = logging.getLogger('abcall-users-microservice')


@dataclass
class DeleteCognitoUserCommand(Command):
    cognito_client: BaseClient
    user_sub: str
    user_pool_id: str


class UpdateInformationHandler(CommandBaseHandler):
    def handle(self, command: DeleteCognitoUserCommand):
        LOGGER.info("Handle createCognitoUserCommand")
        repository = self.user_factory.create_object(UserCognitoRepository,
                                                     cognito_client=command.cognito_client,
                                                     user_pool_id=command.user_pool_id)
        return repository.remove(command.user_sub)


@execute_command.register(DeleteCognitoUserCommand)
def execute_update_information_command(command: DeleteCognitoUserCommand):
    handler = UpdateInformationHandler()
    return handler.handle(command)
