import falcon
import base64
import M2Crypto
import ujson as json
from blinker import signal
from urllib.request import urlopen
from app.resource.base import BaseResource
from app.core.serialize import SyncProtocolDataAnalyser as ProtoDumper
from app.core.redis import red
from app.core.errors import RedisLockError
from redis.exceptions import LockError
from app.model.device_event import DeviceEventModel
from app.util.alert import ding_alert
from config import ENV


error = signal('ERROR')

online = signal('ONLINE')
offline = signal('OFFLINE')

attr_set = signal('ATTR_SET')
attr_query = signal('ATTR_QUERY')
attr_report = signal('ATTR_REPORT')

state_query = signal('STATE_QUERY')
state_report = signal('STATE_REPORT')

script_query = signal('SCRIPT_QUERY')

upgrade = signal('UPGRADE')
reboot = signal('REBOOT')


class IoTNotifyResource(BaseResource):

    def __init__(self):
        self.method = 'POST'
        if ENV == 'PROD':
            self.path = '/iot/notify'
        else:
            self.path = '/notify'

    def _auth(self, req):
        # https://help.aliyun.com/document_detail/32313.html
        headers = {k.lower(): v for k, v in req.headers.items()}

        # get string to signature
        service_str = "\n".join(sorted([
            "%s:%s" % (k, v) for k, v in headers.items() if k.startswith("x-mns-")
        ]))
        sign_header_list = []
        for key in ["content-md5", "content-type", "date"]:
            if key in headers.keys():
                sign_header_list.append(headers[key])
            else:
                sign_header_list.append("")
        str2sign = "%s\n%s\n%s\n%s" % (self.method, "\n".join(sign_header_list), service_str, self.path)

        # verify
        authorization = headers.get('authorization')
        try:
            signature = base64.b64decode(authorization)
            cert_str = urlopen(
                base64.b64decode(headers.get('x-mns-signing-cert-url')).decode()
            ).read()
        except TypeError:
            return False

        pubkey = M2Crypto.X509.load_cert_string(cert_str).get_pubkey()
        pubkey.reset_context(md='sha1')
        pubkey.verify_init()
        pubkey.verify_update(str2sign.encode())
        return pubkey.verify_final(signature)

    def on_get(self, req, resp):
        reset = req.get_param_as_bool('reset', required=False)
        if reset:
            red.set('yo', 0)
            resp.body = 'reset'
            return

        try:
            with red.lock('test', blocking_timeout=1):
                result = red.get('yo')
                if not result:
                    result = 0
                red.set('yo', int(result) + 1)
                result = red.get('yo')
        except LockError as e:
            raise RedisLockError(msg=str(e))

        resp.status = falcon.HTTP_726
        resp.body = result

    def on_post(self, req, resp):
        if not self._auth(req):
            resp.body = 'Access Denied'
            resp.status = falcon.HTTP_403
            return

        body = req.stream.read(req.content_length or 0)

        body_dict = json.loads(body)

        print(body_dict)

        message = json.loads(body_dict['Message'])
        device_name = int(message['device'])

        try:
            """
            http://static-aliyun-doc.oss-cn-hangzhou.aliyuncs.com/download/pdf/DNLKIT1831689_public_2_intl_zh-CN_2018-09-25.pdf
            {
                "lastTime":"2019-03-22 16:22:15.349",   // 状态变更时最后一次通信时间
                "utcLastTime":"2019-03-22T08:22:15.349Z",
                "clientIp":"60.177.97.64",
                "utcTime":"2019-03-22T08:22:15.356Z",
                "time":"2019-03-22 16:22:15.356",  // 发送通知时间
                "productKey":"a1LKBWmhOFE",
                "deviceName":"10004",
                "status":"online/offline"
            }
            """
            msg = json.loads(message['payload'])
            cmd = msg['status'].upper()
        except ValueError:
            # 目前除上下线事件消息外，其它均为 Base64 encode 之后的二进制消息
            payload = base64.b64decode(message['payload'])
            spda = ProtoDumper()
            msg = spda.dump(payload)

            if msg['State'] == 'Success':
                cmd = msg['Command'].upper()
            else:
                cmd = 'ERROR'

        sig = signal(cmd)
        sig.send(device_name, message=msg)

        resp.body = ''
        resp.content_type = falcon.MEDIA_HTML
        resp.status = falcon.HTTP_201


"""
以下处理设备 同步/异步 的 返回/上报 消息 & 上下线事件
"""


@error.connect
def error_evt(device, message):
    """
    协议解析错误
    """
    ding_alert(f'{device} 协议错误: {message}')

    # Todo 记录错误消息
    return


@online.connect
def online_evt(device, message):
    result = DeviceEventModel.online(device=device, message=message)
    if result:
        ip = message['clientIp']
        online_time = message['lastTime']
        ding_alert(f'{device} 上线 IP: {ip}  [{online_time}]')
    return


@offline.connect
def offline_evt(device, message):
    result = DeviceEventModel.offline(device=device, message=message)
    if result:
        offline_time = message['lastTime']
        ding_alert(f'{device} 离线  [{offline_time}]')
    return


@upgrade.connect
def upgrade_evt(device, message):
    ding_alert(f'{device} 升级: {message}')
    return


@state_report.connect
def state_report_evt(device, message):
    DeviceEventModel.update_state(device=device, message=message)

    ding_alert(f'{device} 上报设备状态: {message}')
    return


@state_query.connect
def state_query_evt(device, message):
    DeviceEventModel.update_state(device=device, message=message)

    ding_alert(f'{device} 查询设备状态: {message}')
    return


@attr_report.connect
def attr_report_evt(device, message):
    DeviceEventModel.update_attr(device=device, message=message)

    ding_alert(f'{device} 上报设备属性: {message}')
    return


@attr_query.connect
def attr_query_evt(device, message):
    DeviceEventModel.update_attr(device=device, message=message)

    ding_alert(f'{device} 查询设备属性: {message}')
    return


@attr_set.connect
def attr_set_evt(device, message):
    DeviceEventModel.update_attr(device=device, message=message)

    ding_alert(f'{device} 设置设备属性: {message}')
    return


@script_query.connect
def script_query_evt(device, message):
    DeviceEventModel.update_attr(device=device, message=message)

    ding_alert(f'{device} 查询设备脚本: {message}')
    return


@reboot.connect
def reboot_evt(device, message):
    ding_alert(f'{device} 重启: {message}')
    return
