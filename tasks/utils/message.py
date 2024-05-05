import base64
import hashlib
import hmac
import json
import time
from urllib.parse import quote_plus

import requests

def message2dingtalk(dingtalk_secret, dingtalk_access_token, content):
    print("Dingtalk 推送开始")
    timestamp = str(round(time.time() * 1000))
    sign = ""
    url=f'https://oapi.dingtalk.com/robot/send?access_token={dingtalk_access_token}&timestamp={timestamp}'
    if dingtalk_secret:
        secret_enc = dingtalk_secret.encode("utf-8")
        string_to_sign = f"{timestamp}\n{dingtalk_secret}"
        string_to_sign_enc = string_to_sign.encode("utf-8")
        hmac_code = hmac.new(
            secret_enc, string_to_sign_enc, digestmod=hashlib.sha256
        ).digest()
        sign = quote_plus(base64.b64encode(hmac_code))
        url+=f'&sign={sign}'
    send_data = {"msgtype": "text", "text": {"content": content}}
    requests.post(
        url="https://oapi.dingtalk.com/robot/send?access_token={}&timestamp={}&sign={}".format(
            dingtalk_access_token, timestamp, sign
        ),
        headers={"Content-Type": "application/json", "Charset": "UTF-8"},
        data=json.dumps(send_data),
        timeout=5,
    )
    return

def push_message(content_list: list, config_dic: dict):
    dingtalk_secret = config_dic.get("dingtalk_secret")
    dingtalk_access_token = config_dic.get("dingtalk_access_token")
    content_str = "\n————————————\n\n".join(content_list)
    message_list = [content_str]
    for message in message_list:
        if dingtalk_access_token and dingtalk_secret:
            try:
                message2dingtalk(
                    dingtalk_secret=dingtalk_secret,
                    dingtalk_access_token=dingtalk_access_token,
                    content=message,
                )
            except Exception as e:
                print("钉钉推送失败", e)
