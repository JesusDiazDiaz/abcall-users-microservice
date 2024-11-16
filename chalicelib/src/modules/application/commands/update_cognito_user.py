import logging
from dataclasses import dataclass

from botocore.client import BaseClient

from chalicelib.src.modules.application.commands.base import CommandBaseHandler
from chalicelib.src.modules.infrastructure.cognito_repository import UserCognitoRepository
from chalicelib.src.seedwork.application.commands import execute_command
from chalicelib.src.seedwork.application.commands import Command

LOGGER = logging.getLogger('abcall-users-microservice')


@dataclass
class UpdateCognitoUserCommand(Command):
    cognito_client: BaseClient
    attributes: dict
    user_pool_id: str
    user_sub: str


class UpdateInformationHandler(CommandBaseHandler):
    def handle(self, command: UpdateCognitoUserCommand):
        LOGGER.info("Handle createCognitoUserCommand")
        repository = self.user_factory.create_object(UserCognitoRepository,
                                                     cognito_client=command.cognito_client,
                                                     user_pool_id=command.user_pool_id)
        return repository.update(user_sub=command.user_sub, attributes=command.attributes)


@execute_command.register(UpdateCognitoUserCommand)
def execute_update_information_command(command: UpdateCognitoUserCommand):
    handler = UpdateInformationHandler()
    return handler.handle(command)
