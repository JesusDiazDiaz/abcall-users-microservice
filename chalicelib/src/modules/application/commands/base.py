from chalicelib.src.modules.infrastructure.factory import UserFactory
from chalicelib.src.seedwork.application.commands import CommandHandler


class CommandBaseHandler(CommandHandler):
    def __init__(self):
        self._user_factory: UserFactory = UserFactory()

    @property
    def user_factory(self):
        return self._user_factory