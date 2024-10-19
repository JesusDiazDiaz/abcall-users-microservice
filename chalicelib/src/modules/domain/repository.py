from abc import ABC
from chalicelib.src.seedwork.domain.repository import Repository


class UserRepository(Repository, ABC):
    pass