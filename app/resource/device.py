import ujson as json
from app.model.device import DeviceModel
from app.model.device_config import DeviceConfigModel
from app.model.device_cmd import DeviceCmdModel
from app.resource.base import BaseResource
from app.core import errors
from app.core.serialize import UpgradeType, MasterSlaveType
from config import Config


class DeviceResource(BaseResource):
    def __init__(self):
        self.device_model = DeviceModel()

    def on_get(self, req, resp):
        device = req.get_param_as_int('device', required=False, default=0)
        p = req.get_param_as_int('p', required=False, min=1, default=1)
        n = req.get_param_as_int('n', required=False, min=1, max=100, default=10)
        free_master = req.get_param_as_bool('free-master', required=False)
        free_device = req.get_param_as_bool('free-device', required=False)

        if device:
            result = self.device_model.get_device(device_name=device)
            resp.body = json.dumps(result)
        else:
            param = {'page': p, 'limit': n}
            device_filter = []
            if free_master:
                device_filter.extend([
                    MasterSlaveType.NOT_SET.name,
                    MasterSlaveType.MASTER.name,
                ])
            if free_device:
                device_filter.extend([
                    MasterSlaveType.NOT_SET.name,
                ])
            if device_filter:
                param['equal'] = {'master_slave': device_filter}
            result, total = self.device_model.get_devices(**param)
            resp.body = json.dumps({"data": result, "total": total})

    def on_put(self, req, resp):
        input = {}
        # 主从设备编号
        master_device = req.get_param_as_int('master_device', required=True)
        slave_device = req.get_param_as_int('slave_device', required=False)
        # 影院影厅信息
        req.get_param('cinema', required=False, store=input)
        req.get_param_as_int('cinema_id', required=False, store=input)
        req.get_param('hall', required=False, store=input)
        req.get_param_as_int('hall_id', required=False, store=input)
        # 主从、物理逻辑信道
        req.get_param_as_int(name='master_slave', required=True, min=-1, max=1, store=input)
        req.get_param_as_int(name='physical_channel', required=False, min=1, max=254, store=input)
        req.get_param_as_int(name='logical_channel', required=False, min=0, max=255, store=input)
        # 电影脚本信息
        req.get_param(name='script', required=False, store=input)
        req.get_param_as_int(name='script_id', required=False, store=input)
        req.get_param(name='script_hash', required=False, store=input)

        md_info = self.device_model.get_device(device_name=master_device)
        if not md_info:
            raise errors.HTTPNotFound(msg=f'{master_device}号设备不存在')

        master_input = input
        master_input['slave'] = 0
        if input['master_slave'] != -1:
            master_input['master'] = master_device
            if slave_device:
                master_input['master_slave'] = MasterSlaveType.MASTER_WITH_SLAVE.name
                master_input['slave'] = slave_device
            else:
                master_input['master_slave'] = MasterSlaveType.MASTER.name
        else:
            master_input['master_slave'] = MasterSlaveType.NOT_SET.name
            master_input['master'] = 0

        self.cinema_update(device=master_device, new_info=master_input, old_info=md_info)
        self.attrs_update(device=master_device, new_info=master_input, old_info=md_info)
        self.script_update(device=master_device, new_info=master_input, old_info=md_info)

        if slave_device:
            sd_info = self.device_model.get_device(device_name=slave_device)
            if not sd_info:
                raise errors.HTTPNotFound(msg=f'{slave_device}号设备不存在')
            slave_input = input
            slave_input['master'] = master_device
            slave_input['slave'] = slave_device
            slave_input['master_slave'] = MasterSlaveType.SLAVE.name

            self.cinema_update(device=slave_device, new_info=slave_input, old_info=sd_info)
            self.attrs_update(device=slave_device, new_info=slave_input, old_info=sd_info)
            self.script_update(device=slave_device, new_info=slave_input, old_info=sd_info)

        resp.body = json.dumps({"message": "success", "code": 0})

    def on_delete(self, req, resp):
        device = req.get_param_as_int('device', required=True)
        self.device_model.delete_device(device_name=device)
        device_config_model = DeviceConfigModel()
        device_config_model.delete_device_config(device_name=device)
        resp.body = json.dumps({"message": "success", "code": 0})

    def cinema_update(self, device, new_info, old_info):
        fields = ['cinema', 'cinema_id', 'hall', 'hall_id', ]
        attrs = []
        for f in fields:
            if f in new_info and (
                    f in old_info and new_info[f] != old_info[f]
                    or f not in old_info
            ):
                attrs.append((f, new_info[f]))
        if attrs:
            self.device_model.set_device(device_name=device)
            self.device_model.update_device(attributes=attrs, expect='EXIST')

        return

    def attrs_update(self, device, new_info, old_info):
        fields = ['physical_channel', 'logical_channel', 'master', 'slave', 'master_slave', ]
        need_upate = False

        for f in fields:
            if f in new_info and (
                    f in old_info and new_info[f] != old_info[f]
                    or f not in old_info
            ):
                need_upate = True
                break

        if need_upate:
            if 'physical_channel' not in new_info or 'logical_channel' not in new_info:
                raise errors.HTTPInvalidInput(error='主从关系、逻辑信道、物理信道需要同时配置')
            try:
                # 发送 MQTT 消息到设备
                result = DeviceCmdModel.attr_set(
                    device=device, sync=True,
                    master_slave=getattr(MasterSlaveType, new_info['master_slave']),
                    physical_chan=new_info['physical_channel'],
                    logical_chan=new_info['logical_channel'],
                )
            except errors.HTTPIoTError as e:
                raise errors.HTTPIoTError(error=f'{device}号设备设置信道/主从关系失败：{e.error}')

            # Result 1 为拒绝执行
            if result.get('Result'):
                return

            self.device_model.set_device(device_name=device)
            self.device_model.update_device(attributes=[
                ('master', new_info['master']),
                ('slave', new_info['slave']),
                ('master_slave', new_info['master_slave']),
                ('logical_channel', new_info['logical_channel']),
                ('physical_channel', new_info['physical_channel']),
            ], expect='EXIST')

        return

    def script_update(self, device, new_info, old_info):
        fields = ['script', 'script_id', 'script_hash', ]
        need_update = False
        for f in fields:
            if f in new_info and (
                    f in old_info and new_info[f] != old_info[f]
                    or f not in old_info
            ):
                need_update = True
                break

        if need_update:
            try:
                script = new_info['script']
                scprit_id = new_info['script_id']
                script_hash = new_info['script_hash']
            except KeyError:
                raise errors.HTTPInvalidInput(error='script, script_id & script_hash needed')

            try:
                # 发送 MQTT 消息到设备
                result = DeviceCmdModel.upgrade(
                    device=device,
                    sync=True,
                    type=UpgradeType.SCRIPT,
                    res=scprit_id,
                    md5=script_hash,
                    ip=Config['upgrade_server']['ip'],
                    port=Config['upgrade_server']['port'],
                )
            except errors.HTTPIoTError as e:
                raise errors.HTTPIoTError(error=f'{device}号设备更新脚本失败：{e.error}')

            # Result 1 为拒绝执行
            if result.get('Result'):
                return

            self.device_model.set_device(device_name=device)
            self.device_model.update_device([
                ('download_script', 1), ('new_script', script)
            ], expect='EXIST')

        return
