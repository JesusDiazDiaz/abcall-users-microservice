from dataclasses import dataclass
from chalicelib.src.seedwork.application.queries import Query, QueryResult, execute_query
from chalicelib.src.modules.application.queries.base import QueryBaseHandler
from chalicelib.src.modules.domain.repository import UserRepository
from typing import Optional


@dataclass
class GetUsersQuery(Query):
    client_id: Optional[str] = None
    filters: Optional[dict] = None


class GetUsersHandler(QueryBaseHandler):
    def handle(self, query: GetUsersQuery):
        repository = self.user_factory.create_object(UserRepository)
        if query.filters is not None:
            result = repository.get_all(query.filters)
        else:
            result = repository.get_all({'client_id': query.client_id})
        return QueryResult(result=result)


@execute_query.register(GetUsersQuery)
def execute_get_users(query: GetUsersQuery):
    handler = GetUsersHandler()
    return handler.handle(query)