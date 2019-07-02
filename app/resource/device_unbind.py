import ujson as json
from app.model.device import DeviceModel
from app.resource.base import BaseResource


class DeviceUnbindResource(BaseResource):

    def on_put(self, req, resp):
        device = req.get_param_as_int('device', required=True)
        device_model = DeviceModel()
        device_model.unbind_device(device_name=device)
        resp.body = json.dumps({"message": "success", "code": 0})
