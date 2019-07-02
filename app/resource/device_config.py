import ujson as json
from app.resource.base import BaseResource
from app.model.device_config import DeviceConfigModel
from config import Config


class DeviceConfigResource(BaseResource):
    def __init__(self):
        pass

    def on_get(self, req, resp):
        device_name = req.get_param_as_int(name='device', required=False, default=0)
        device_config_model = DeviceConfigModel(device_name)
        if device_name:
            result = device_config_model.get_device_config()
        else:
            result = device_config_model.get_device_configs()
        resp.body = json.dumps(result)

    def on_post(self, req, resp):
        hardware_sn = req.get_param(name='sn', required=True)
        device_config_model = DeviceConfigModel()
        client_id, username, passwd = device_config_model.create_device_config(hardware_sn)
        resp.body = json.dumps({
            'client_id': client_id,
            'username': username,
            'passwd': passwd,
            'mqtt_broker': Config['iot']['mqtt_broker'],
        })
