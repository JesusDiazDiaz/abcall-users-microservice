import logging
from dataclasses import dataclass
from chalicelib.src.modules.application.commands.base import CommandBaseHandler
from chalicelib.src.seedwork.application.commands import execute_command
from chalicelib.src.seedwork.application.commands import Command
from chalicelib.src.modules.domain.repository import UserRepository

LOGGER = logging.getLogger('abcall-users-microservice')


@dataclass
class DeleteUserCommand(Command):
    cognito_user_sub: str


class UpdateInformationHandler(CommandBaseHandler):
    def handle(self, command: DeleteUserCommand):
        LOGGER.info("Handle createUserCommand")

        repository = self.user_factory.create_object(UserRepository.__class__)
        repository.remove(command.cognito_user_sub)


@execute_command.register(DeleteUserCommand)
def execute_update_information_command(command: DeleteUserCommand):
    handler = UpdateInformationHandler()
    handler.handle(command)
