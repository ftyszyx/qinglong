from flask import request, make_response, Response
from pydantic import BaseModel
from typing import *
import logging
import json
import hashlib

LARK_REQUEST_TIMESTAMP = "X-Lark-Request-Timestamp"
LARK_REQUEST_NONCE = "X-Lark-Request-Nonce"
LARK_REQUEST_SIGNATURE = "X-Lark-Signature"
X_REQUEST_ID = "X-Request-Id"
UTF_8 = "UTF-8"


class RawRequest(BaseModel):
    uri: str = ""
    body: bytes = None
    headers: Dict[str, str] = {}


class RawResponse(BaseModel):
    status_code: int = None
    headers: Dict[str, str] = {}
    content: bytes = None

    def set_content_type(self, content_type: str) -> None:
        self.headers["Content-Type"] = content_type


def _parse_req() -> RawRequest:
    headers = {}
    for pair in request.headers.to_wsgi_list():
        headers[pair[0]] = pair[1]
    req = RawRequest()
    req.uri = request.path
    req.body = request.data
    req.headers = headers
    return req


def _parse_resp(response: RawResponse) -> Response:
    resp = make_response(str(response.content, "UTF-8"))
    resp.status_code = response.status_code
    for k, v in response.headers.items():
        resp.headers[k] = v
    return resp


class CardAction(BaseModel):
    value: Dict[str, Any] = {}
    tag: str = None
    option: str = None
    timezone: str = None


class CardReq(BaseModel):
    open_id: str = ""
    user_id: str = ""
    tenant_key: str = ""
    open_message_id: str = ""
    open_chat_id: str = ""
    token: str = ""
    challenge: str = ""
    type: str = ""
    action: CardAction = None
    raw: RawRequest = None


class CardListenerHandler:
    _encrypt_key: str = ""
    _check_token: str = ""
    _handler: Callable[[CardReq], Any] = None

    def __init__(
        self, check_token: str, encrypt_key: str, handler: Callable[[CardReq], Any]
    ) -> None:
        self._encrypt_key = encrypt_key
        self._check_token = check_token
        self._handler = handler

    def process(self) -> Response:
        req = _parse_req()
        logging.debug("req:%s", req.json(exclude_none=True, ensure_ascii=False))
        resp = RawResponse()
        resp.status_code = 200
        resp.set_content_type("application/json;charset=utf-8")
        try:
            if req.body is None:
                raise RuntimeError("request body is null")
            # 反序列化
            req_str = str(req.body, UTF_8)
            card_json = json.loads(req_str)
            card = CardReq.parse_obj(card_json)
            card.raw = req
            if "url_verification" == card.type:
                if self._check_token != card.token:
                    raise RuntimeError("invalid verification_token")
                # 返回 Challenge Code
                resp_body = '{"challenge":"%s"}' % card.challenge
                resp.content = resp_body.encode(UTF_8)
                print(f"resp:{resp.json()}")
                return _parse_resp(resp)
            else:
                # 否则验签
                self._verify_sign(req)
            if self._handler is None:
                raise RuntimeError("processor not found")

            # 处理业务逻辑
            result: Any = self._handler(card)
            # 返回结果
            if result is None:
                resp.content = '{"msg":"success"}'.encode(UTF_8)
            elif isinstance(result, bytes):
                resp.content = result
            elif isinstance(result, str):
                resp.content = bytes(result, UTF_8)
            elif isinstance(result, RawResponse):
                resp = result
            else:
                resp.content = json.dumps(result).encode(UTF_8)
            return _parse_resp(resp)

        except Exception as e:
            logging.exception(
                "handle card err:url:%s request_id:%s err:%s",
                req.uri,
                req.headers.get(X_REQUEST_ID),
                e,
            )
            resp.status_code = 500
            resp_body = '{"msg":"%s"}' % str(e)
            resp.content = resp_body.encode(UTF_8)
            return _parse_resp(resp)

    def _verify_sign(self, request_data: RawRequest) -> None:
        timestamp = request_data.headers.get(LARK_REQUEST_TIMESTAMP)
        nonce = request_data.headers.get(LARK_REQUEST_NONCE)
        signature = request_data.headers.get(LARK_REQUEST_SIGNATURE)
        bs = (timestamp + nonce + self._check_token).encode("UTF-8") + request_data.body
        h = hashlib.sha1(bs)
        if signature != h.hexdigest():
            raise RuntimeError("signature verification failed")
