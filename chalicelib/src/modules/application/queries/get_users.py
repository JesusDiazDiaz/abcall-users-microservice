from dataclasses import dataclass
from chalicelib.src.seedwork.application.queries import Query, QueryResult, execute_query
from chalicelib.src.modules.application.queries.base import QueryBaseHandler
from chalicelib.src.modules.domain.repository import UserRepository


@dataclass
class GetUsersQuery(Query):
    client_id:str

class GetUsersHandler(QueryBaseHandler):
    def handle(self, query: GetUsersQuery):
        repository = self.user_factory.create_object(UserRepository.__class__)
        result = repository.get_all({'client_id': query.client_id})
        return QueryResult(result=result)


@execute_query.register(GetUsersQuery)
def execute_get_users(query: GetUsersQuery):
    handler = GetUsersHandler()
    return handler.handle(query)