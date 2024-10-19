import logging
from dataclasses import dataclass
from chalicelib.src.modules.application.commands.base import CommandBaseHandler
from chalicelib.src.seedwork.application.commands import execute_command
from chalicelib.src.seedwork.application.commands import Command
from chalicelib.src.modules.domain.repository import UserRepository

LOGGER = logging.getLogger('abcall-users-microservice')


@dataclass
class UpdateUserCommand(Command):
    cognito_user_sub: str
    user_data: dict


class UpdateInformationHandler(CommandBaseHandler):
    def handle(self, command: UpdateUserCommand):
        LOGGER.info("Handle createUserCommand")

        repository = self.user_factory.create_object(UserRepository.__class__)
        repository.update(command.cognito_user_sub, command.user_data)


@execute_command.register(UpdateUserCommand)
def execute_update_information_command(command:  UpdateUserCommand):
    handler = UpdateInformationHandler()
    handler.handle(command)
