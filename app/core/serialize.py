import time
import random
import re
from enum import Enum


class UpgradeType(Enum):
    # 0=同步芯片固件
    SYNC_FIRMWARE = 0x00
    # 1=脚本
    SCRIPT = 0x01
    # 2=识别芯片固件
    IDENT_FIRMWARE = 0x02
    # 3=识别芯片特征文件
    IDENT_FILE = 0x03


class MasterSlaveType(Enum):
    # 7 未初始化
    NOT_SET = 0x07
    # 3 从
    SLAVE = 0x03
    # 0 主
    MASTER = 0x00
    # 2 有从的主
    MASTER_WITH_SLAVE = 0x02


class ProtocolInstructions(Enum):
    # 读取脚本 MD5
    SCRIPT_QUERY = 0x03
    # 设置同步器参数（物理信道、主从、信道）
    ATTR_SET = 0x04
    # 读取同步器参数
    ATTR_QUERY = 0x05
    # 同步器主动上报参数
    ATTR_REPORT = 0x85
    # 服务端控制同步器重启
    REBOOT = 0x06
    # 服务器通知设备升级脚本\固件\特征文件
    UPGRADE = 0x0a
    # 同步器上报工作状态
    STATE_REPORT = 0x8f
    # 服务端读取同步器工作状态
    STATE_QUERY = 0x0f


class ProtocolPackage:
    Header = 0xf5
    Version = 1.1
    RequestID = 0
    FunctionCode = 0x00
    # 数据包总长度 - 4
    PayloadLength = 0x00
    Payload = []
    CheckSum = 0
    End = 0x55

    ByteData = []
    MinPackageLength = 13

    def __init__(self, version=1.1):
        self.Version = version

    def load_from_byte_array(self, byte_array):
        if len(byte_array) < self.MinPackageLength:
            raise SyncProtocolException(
                f"Data Length Smaller Than MinPackageLength {self.MinPackageLength}",
                payload=byte_array.hex()
            )
        if byte_array[0] != self.Header:
            raise SyncProtocolException("Header Not Match", byte_array.hex())

        self.Version = byte_array[1] + byte_array[2] / 10.0
        self.RequestID = self.byte2number(byte_array, 3, 4)
        self.FunctionCode = byte_array[7]
        self.PayloadLength = self.byte2number(byte_array, 8, 2) - 3
        package_length = self.PayloadLength + self.MinPackageLength
        if len(byte_array) < package_length:
            raise SyncProtocolException(
                "Data Length Smaller Than Package Length (%d)" % package_length + 4,
                payload=byte_array.hex(),
            )
        self.Payload = byte_array[10:10 + self.PayloadLength]
        self.CheckSum = self.byte2number(byte_array, package_length - 3, 2)
        cal_check_sum = self.cal_check_sum(byte_array, 7, self.PayloadLength + 3)
        if cal_check_sum != self.CheckSum:
            raise SyncProtocolException(
                "校验和错误 (Expect %02x,Got %02x)" % (cal_check_sum, self.CheckSum),
                payload=byte_array.hex()
            )

        return True

    @staticmethod
    def cal_check_sum(byte_array, start, length):
        val = 0
        for i in range(start, start + length):
            val += byte_array[i]
        return val & 0xffff

    @staticmethod
    def int2bytes(integer, bytes_num=4):
        arr = []
        for i in range(bytes_num):
            arr.append((integer >> (8 * (bytes_num - i - 1))) & 0xff)
        return list(bytes(arr))

    @staticmethod
    def byte2number(byte_array, start=0, number_byte_count=4):
        val = 0
        for i in range(start, start + number_byte_count):
            val = (val << 8) + byte_array[i]
        return val

    @staticmethod
    def generate_request_id():
        return int("%04d" % random.randint(10000, 100000) + "%06d" % int(str(time.time())[5:10])) & 0xffffffff

    def to_byte_array(self, new_req_id=True):
        version_seg = str(self.Version).split('.', 2)
        self.PayloadLength = len(self.Payload)
        data_length = self.PayloadLength + 3
        if new_req_id:
            self.RequestID = self.generate_request_id()
        byte_array = [self.Header, int(version_seg[0]), int(version_seg[1])] + \
            self.int2bytes(self.RequestID) + [self.FunctionCode] + \
            self.int2bytes(data_length, 2) + self.Payload + \
            self.int2bytes(self.CheckSum, 2) + [self.End]
        package_length = len(byte_array)
        cal_check_sum = self.cal_check_sum(byte_array, 7, data_length)
        byte_array[package_length - 3] = (cal_check_sum >> 8) & 0xff
        byte_array[package_length - 2] = cal_check_sum & 0xff
        return bytes(byte_array)

    @staticmethod
    def ipaddress2bytes(ipaddress):
        """
        ip 地址转字节
        :param ipaddress:
        :return:
        """
        seg = ipaddress.split(".")
        return [int(seg[0]), int(seg[1]), int(seg[2]), int(seg[3])]

    @staticmethod
    def byte2version(byte_array, start=0, prefix="v"):
        """
        byte 数组转版本号（v1.2.3）
        :param byte_array:
        :param start:
        :param prefix:
        :return:
        """
        return prefix + "%d.%d.%d" % (byte_array[start], byte_array[start + 1], byte_array[start + 2])

    @staticmethod
    def parse_version2bytes(version):
        """
        解析 vx.y.z 的版本号为三个字节的数组
        :param version: 版本号字符串
        :return:
        """
        version = version.lower().replace("v", "")
        seg = version.split(".")
        return [int(seg[0]), int(seg[1]), int(seg[2])]


class SyncProtocolException(Exception):
    def __init__(self, error, payload=''):
        self.error = error
        self.payload = payload

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"{self.error}  payload: [{self.payload}]"


class SyncProtocolInstructionAssembler(ProtocolPackage):
    """
    用于组装协议
    """

    def simulate_resp_base(self, function_code, result=0):
        self.FunctionCode = function_code
        self.Payload = [result] + [0, 0, 0, 0]
        return self.to_byte_array()

    def simulate_resp_query_script(self, md5_val="28fdc23fe3c2fba26bf0067a4f337494", result=0):
        """
        模拟查询脚本md5回复
        :param md5_val:
        :param result:
        :return:
        """
        self.FunctionCode = ProtocolInstructions.SCRIPT_QUERY.value
        self.Payload = [result] + list(bytes.fromhex(md5_val))
        return self.to_byte_array()

    def simulate_resp_attr_set(self, result=0):
        """
        模拟设置参数回复
        :param result:
        :return:
        """
        return self.simulate_resp_base(ProtocolInstructions.ATTR_SET.value, result)

    def simulate_resp_attr_read(self, result=0):
        """
        模拟回复读取参数
        :param result:
        :return:
        """
        self.FunctionCode = ProtocolInstructions.ATTR_QUERY.value

        result = result
        hardware_version = "1.2.3"
        sync_chip_boot_version = "2.3.4"
        sync_chip_firmware_version = "4.5.6"
        identification_chip_boot_version = "1.2.34"
        identification_chip_firmware_version = "33.2.2"
        script_md5 = "28fdc23fe3c2fba26bf0067a4f337494"
        identification_file_md5 = "28fdc23fe3c2fba26bf0067a4f337494"
        sim_code = "3839383630343430313131384333373138313137"
        master_slave = MasterSlaveType.NOT_SET.value
        sync_delay_second = 1
        physical_channel = 0x96
        channel = 0x60
        device_state = 2

        self.Payload = [result] + self.parse_version2bytes(hardware_version) + \
            self.parse_version2bytes(sync_chip_boot_version) + \
            self.parse_version2bytes(sync_chip_firmware_version) + \
            self.parse_version2bytes(identification_chip_boot_version) + \
            self.parse_version2bytes(identification_chip_firmware_version) + \
            list(bytes.fromhex(script_md5)) + \
            list(bytes.fromhex(identification_file_md5)) + \
            list(bytes.fromhex(sim_code)) + \
            [master_slave, sync_delay_second, physical_channel, channel, device_state] + [0] * 14
        return self.to_byte_array()

    def simulate_resp_remote_operations(self, result=0):
        """
        模拟回复 远程操作
        :param result:
        :return:
        """
        return self.simulate_resp_base(ProtocolInstructions.REBOOT.value, result)

    def simulate_resp_resource_download_broadcast(self, result=0):
        """
        模拟回复 下载程序
        :param result:
        :return:
        """
        return self.simulate_resp_base(ProtocolInstructions.UPGRADE.value, result)

    def simulate_resp_report_state(self, result=0, sync_time=12344, status=1):
        """
        模拟回复读取工作状态
        :param result:
        :param sync_time:
        :param status:
        :return:
        """
        self.FunctionCode = ProtocolInstructions.STATE_QUERY.value
        self.Payload = [result] + self.int2bytes(sync_time, 4) + [status, 0, 0, 0, 0]
        return self.to_byte_array()

    def load(self, function_code: ProtocolInstructions, **parameters) -> bytes:
        """
        协议序列化
        :param function_code: ProtocolInstructions
        :param parameters:
             ProtocolInstructions.REBOOT，
                传入 operation_code     表示操作码    操作码 001  同步器重启
             ProtocolInstructions.ATTR_SET，
                传入 master_slave  主从模式      MasterSlaveType，默认 MasterSlaveType.MASTER
                     sync_delay:        同步延时时间，单位秒 默认 0x00
                     physical_channel   物理信道      默认 0x96
                     channel            信道          默认 0x00
             ProtocolInstructions.UPGRADE，
                传入 type_id            资源类别          0=同步芯片固件，1=脚本，2=识别芯片固件，3=识别芯片特征文件
                     resource_id        资源编号或者版本号，脚本为 脚本编号，其他为版本号，格式 1.2.3
                     resource_md5       资源md5
                     server_ip          下载用 tcp 服务端 ip
                     server_port        下载用 tcp 服务端 port
             其他无参数
        :return: bytearray
        """
        if function_code == ProtocolInstructions.SCRIPT_QUERY:
            return self.assemble_request_query_script_ins()

        if function_code == ProtocolInstructions.ATTR_QUERY:
            return self.assemble_request_attribute_read_ins()

        if function_code == ProtocolInstructions.REBOOT:
            if "operation_code" not in parameters:
                parameters["operation_code"] = 1
            return self.assemble_request_remote_operations_ins(parameters["operation_code"])

        if function_code == ProtocolInstructions.STATE_QUERY:
            return self.assemble_request_read_working_state_ins()

        if function_code == ProtocolInstructions.ATTR_SET:
            if "master_slave" not in parameters:
                parameters["master_slave"] = MasterSlaveType.MASTER.value
            if parameters["master_slave"] in MasterSlaveType:
                parameters["master_slave"] = parameters["master_slave"].value
            else:
                raise SyncProtocolException(f"master_slave value {parameters['master_slave']} error")
            if "sync_delay" not in parameters:
                parameters["sync_delay"] = 0x00
            if "physical_channel" not in parameters:
                parameters["physical_channel"] = 0x96
            if "channel" not in parameters:
                parameters["channel"] = 0
            return self.assemble_request_attribute_setting_ins(
                parameters["master_slave"],
                parameters["sync_delay"],
                parameters["physical_channel"],
                parameters["channel"]
            )

        if function_code == ProtocolInstructions.UPGRADE:
            params = ["type_id", "resource_id", "resource_md5", "server_ip", "server_port"]
            for i in range(0, len(params)):
                if params[i] not in parameters:
                    raise SyncProtocolException(f"Param {params[i]} Not Found")
            if type(parameters["type_id"]) is UpgradeType:
                parameters["type_id"] = parameters["type_id"].value
            return self.assemble_notify_resource_download_ins(
                parameters["type_id"],
                parameters["resource_id"],
                parameters["resource_md5"],
                parameters["server_ip"],
                parameters["server_port"]
            )

    def assemble_request_query_script_ins(self):
        """
        拼装读取脚本md5的协议
        :return: byte list
        """
        self.FunctionCode = ProtocolInstructions.SCRIPT_QUERY.value
        self.Payload = []
        return self.to_byte_array()

    def assemble_request_attribute_read_ins(self):
        """
        拼装读取设备信息的协议
        :return: byte list
        """
        self.FunctionCode = ProtocolInstructions.ATTR_QUERY.value
        self.Payload = []
        return self.to_byte_array()

    def assemble_request_remote_operations_ins(self, operation_code):
        """
        拼装远程操作设备的协议
        :param operation_code: 操作码 001  同步器重启
        :return: byte list
        """
        self.FunctionCode = ProtocolInstructions.REBOOT.value
        self.Payload = [operation_code, 0, 0, 0]
        return self.to_byte_array()

    def assemble_request_read_working_state_ins(self):
        """
        拼装主动读取设备工作信息的协议
        :return:
        """
        self.FunctionCode = ProtocolInstructions.STATE_QUERY.value
        return self.to_byte_array()

    def assemble_request_attribute_setting_ins(self, master_slave, sync_delay, physical_channel, channel):
        """
        拼装同步器参数设置的协议
        :param master_slave:  设备模式  0/1（0=主，1=从）
        :param sync_delay: 同步延时时间，单位秒
        :param physical_channel:设备物理地址  0x96
        :param channel:设备信道  0x00
        :return:
        """
        self.FunctionCode = ProtocolInstructions.ATTR_SET.value
        self.Payload = [0] * 18
        self.Payload[0] = master_slave
        self.Payload[1] = sync_delay
        self.Payload[2] = physical_channel
        self.Payload[3] = channel
        return self.to_byte_array()

    def assemble_notify_resource_download_ins(self, type_id, resource_id, resource_md5, server_ip, server_port):
        """
        组装 通知设备 下载脚本\升级同步芯片固件\升级识别芯片固件\升级特征文件
        :param type_id:  0=同步芯片固件，1=脚本，2=识别芯片固件，3=识别芯片特征文件
        :param resource_id: 资源编号，脚本为 脚本编号，其他为版本号，格式 1.2.3
        :param resource_md5: 资源 md5
        :param server_ip: 同步器需要连接的 tcp 服务器 ip
        :param server_port: 同步器需要连接的 tcp 服务器 端口
        :return: byte array
        """
        if type_id == UpgradeType.SCRIPT or type_id == UpgradeType.SCRIPT.value:
            resource_str = str(resource_id)
            if re.match('^\d+$', resource_str) is None:
                raise SyncProtocolException("脚本编号解析失败，请传入正确格式的脚本编号（类似 542）")
            type_byte = self.int2bytes(int(resource_str), 4)
        else:
            resource_id = str(resource_id)
            if re.match('^[vV]\d+(\.\d+){2}$', resource_id) is None:
                raise SyncProtocolException("版本号解析失败，请传入正确格式的版本号（类似 v1.2.3）")
            type_byte = [0] + self.parse_version2bytes(resource_id)

        self.FunctionCode = ProtocolInstructions.UPGRADE.value
        self.Payload = [type_id] + type_byte \
            + self.ipaddress2bytes(server_ip) \
            + self.int2bytes(server_port, 2) \
            + list(bytes.fromhex(resource_md5)) \
            + [0, 0, 0, 0]
        return self.to_byte_array()


class SyncProtocolDataAnalyser(SyncProtocolInstructionAssembler):
    """
    用于解析协议
    """

    @staticmethod
    def parse_function_code(function_code):
        """
        功能码转解析函数名称
        :param function_code:
        :return:
        """
        prefix = "parse_response__"
        return prefix + ProtocolInstructions(function_code).name.lower()

    @staticmethod
    def parse_response__script_query(package):
        """
        处理读取脚本md5
        :param package:
        :return:
        """
        return {
            "State": "Success",
            "RequestID": package.RequestID,
            "Command": ProtocolInstructions(package.FunctionCode).name,
            "Result": package.Payload[0],
            "MD5": bytes(package.Payload[1:17]).hex()
        }

    @staticmethod
    def parse_response__attr_set(package):
        """
        处理设置设备属性
        :param package:
        :return:
        """
        return {
            "State": "Success",
            "RequestID": package.RequestID,
            "Command": ProtocolInstructions(package.FunctionCode).name,
            "Result": package.Payload[0],
            "MasterSlave": MasterSlaveType(package.Payload[1]).name,
            "SyncDelaySecond": package.Payload[2],
            "PhysicalChannel": package.Payload[3],
            "LogicalChannel": package.Payload[4],
        }

    @staticmethod
    def parse_response__attr_query(package):
        """
        处理读取设备属性
        :param package:
        :return:
        """
        return {
            "State": "Success",
            "RequestID": package.RequestID,
            "Command": ProtocolInstructions(package.FunctionCode).name,
            "Result": package.Payload[0],
            "HardwareVersion": SyncProtocolDataAnalyser.byte2version(package.Payload, 1),
            "SyncBootVersion": SyncProtocolDataAnalyser.byte2version(package.Payload, 4),
            "SyncVersion": SyncProtocolDataAnalyser.byte2version(package.Payload, 7),
            "IdentBootVersion": SyncProtocolDataAnalyser.byte2version(package.Payload, 10),
            "IdentVersion": SyncProtocolDataAnalyser.byte2version(package.Payload, 13),
            "ScriptMD5": bytes(package.Payload[16:32]).hex(),
            "IdentFileMD5": bytes(package.Payload[32:48]).hex(),
            "SIMCode": str(bytes(package.Payload[48:68]), encoding="UTF-8"),
            "MasterSlave": MasterSlaveType(package.Payload[68]).name,
            "SyncDelaySecond": package.Payload[69],
            "PhysicalChannel": package.Payload[70],
            "LogicalChannel": package.Payload[71],
            "DeviceState": package.Payload[72],
        }

    @staticmethod
    def parse_response__attr_report(package):
        """
        处理设备主动上报设备属性
        :param package:
        :return:
        """
        return SyncProtocolDataAnalyser.parse_response__attr_query(package)

    @staticmethod
    def parse_response__reboot(package):
        """
        处理远程控制设备的回复
        :param package:
        :return:
        """
        return {
            "State": "Success",
            "RequestID": package.RequestID,
            "Command": ProtocolInstructions(package.FunctionCode).name,
            "Result": package.Payload[0],
        }

    @staticmethod
    def parse_response__upgrade(package):
        """
        处理广播通知下载脚本\升级同步芯片固件\升级识别芯片固件\升级特征文件
        :param package:
        :return:
        """
        return {
            "State": "Success",
            "RequestID": package.RequestID,
            "Command": ProtocolInstructions(package.FunctionCode).name,
            "Result": package.Payload[0],
        }

    @staticmethod
    def parse_response__state_report(package):
        """
        处理设备主动上报工作状态
        :param package:
        :return:
        """
        return {
            "State": "Success",
            "RequestID": package.RequestID,
            "Command": ProtocolInstructions(package.FunctionCode).name,
            "Result": package.Payload[0],
            "LastSync": ProtocolPackage.byte2number(package.Payload, 1, 4),
            "DeviceState": package.Payload[6],
        }

    @staticmethod
    def parse_response__state_query(package):
        """
        处理服务端主动请求设备工作状态
        :param package:
        :return:
        """
        return SyncProtocolDataAnalyser.parse_response__state_report(package)

    def dump(self, bytes_data):
        """
        数据转换
        :param bytes_data:
        :return:
        """
        byte_array = bytes_data
        if bytes_data is bytes:
            byte_array = list(bytes_data)
        pk = ProtocolPackage()
        try:
            pk.load_from_byte_array(byte_array)
            return getattr(SyncProtocolDataAnalyser, self.parse_function_code(pk.FunctionCode))(pk)
        except Exception as ex:
            return {
                "State": "Failure",
                "Message": str(ex)
            }
