import ujson as json
from app.core import errors
from app.core.serialize import SyncProtocolException, MasterSlaveType
from app.resource.base import BaseResource
from app.model.device_cmd import DeviceCmdModel


class IoTCmdResource(BaseResource):

    def __init__(self):
        pass

    def on_post(self, req, resp):
        cmd = req.params.get('cmd', '')
        if isinstance(cmd, list):
            cmd = cmd[0]

        device = req.get_param_as_int('device', required=True)
        sync = req.get_param_as_bool('sync', required=False)

        try:
            result = getattr(IoTCmd, cmd.lower())(req, device, sync)
        except AttributeError:
            raise errors.HTTPInvalidParam(param_name='cmd')
        except SyncProtocolException as e:
            raise errors.HTTPIoTError(error=str(e))

        resp.body = json.dumps(result)


class IoTCmd:

    @staticmethod
    def upgrade(req, device, sync):
        input = {}
        req.get_param_as_int(name='type', required=True, min=0, max=3, store=input)
        req.get_param(name='res', required=True, store=input)
        req.get_param(name='md5', required=True, store=input)
        req.get_param(name='ip', required=True, store=input)
        req.get_param_as_int(name='port', required=True, min=1, max=65535, store=input)
        return DeviceCmdModel.upgrade(device, sync, **input)

    @staticmethod
    def script_query(req, device, sync):
        return DeviceCmdModel.script_query(device, sync)

    @staticmethod
    def attr_query(req, device, sync):
        return DeviceCmdModel.attr_query(device, sync)

    @staticmethod
    def attr_set(req, device, sync):
        input = {}
        req.get_param(name='master_slave', required=True, store=input)
        req.get_param_as_int(name='physical_chan', required=True, min=1, max=254, store=input)
        req.get_param_as_int(name='logical_chan', required=True, min=0, max=255, store=input)
        try:
            input['master_slave'] = getattr(MasterSlaveType, input['master_slave'].upper())
        except AttributeError:
            raise errors.HTTPInvalidInput(error='非法的 master/slave 参数: ' + input['master_slave'])
        return DeviceCmdModel.attr_set(device, sync, **input)

    @staticmethod
    def state_query(req, device, sync):
        return DeviceCmdModel.state_query(device, sync)

    @staticmethod
    def reboot(req, device, sync):
        input = {}
        req.get_param_as_int(name='op', required=False, min=0, store=input)
        return DeviceCmdModel.reboot(device, sync, **input)
