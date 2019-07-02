from app.model.base import BaseModel
from app.model.device import DeviceModel
from app.model.sync_files import SyncFileModel
from app.core.redis import red
from app.core.errors import RedisLockError
from redis.exceptions import LockError


class DeviceEventModel(BaseModel):

    @staticmethod
    def online(device, message):
        online_time = message['lastTime']
        device_model = DeviceModel(device)
        try:
            with red.lock(f'online-{device}', blocking_timeout=0.5):
                device_info = device_model.get_device()
                last_time = device_info.get('time_online', '')
                if online_time > last_time:
                    device_model.update_device(attributes=[
                        ('online', 1),
                        ('time_online', online_time),
                        ('download_script', 0),
                        ('download_sync', 0),
                        ('download_ident', 0),
                        ('download_ident_file', 0),
                    ])
                    return True
        except LockError as e:
            raise RedisLockError(msg=str(e))

        return False

    @staticmethod
    def offline(device, message=None):
        device_model = DeviceModel(device)
        if message:
            offline_time = message['lastTime']
            try:
                with red.lock(f'online-{device}', blocking_timeout=0.5):
                    device_info = device_model.get_device()
                    last_time = device_info.get('time_online', '')
                    if offline_time > last_time:
                        device_model.update_device(attributes=[
                            ('online', 0),
                            ('time_online', offline_time),
                        ])
                        return True
            except LockError as e:
                raise RedisLockError(msg=str(e))
        else:
            device_model.update_device(attributes=[('online', 0)])
        return False

    @staticmethod
    def update_attr(device, message):
        script_hash = message.get('ScriptMD5')
        ident_file_hash = message.get('IdentFileMD5')

        attrs = [
            ('working_status', message.get('DeviceState')),
            ('logical_channel', message.get('LogicalChannel')),
            ('physical_channel', message.get('PhysicalChannel')),
            ('master_slave', message.get('MasterSlave')),
            ('sync_delay', message.get('SyncDelaySecond')),
            ('script_hash', script_hash),
            ('sync_version', message.get('SyncVersion')),
            ('ident_version', message.get('IdentVersion')),
            ('ident_file_hash', ident_file_hash),
            ('sim', message.get('SIMCode')),
            ('hardware_version', message.get('HardwareVersion')),
            ('sync_boot_version', message.get('SyncBootVersion')),
            ('ident_boot_version', message.get('IdentBootVersion')),
        ]
        attrs = [v for v in attrs if v[1] is not None]

        if ident_file_hash:
            sync_file_model = SyncFileModel()
            ident_file_version = sync_file_model.get_version_by_hash(
                hash=ident_file_hash
            )
            attrs.append(('ident_file_version', ident_file_version))

        device_model = DeviceModel(device)
        return device_model.update_device(attributes=attrs)

    @staticmethod
    def update_state(device, message):
        last_sync = message.get('LastSync')  # 同步开始/结束时间距离上报时间的秒数
        device_state = message.get('DeviceState')
        attrs = [
            ('working_status', device_state),
        ]
        device_model = DeviceModel(device)
        return device_model.update_device(attributes=attrs)
