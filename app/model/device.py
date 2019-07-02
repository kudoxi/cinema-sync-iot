from app.model.base import BaseModel
from app.model.device_cmd import DeviceCmdModel
from app.core.table_store import TableStore
from app.core.serialize import MasterSlaveType
from app.core.iot import IoTCtl
from app.core import errors


class DeviceModel(BaseModel):

    def __init__(self, device_name=0):
        self.device_name = int(device_name)
        self.table_device = TableStore('device')
        self.primary_key = 'device_name'

        # 索引 master(int) master_slave(str) script(str) cinema(str) online(int) working_status(int)
        self.index_name = 'sort_index'

        self.attribute_columns = [
            # 主设备编号/从设备编号/未设置、主、从、单主/主从延时秒数
            'master', 'slave', 'master_slave', 'sync_delay',
            # 未激活 -1 在线 1 离线 0/工作状态 空闲 0 同步中 1
            'online', 'working_status',
            # online & working_status 状态更新时间 防止乱序消息
            'time_online', 'time_working_status',
            # 逻辑信道/物理信道
            'logical_channel', 'physical_channel',
            # 影院ID/影院名称/影厅ID/影厅名称
            'cinema_id', 'cinema', 'hall_id', 'hall',

            # 脚本名称/脚本ID/脚本MD5
            'script', 'script_id', 'script_hash',
            # 同步固件版本号/识别程序固件版本号/识别特征值文件版本号/识别特征值文件MD5
            'sync_version', 'ident_version', 'ident_file_version', 'ident_file_hash',
            # SIM卡号/硬件整体版本号/同步Boot版本号/识别程序Boot版本号
            'sim', 'hardware_version', 'sync_boot_version', 'ident_boot_version',

            # 将要下载的脚本名称/同步固件版本号/识别固件版本号/特征值文件版本号
            'new_script', 'new_sync', 'new_ident', 'new_ident_file',
            # 脚本/同步固件/识别固件/特征值文件 下载失败 -1 下载成功 0 下载中 1
            'download_script', 'download_sync', 'download_ident', 'download_ident_file',
        ]

    def set_device(self, device_name):
        self.device_name = device_name

    def create_device(self):
        # 设备烧写完成 尚未上线
        return self.table_device.add_row(
            primary_key=[(self.primary_key, self.device_name)],
            attribute_columns=[
                ('online', -1),
                ('master', 0),
                ('slave', 0),
                ('master_slave', MasterSlaveType.NOT_SET.name),
            ],
        )

    def update_device(self, attributes, expect=''):
        return self.table_device.update_row(
            primary_key=[(self.primary_key, self.device_name)],
            attribute_columns={'PUT': attributes},
            expect=expect,
        )

    def get_device(self, device_name=0):
        device = device_name if device_name else self.device_name
        result = self.table_device.get_row([(self.primary_key, device)])
        return self.row_normalize(result)

    def get_devices(self, page=1, limit=10, equal=None, not_equal=None):
        rows, total_count = self.table_device.pagination(
            index_name=self.index_name,
            offset=(page - 1) * limit,
            limit=limit,
            equal=equal,
            not_equal=not_equal,
            sort_fields_and_order=[
                ('master', 'asc'),
                ('master_slave', 'asc'),
            ],
        )
        return self.page_normalize(rows), total_count

    def unbind_device(self, device_name):
        devices, _ = self.get_devices(
            limit=2, equal={'master': [device_name, ]}
        )
        if devices:
            for v in devices:
                working_status = v.get('working_status')
                if working_status == 1:
                    raise errors.HTTPIoTError(
                        error=str(v['device_name']) + '号设备正在工作中 请稍后再试'
                    )
            for v in devices:
                # 恢复出厂配置
                DeviceCmdModel.attr_set(
                    device=v['device_name'],
                    sync=True,
                    master_slave=MasterSlaveType.NOT_SET,
                    physical_chan=150,
                    logical_chan=0,
                )
                self.set_device(device_name=v['device_name'])
                self.update_device(attributes=[
                    ('master', 0),
                    ('slave', 0),
                    ('master_slave', MasterSlaveType.NOT_SET.name),
                    ('cinema_id', 0),
                    ('cinema', ''),
                    ('hall_id', 0),
                    ('hall', ''),
                ], expect='EXIST')

        return

    def delete_device(self, device_name):
        IoTCtl.delete_device(device_name=device_name)
        return self.table_device.delete_row(primary_key=[(self.primary_key, device_name)])
