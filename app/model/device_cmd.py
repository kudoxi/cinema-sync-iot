import base64
from app.model.base import BaseModel
from app.core.serialize import (
    ProtocolInstructions as Cmd,
    SyncProtocolInstructionAssembler as ProtoLoader,
    SyncProtocolDataAnalyser as ProtoDumper,
)
from app.core import errors
from app.core.iot import IoTCtl
from blinker import signal
from config import Config


class DeviceCmdModel(BaseModel):

    @classmethod
    def send(cls, device, message, sync):
        """
        同步返回消息
        {
            "MessageId": 1110512264470883840,
            "RequestId": "898F7877-7F62-418D-9D34-8762FDCD006D",
            "PayloadBase64Byte": "9QEBUw2CAQoACAAAAAAAABJV",
            "Success": true,
            "RrpcCode": "SUCCESS"
        }
        异步返回消息
        {
            "MessageId": 1110512330652827648,
            "RequestId": "684A0BB9-402F-4557-A61F-F54E53637D0C",
            "Success": true
        }
        """
        if sync:
            # 发送同步消息
            sync_result = IoTCtl.rrpc_message(
                device_name=device,
                message=message,
            )
            pd = ProtoDumper()
            payload = pd.dump(
                base64.b64decode(sync_result['PayloadBase64Byte'])
            )

            if payload['State'] == 'Success':
                cmd = payload['Command'].upper()
            else:
                cmd = 'ERROR'

            sig = signal(cmd)
            sig.send(device, message=payload)

            if payload['State'] != 'Success':
                raise errors.HTTPIoTError(error=payload['Message'])
            return payload

        # 发送异步消息
        product_key = Config['iot']['product_key']
        return IoTCtl.publish_message(
            topic=f'/{product_key}/{device}/get',
            message=message,
        )

    @classmethod
    def upgrade(cls, device, sync, **kwargs):
        pl = ProtoLoader()
        message = pl.load(
            function_code=Cmd.UPGRADE,
            type_id=kwargs.get('type'),
            resource_id=kwargs.get('res'),
            resource_md5=kwargs.get('md5'),
            server_ip=kwargs.get('ip'),
            server_port=kwargs.get('port'),
        )
        return cls.send(device, message, sync)

    @classmethod
    def state_query(cls, device, sync):
        pl = ProtoLoader()
        message = pl.load(function_code=Cmd.STATE_QUERY)
        return cls.send(device, message, sync)

    @classmethod
    def script_query(cls, device, sync):
        pl = ProtoLoader()
        message = pl.load(function_code=Cmd.SCRIPT_QUERY)
        return cls.send(device, message, sync)

    @classmethod
    def attr_query(cls, device, sync):
        pl = ProtoLoader()
        message = pl.load(function_code=Cmd.ATTR_QUERY)
        return cls.send(device, message, sync)

    @classmethod
    def attr_set(cls, device, sync, **kwargs):
        pl = ProtoLoader()
        message = pl.load(
            function_code=Cmd.ATTR_SET,
            master_slave=kwargs.get('master_slave'),
            physical_channel=kwargs.get('physical_chan'),
            channel=kwargs.get('logical_chan'),
        )
        return cls.send(device, message, sync)

    @classmethod
    def reboot(cls, device, sync, **kwargs):
        pl = ProtoLoader()
        message = pl.load(
            function_code=Cmd.REBOOT,
            operation_code=kwargs.get('op', 1),
        )
        return cls.send(device, message, sync)
