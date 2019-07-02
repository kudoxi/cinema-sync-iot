import ujson as json
from config import Config
from app.core import errors
from aliyunsdkcore import client
from aliyunsdkiot.request.v20180120 import (
    RegisterDeviceRequest, DeleteDeviceRequest,
    QueryDeviceRequest, QueryDeviceDetailRequest,
    ListRuleRequest,
    PubRequest, PubBroadcastRequest, RRpcRequest,
)
from base64 import b64encode


class IoTController:
    def __init__(self):
        self.ctl = client.AcsClient(
            ak=Config['aliyun']['access_key'],
            secret=Config['aliyun']['access_secret'],
            region_id=Config['iot']['region'],
        )
        self.device = 0

    def _request(self, request, set_product_key=True):
        if set_product_key:
            request.set_ProductKey(Config['iot']['product_key'])
        result = self.ctl.do_action_with_exception(request)
        r_dict = json.loads(result)

        if 'Success' not in r_dict or r_dict['Success'] is not True:
            error_msg = '' if 'Code' not in r_dict else r_dict['Code']
            error = ''
            iot_error = ''

            # https://help.aliyun.com/document_detail/87387.html
            if error_msg.endswith('OFFLINE'):
                error = '设备离线'
                iot_error = 'OFFLINE'
            elif error_msg.endswith('TIMEOUT'):
                error = '设备响应超时或已掉线'
                iot_error = 'TIMEOUT'

            if error:
                error_msg = f'{error}: {error_msg}'

            raise errors.HTTPIoTError(
                error=error_msg, iot_error=iot_error, device=self.device
            )
        return r_dict

    def register_device(self, device_name):
        request = RegisterDeviceRequest.RegisterDeviceRequest()
        request.set_DeviceName(device_name)
        result = self._request(request=request)
        return result['Data']['DeviceSecret'], result['Data']['IotId']

    def query_device_detail(self, device_name):
        request = QueryDeviceDetailRequest.QueryDeviceDetailRequest()
        request.set_DeviceName(device_name)
        result = self._request(request=request)
        return result

    def list_devices(self, current_page=1, page_size=50):
        request = QueryDeviceRequest.QueryDeviceRequest()
        request.set_CurrentPage(current_page)
        request.set_PageSize(page_size)
        result = self._request(request=request)
        return result

    def delete_device(self, device_name):
        request = DeleteDeviceRequest.DeleteDeviceRequest()
        request.set_DeviceName(device_name)
        self._request(request=request)
        return True

    def publish_message(self, topic, message, qos=0):
        # Topic is like '/a1LKBWmhOFE/23001/get'
        self.device = int(topic.split('/')[2])

        request = PubRequest.PubRequest()
        request.set_Qos(qos)
        request.set_TopicFullName(topic)
        request.set_MessageContent(b64encode(message))
        result = self._request(request=request)
        return result

    def broadcast_message(self, topic, message):
        # https://help.aliyun.com/document_detail/69909.html
        request = PubBroadcastRequest.PubBroadcastRequest()
        request.set_TopicFullName(topic)
        request.set_MessageContent(b64encode(message))
        result = self._request(request=request)
        return result

    def rrpc_message(self, device_name, message, timeout=5000, topic=None):
        self.device = int(device_name)

        request = RRpcRequest.RRpcRequest()
        request.set_DeviceName(device_name)
        request.set_Timeout(timeout)  # 1000 ~ 5000 ms
        request.set_RequestBase64Byte(b64encode(message))
        if topic:
            request.set_Topic(topic)
        result = self._request(request=request)
        return result

    def list_rule(self):
        request = ListRuleRequest.ListRuleRequest()
        request.set_PageSize(100)
        request.set_CurrentPage(1)
        result = self._request(request=request, set_product_key=False)
        return result


IoTCtl = IoTController()
