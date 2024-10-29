import logging
from operator import and_

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from chalicelib.src.config.db import init_db
from chalicelib.src.modules.domain.repository import UserRepository
from chalicelib.src.modules.infrastructure.dto import User, DocumentType, UserRole, CommunicationType, UserSchema

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
            communication_type=CommunicationType(user.communication_type),
            cellphone=user.cellphone
        )
        try:
            self.db_session.add(new_user)
            self.db_session.commit()
            return user_schema.dump(new_user)
        except IntegrityError as e:
            self.db_session.rollback()
            LOGGER.error(f"Integrity error while adding user {user}: {e}")
            raise ValueError("Error: datos de usuario no válidos o duplicados") from e
        except SQLAlchemyError as e:
            self.db_session.rollback()
            LOGGER.error(f"Database error while adding user {user}: {e}")
            raise RuntimeError("Error en la base de datos, intente nuevamente más tarde") from e
        except Exception as e:
            self.db_session.rollback()
            LOGGER.error(f"Unexpected error while adding user {user}: {e}")
            raise RuntimeError("Ocurrió un error inesperado") from e

    def get(self, user_sub):
        user_schema = UserSchema()
        user = self.db_session.query(User).filter_by(cognito_user_sub=user_sub).first()
        if not user:
            raise ValueError("user not found")
        return user_schema.dump(user)

    def remove(self, user_sub):
        LOGGER.info(f"Repository remove user: {user_sub}")

        try:
            entity = self.db_session.query(User).filter_by(cognito_user_sub=user_sub).first()

            if entity is None:
                LOGGER.warning(f"User {user_sub} not found for deletion")
                raise ValueError(f"Usuario con sub {user_sub} no encontrado")

            self.db_session.delete(entity)
            self.db_session.commit()
            LOGGER.info(f"User {user_sub} removed successfully")

        except IntegrityError as e:
            self.db_session.rollback()
            LOGGER.error(f"Integrity error while removing user {user_sub}: {e}")
            raise ValueError("Error de integridad al intentar eliminar el usuario") from e

        except SQLAlchemyError as e:
            self.db_session.rollback()
            LOGGER.error(f"Database error while removing user {user_sub}: {e}")
            raise RuntimeError("Error en la base de datos, intente nuevamente más tarde") from e

        except Exception as e:
            self.db_session.rollback()
            LOGGER.error(f"Unexpected error while removing user {user_sub}: {e}")
            raise RuntimeError("Ocurrió un error inesperado al intentar eliminar el usuario") from e

    def get_all(self, query: dict[str, str]):
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

        result = self.db_session.query(User).filter(and_(*filters)).all() if len(filters) > 1 \
            else self.db_session.query(User).filter(filters[0]).all()
        return user_schema.dump(result)

    def update(self, user_sub, data) -> None:
        LOGGER.info(f"Repository update user sub: {user_sub} with data: {data}")

        try:
            user = self.db_session.query(User).filter_by(cognito_user_sub=user_sub).first()

            if not user:
                LOGGER.warning(f"User {user_sub} not found for update")
                raise ValueError("Usuario no encontrado")

            if 'name' in data:
                user.name = data['name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'cellphone' in data:
                user.cellphone = data['cellphone']
            if 'client_id' in data:
                user.client_id = data['client_id']
            if 'user_role' in data:
                user.user_role = UserRole(data['user_role'])
            if 'document_type' in data:
                user.document_type = DocumentType(data['document_type'])
            if 'communication_type' in data:
                user.communication_type = CommunicationType(data['communication_type'])

            self.db_session.commit()
            LOGGER.info(f"User {user_sub} updated successfully")

        except IntegrityError as e:
            self.db_session.rollback()
            LOGGER.error(f"Integrity error while updating user {user_sub}: {e}")
            raise ValueError("Error de integridad al intentar actualizar el usuario") from e

        except SQLAlchemyError as e:
            self.db_session.rollback()
            LOGGER.error(f"Database error while updating user {user_sub}: {e}")
            raise RuntimeError("Error en la base de datos, intente nuevamente más tarde") from e

        except Exception as e:
            self.db_session.rollback()
            LOGGER.error(f"Unexpected error while updating user {user_sub}: {e}")
            raise RuntimeError("Ocurrió un error inesperado al intentar actualizar el usuario") from e
