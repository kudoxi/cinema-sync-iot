from falcon.request import Request
from app.core import errors


class BaseRequest(Request):
    def __init__(self, env, options=None):
        super().__init__(env, options=options)

    def get_param_as_int(self, name,
                         required=False, min=None, max=None, default=None, store=None):
        params = self._params

        if name in params:
            val = params[name]
            if isinstance(val, list):
                val = val[-1]

            try:
                val = int(val)
            except ValueError:
                msg = 'The value must be an integer.'
                raise errors.HTTPInvalidParam(msg, name)

            if min is not None and val < min:
                msg = 'The value must be at least ' + str(min)
                raise errors.HTTPInvalidParam(msg, name)

            if max is not None and max < val:
                msg = 'The value may not exceed ' + str(max)
                raise errors.HTTPInvalidParam(msg, name)

            if store is not None:
                store[name] = val

            return val

        if not required:
            if store is not None and default is not None:
                store[name] = default
            return default

        raise errors.HTTPMissingParam(name)
