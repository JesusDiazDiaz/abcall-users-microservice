
class DomainException(Exception):
    ...


class ImmutableIdException(DomainException):
    def __init__(self, message='The identifier must be immutable'):
        self.__message = message

    def __str__(self):
        return str(self.__message)


class FactoryException(DomainException):
    def __init__(self, message):
        self.__message = message

    def __str__(self):
        return str(self.__message)
