from app.core.errors import HTTPIoTError
from app.model.device_event import DeviceEventModel


def error_handler(ex, req, resp, params):
    if isinstance(ex, HTTPIoTError):
        if ex.device and ex.iot_error == 'OFFLINE':
            DeviceEventModel.offline(device=ex.device)
    raise ex
