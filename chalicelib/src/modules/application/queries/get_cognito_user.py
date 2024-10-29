from dataclasses import dataclass

from botocore.client import BaseClient

from chalicelib.src.modules.application.queries.base import QueryBaseHandler
from chalicelib.src.modules.infrastructure.cognito_repository import UserCognitoRepository
from chalicelib.src.seedwork.application.queries import Query, QueryResult, execute_query


@dataclass
class GetCognitoUserQuery(Query):
    user_sub: str
    cognito_client: BaseClient
    user_pool_id: str


class GetUserCognitoHandler(QueryBaseHandler):
    def handle(self, query: GetCognitoUserQuery):
        repository = self.user_factory.create_object(UserCognitoRepository,
                                                     cognito_client=query.cognito_client,
                                                     user_pool_id=query.user_pool_id)
        result = repository.get(query.user_sub)
        return QueryResult(result=result)


@execute_query.register(GetCognitoUserQuery)
def execute_get_user(query: GetCognitoUserQuery):
    handler = GetUserCognitoHandler()
    return handler.handle(query)
