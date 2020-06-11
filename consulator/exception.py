from consul import ConsulException

class ConsulatorException(Exception):
    def __init__(self, value):
        self.value = value

    def __setr__(self):
        return repr(self.value)

class ConsulError(ConsulatorException):
    pass

class ConsulConnectionError(ConsulatorException):
    pass

class ConsulInternalError(ConsulException):
    pass

class InvalidSessionTTL(ConsulException):
    pass

class InvalidSession(ConsulException):
    pass
