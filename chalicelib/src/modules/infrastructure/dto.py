import enum
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Enum, Date, Text
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class DocumentType(enum.Enum):
    CEDULA = "Cedula"
    PASSPORT = "Passport"
    CEDULA_EXTRANJERIA = "Cedula_Extranjeria"


class UserRole(enum.Enum):
    SUPERADMIN = "Superadmin"
    ADMIN = "Admin"
    AGENT = "Agent"
    REGULAR = "Regular"


# TODO: Change this to spanish
class CommunicationType(enum.Enum):
    EMAIL = "Email"
    TELEFONO = "Telefono"
    SMS = "Sms"
    CHAT = "Chat"


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    cognito_user_sub = Column(String, nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    user_role = Column(Enum(UserRole), nullable=False)
    client_id = Column(Integer, nullable=False)
    id_number = Column(String, nullable=False)
    name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    communication_type = Column(Enum(CommunicationType), nullable=False)


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
