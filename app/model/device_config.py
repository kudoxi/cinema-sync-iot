from app.model.base import BaseModel
from app.core.table_store import TableStore
from app.core.iot import IoTCtl
from app.model.device import DeviceModel
from app.util.hash import hmac_sha1
from config import Config
from app.core.redis import red
from app.core.errors import RedisLockError
from redis.exceptions import LockError


class DeviceConfigModel(BaseModel):

    def __init__(self, device_name=0):
        self.device_name = int(device_name)
        self.table_device_config = TableStore('device_config')
        self.primary_key = 'device_name'
        self.attribute_columns = [
            'hardware_sn', 'iot_id', 'mqtt_passwd', 'device_secret',
        ]

    @property
    def mqtt_client_id(self):
        return str(self.device_name) + '|securemode=3,signmethod=hmacsha1|'

    @property
    def mqtt_username(self):
        return str(self.device_name) + '&' + Config['iot']['product_key']

    def mqtt_passwd(self, device_secret):
        content = 'clientId{}deviceName{}productKey{}'.format(
            self.device_name, self.device_name, Config['iot']['product_key']
        )
        return hmac_sha1(message=content, secret=device_secret)

    def create_device_config(self, hardware_sn):
        config = self.table_device_config.get_last_row(
            primary_key_names=self.primary_key,
            hardware_sn=hardware_sn,
        )
        if config:
            configs = self.row_normalize(config)
            self.device_name = configs['device_name']
            return self.mqtt_client_id, self.mqtt_username, configs['mqtt_passwd']

        try:
            with red.lock('register-device', blocking_timeout=1):
                last_config = self.table_device_config.get_last_row(self.primary_key)
                if last_config:
                    # 设备编号自增
                    last_device_name = self.row_normalize(last_config)['device_name']
                    self.device_name = last_device_name + 1
                else:
                    # 初始编号
                    self.device_name = 23000
        except LockError as e:
            raise RedisLockError(msg=str(e))

        # Todo transaction
        device_secret, iot_id = IoTCtl.register_device(device_name=self.device_name)
        mqtt_passwd = self.mqtt_passwd(device_secret)
        self.table_device_config.add_row(
            primary_key=[(self.primary_key, self.device_name)],
            attribute_columns=[
                ('hardware_sn', hardware_sn),
                ('iot_id', iot_id),
                ('mqtt_passwd', mqtt_passwd),
                ('device_secret', device_secret),
            ]
        )
        device_model = DeviceModel(self.device_name)
        device_model.create_device()

        return self.mqtt_client_id, self.mqtt_username, mqtt_passwd

    def get_device_config(self):
        result = self.table_device_config.get_row(
            primary_key=[(self.primary_key, self.device_name)]
        )
        return self.row_normalize(result)

    def get_device_configs(self, **attributes):
        result = self.table_device_config.get_rows(
            primary_key_names=self.primary_key, **attributes
        )
        return self.row_normalize(result)

    def delete_device_config(self, device_name):
        return self.table_device_config.delete_row(primary_key=[(self.primary_key, device_name)])
