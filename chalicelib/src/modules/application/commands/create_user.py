import logging
from dataclasses import dataclass
from chalicelib.src.modules.application.commands.base import CommandBaseHandler
from chalicelib.src.seedwork.application.commands import execute_command
from chalicelib.src.seedwork.application.commands import Command
from chalicelib.src.modules.domain.repository import UserRepository

LOGGER = logging.getLogger('abcall-users-microservice')


@dataclass
class CreateUserCommand(Command):
    cognito_user_sub: str
    document_type: str
    user_role: str
    client_id: str
    id_number: str
    name: str
    last_name: str
    communication_type: str


class UpdateInformationHandler(CommandBaseHandler):
    def handle(self, command: CreateUserCommand):
        LOGGER.info("Handle createUserCommand")

        repository = self.user_factory.create_object(UserRepository.__class__)
        repository.add(command)


@execute_command.register(CreateUserCommand)
def execute_update_information_command(command:  CreateUserCommand):
    handler = UpdateInformationHandler()
    handler.handle(command)
