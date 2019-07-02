import falcon
from app.core.request import BaseRequest
from app.error_handler import error_handler
from app.resource import *


app = falcon.API(request_type=BaseRequest, middleware=[])
app.req_options.auto_parse_form_urlencoded = True
app.add_error_handler(Exception, error_handler)

device = DeviceResource()
device_config = DeviceConfigResource()
device_firmware = DeviceFirmwareResource()
device_unbind = DeviceUnbindResource()
iot_cmd = IoTCmdResource()
iot_notify = IoTNotifyResource()

app.add_route('/iot/device', device)
app.add_route('/iot/device/config', device_config)
app.add_route('/iot/device/firmware', device_firmware)
app.add_route('/iot/device/unbind', device_unbind)
app.add_route('/iot/cmd', iot_cmd)
app.add_route('/iot/notify', iot_notify)
