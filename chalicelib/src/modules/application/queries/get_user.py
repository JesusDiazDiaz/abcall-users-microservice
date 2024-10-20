from dataclasses import dataclass
from chalicelib.src.seedwork.application.queries import Query, QueryResult, execute_query
from chalicelib.src.modules.application.queries.base import QueryBaseHandler
from chalicelib.src.modules.domain.repository import UserRepository


@dataclass
class GetUserQuery(Query):
    user_sub: str


class GetUserHandler(QueryBaseHandler):
    def handle(self, query: GetUserQuery):
        repository = self.user_factory.create_object(UserRepository.__class__)
        result = repository.get(query.user_sub)
        return QueryResult(result=result)


@execute_query.register(GetUserQuery)
def execute_get_user(query: GetUserQuery):
    handler = GetUserHandler()
    return handler.handle(query)
