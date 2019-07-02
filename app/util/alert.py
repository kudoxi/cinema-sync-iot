import requests
from config import Config


def ding_alert(message):
    ding_url = Config['dingding']['url']
    if isinstance(message, bytes):
        message = message.decode()
    r = requests.post(ding_url, json={
        'msgtype': 'text',
        'text': {
            'content': str(message)
        }
    })
    return r.text
