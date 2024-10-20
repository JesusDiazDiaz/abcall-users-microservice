from operator import and_
from uuid import UUID
import logging
from chalicelib.src.modules.domain.repository import UserRepository
from chalicelib.src.modules.infrastructure.dto import User, DocumentType, UserRole, CommunicationType, UserSchema
from chalicelib.src.config.db import db_session, init_db
from chalicelib.src.seedwork.infrastructure.utils import handle_db_session


LOGGER = logging.getLogger('abcall-pqrs-microservice')


class UserRepositoryPostgres(UserRepository):
    def __init__(self):
        self.db_session = init_db()

    def add(self, user):
        LOGGER.info(f"Repository add user: {user}")
        user_schema = UserSchema()
        new_user = User(
            cognito_user_sub=user.cognito_user_sub,
            document_type=DocumentType(user.document_type),
            user_role=UserRole(user.user_role),
            client_id=user.client_id,
            id_number=user.id_number,
            name=user.name,
            last_name=user.last_name,
            communication_type=CommunicationType(user.communication_type)
        )
        self.db_session.add(new_user)
        self.db_session.commit()
        return user_schema.dump(new_user)

    def get(self, user_sub):
        user_schema = UserSchema()
        user = self.db_session.query(User).filter_by(cognito_user_sub=user_sub).first()
        if not user:
            raise ValueError("user not found")
        return user_schema.dump(user)

    def remove(self, user_sub):
        LOGGER.info(f"Repository remove user: {user_sub}")
        entity = self.db_session.query(User).filter_by(user_sub=user_sub).first()
        self.db_session.delete(entity)
        self.db_session.commit()
        LOGGER.info(f"User {user_sub} removed successfully")

    def get_all(self, query:dict[str, str]):
        user_schema = UserSchema(many=True)
        if not query:
            return self.db_session.query(User).all()

        filters = []
        if 'client_id' in query:
            filters.append(User.client_id == query['client_id'])
        if 'name' in query:
            filters.append(User.name.ilike(f"%{query['name']}%"))  # Para una búsqueda parcial (case-insensitive)
        if 'last_name' in query:
            filters.append(User.last_name.ilike(f"%{query['last_name']}%"))
        if 'document_type' in query:
            filters.append(User.document_type == query['document_type'])
        if 'id_number' in query:
            filters.append(User.id_number == query['id_number'])

        result = self.db_session.query(User).filter(and_(*filters)).all() if len(filters) > 1\
            else self.db_session.query(User).filter(filters[0]).all()
        return user_schema.dump(result)


    def update(self, user_sub, data) -> None:
        LOGGER.info(f"Repository update user sub: {user_sub} with data: {data}")

        user = self.db_session.query(User).filter_by(cognito_user_sub=user_sub).first()
        if not user:
            raise ValueError("User not found")

        if 'name' in data:
            user.name = data['name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            user.email = data['email']
        if 'cellphone' in data:
            user.cellphone = data['cellphone']
        if 'client_id' in data:
            user.client_id = data['client_id']
        if 'document_type' in data:
            user.document_type = DocumentType(data['document_type'])
        if 'user_rol' in data:
            user.user_role = UserRole(data['user_rol'])
        if 'communication_type' in data:
            user.communication_type = CommunicationType(data['communication_type'])

        self.db_session.commit()
        LOGGER.info(f"User {user_sub} updated successfully")
