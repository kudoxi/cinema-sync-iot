import ujson as json
from app.model.device_cmd import DeviceCmdModel
from app.model.device import DeviceModel
from app.resource.base import BaseResource
from app.core import errors
from app.core.serialize import UpgradeType
from config import Config


class DeviceFirmwareResource(BaseResource):
    def __init__(self):
        pass
    
    def on_get(self, req, resp):
        print('-------------in firmware on get -----------')
        resp.body = json.dumps({"message": "success", "code": 0})



    def on_put(self, req, resp):
        print(' --------- in firmware on put ------------------')
        input = {}
        req.get_param_as_int(name='device', required=True, store=input)
        req.get_param(name='type', required=True, store=input)
        req.get_param(name='version', required=True, store=input)
        req.get_param(name='hash', required=True, store=input)
        req.get_param(name='script', required=False, store=input)

        input_file_type = input['type'].upper()
        valid_file_types = [e.name for e in UpgradeType]
        if input_file_type not in valid_file_types:
            raise errors.HTTPInvalidInput(error='文件类型不合法')
        print('========= input_file_type:',input_file_type,'====== UpgradeType.SCRIPT.name:',
                UpgradeType.SCRIPT.name,'======= input.get(script):',input.get('script'))
        if input_file_type == UpgradeType.SCRIPT.name and not input.get('script'):
            raise errors.HTTPMissingParam(param_name='script')

        device_name = input['device']
        print("------ip:",Config['upgrade_server']['ip'],"--------port:",Config['upgrade_server']['port'])
        # Todo script 主从同时下载
        upgrade_type = getattr(UpgradeType, input_file_type)
        result = DeviceCmdModel.upgrade(
            device=device_name,
            sync=True,
            type=upgrade_type,
            res=input['version'],
            md5=input['hash'],
            ip=Config['upgrade_server']['ip'],
            port=Config['upgrade_server']['port'],
        )
        print("-------- res:",result)
        # Result 1 为拒绝执行
        if result.get('Result'):
            resp.body = json.dumps({"message": "success", "code": 0})
            return

        # 将要下载的脚本名称/同步固件版本号/识别固件版本号/特征值文件版本号
        # 'new_script', 'new_sync', 'new_ident', 'new_ident_file',
        # 脚本/同步固件/识别固件/特征值文件 下载失败 -1 下载成功 0 下载中 1
        # 'download_script', 'download_sync', 'download_ident', 'download_ident_file',
        update_fields = None
        upgrade_type_name = upgrade_type.name

        if upgrade_type_name == 'SCRIPT':
            update_fields = [('download_script', 1), ('new_script', input['script'])]
        elif upgrade_type_name == 'SYNC_FIRMWARE':
            update_fields = [('download_sync', 1), ('new_sync', input['version'])]
        elif upgrade_type_name == 'IDENT_FIRMWARE':
            update_fields = [('download_ident', 1), ('new_ident', input['version'])]
        elif upgrade_type_name == 'IDENT_FILE':
            update_fields = [('download_ident_file', 1), ('new_ident_file', input['version'])]

        if update_fields:
            device_model = DeviceModel(device_name=device_name)
            device_model.update_device(update_fields, expect='EXIST')
        resp.body = json.dumps({"message": "success", "code": 0})
