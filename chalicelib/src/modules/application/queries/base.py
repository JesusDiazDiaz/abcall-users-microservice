from chalicelib.src.modules.infrastructure.factory import UserFactory
from chalicelib.src.seedwork.application.commands import CommandHandler
from chalicelib.src.seedwork.application.queries import QueryHandler


class QueryBaseHandler(QueryHandler):
    def __init__(self):
        self._user_factory: UserFactory = UserFactory()

    @property
    def user_factory(self):
        return self._user_factory