import falcon
from falcon.http_error import HTTPError


class BaseHTTPError(HTTPError):
    def __init__(self, status, error, code=None):
        super().__init__(status=status)
        self.status = status
        self.error = error
        self.code = code

    def to_dict(self, obj_type=dict):
        obj = obj_type()
        obj['error'] = self.error
        obj['code'] = self.code if self.code else -1
        return obj


class HTTPMissingParam(BaseHTTPError):
    def __init__(self, param_name=None):
        if param_name:
            msg = 'The {0} is required.'.format(param_name)
        else:
            msg = 'Parameter missing'
        super().__init__(status=falcon.HTTP_400, error=msg, code=1000)


class HTTPInvalidParam(BaseHTTPError):
    def __init__(self, msg='', param_name=''):
        msg = ' ' + msg if msg else ''
        error = 'The {0} parameter is invalid.{1}'.format(param_name, msg)
        super().__init__(status=falcon.HTTP_400, error=error, code=1001)


class HTTPInvalidInput(BaseHTTPError):
    def __init__(self, error=''):
        super().__init__(status=falcon.HTTP_400, error=error, code=1002)


class HTTPIoTError(BaseHTTPError):
    def __init__(self, error, code=2000, device=0, iot_error=''):
        super().__init__(
            status=falcon.HTTP_400, error=error, code=code
        )
        self.device = device
        self.iot_error = iot_error

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return str(self.error)


class MNSUnorderedMessageError(BaseHTTPError):
    def __init__(self):
        super().__init__(
            status=falcon.HTTP_200,
            error='ignore unordered message', code=2010
        )


class TableStoreServiceError(BaseHTTPError):
    def __init__(self, msg='Table Store error'):
        super().__init__(status=falcon.HTTP_400, error=msg, code=2020)


class HTTPUnauthorized(BaseHTTPError):
    def __init__(self, msg='Unauthorized'):
        super().__init__(status=falcon.HTTP_401, error=msg, code=3000)


class HTTPFORBIDDEN(BaseHTTPError):
    def __init__(self, msg='Forbidden'):
        super().__init__(status=falcon.HTTP_403, error=msg, code=3001)


class HTTPNotFound(BaseHTTPError):
    def __init__(self, msg='No data'):
        super().__init__(status=falcon.HTTP_404, error=msg, code=4000)


class RedisLockError(BaseHTTPError):
    def __init__(self, msg='Redis lock error'):
        super().__init__(status=falcon.HTTP_500, error=msg, code=5000)
