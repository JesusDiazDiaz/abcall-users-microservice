from dataclasses import dataclass
from chalicelib.src.seedwork.domain.factory import Factory
from chalicelib.src.seedwork.domain.repository import Repository
from chalicelib.src.modules.domain.repository import UserRepository
from .cognito_repository import UserCognitoRepository
from .exceptions import ImplementationNotExistsForFactoryException
from .repository import UserRepositoryPostgres


@dataclass
class UserFactory(Factory):
    def create_object(self, obj: type, mapper: any = None, **kwargs) -> Repository:
        if obj == UserRepository:
            return UserRepositoryPostgres()

        if obj == UserCognitoRepository:
            cognito_client = kwargs.get('cognito_client')
            user_pool_id = kwargs.get('user_pool_id')

            if not cognito_client or not user_pool_id:
                raise ValueError("cognito_client y user_pool_id son requeridos para crear UserCognitoRepository")

            return UserCognitoRepository(cognito_client=cognito_client, user_pool_id=user_pool_id)

        raise ImplementationNotExistsForFactoryException()