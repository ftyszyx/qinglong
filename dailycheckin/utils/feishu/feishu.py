import json
from requests import Response
from requests_html import HTMLSession
import uuid
import logging
import time
from typing import List, Dict
from .feishu_def import (
    GroupMember,
    GroupInfo,
    MsgCard_Config,
    MsgCard_Element,
    MsgCardColumn,
    MsgCard_Text,
    MsgCard_Header,
    MsgCard_ElementAction,
)
from pydantic import BaseModel
from typing import List


class CardMsgRoot(BaseModel):
    config: MsgCard_Config = MsgCard_Config()
    elements: List[MsgCard_Element] = []
    header: MsgCard_Header = MsgCard_Header()


class FeiShuHelp:
    _appid = ""
    _appsecret = ""
    _token = ""
    _group_list: List[GroupInfo] = []

    def __init__(self, appid, appsecret):
        self._appid = appid
        self._appsecret = appsecret
        self.session = HTMLSession()
        self.session.verify = False  # fiddle抓包
        self.headers = {
            "Content-Type": "application/json",
        }
        self._init_data()

    def _checkErr(self, res: Response):
        retjson = json.loads(res.text)
        if retjson["code"] == 99991663 or retjson["code"] == 99991661:
            logging.debug("token过期，重新获取")
            self._get_token()
            return True
        return False

    # 请求
    def _get(self, url, **kwargs) -> Response:
        kwargs.setdefault("headers", self.headers)
        try:
            ret = self.session.get(url, timeout=10, **kwargs)
            if self._checkErr(ret):
                ret = self.session.get(url, timeout=10, **kwargs)
        except Exception as e:
            time.sleep(2)
            logging.debug("session过期：重新登录:%s", str(e))
            self._get_token()
            res = self.session.get(url, timeout=10, **kwargs)
            return res
        return ret

    # post
    def _post(self, url, dictdata=None, json_data=None, **kwargs) -> Response:
        kwargs.setdefault("headers", self.headers)
        try:
            ret = self.session.post(
                url, data=dictdata, json=json_data, timeout=10, **kwargs
            )
            if self._checkErr(ret):
                ret = self.session.post(
                    url, data=dictdata, json=json_data, timeout=10, **kwargs
                )
        except Exception as e:
            time.sleep(2)
            logging.debug("session过期,重新登录:%s", str(e))
            self._get_token()
            ret = self.session.post(
                url, data=dictdata, json=json_data, timeout=10, **kwargs
            )
            return ret
        return ret

    def _get_token(self):
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        data = {"app_id": self._appid, "app_secret": self._appsecret}
        res = self._post(url, json_data=data)
        self._token = json.loads(res.text)["tenant_access_token"]
        self.headers["Authorization"] = f"Bearer {self._token}"
        logging.debug("飞书token获取成功:%s", self._token)

    def _init_data(self):
        # self._get_token()
        self._get_group_list()

    def _get_group_list(self):
        url = "https://open.feishu.cn/open-apis/im/v1/chats"
        data = {"page_size": 20}
        res = self._get(url, params=data)
        logging.debug(res.text)
        res_json = json.loads(res.text)
        for item in res_json["data"]["items"]:
            groupitem = GroupInfo.parse_obj(item)
            self._group_list.append(groupitem)
        logging.debug("获取组数量:%s", len(self._group_list))

    def get_group_info_by_name(self, grouname) -> GroupInfo:
        for group_info in self._group_list:
            if group_info.name == grouname:
                return group_info
        logging.error("群组找不到:%s", grouname)

    def get_group_info_by_id(self, chat_id: str) -> GroupInfo:
        for group_info in self._group_list:
            if group_info.chat_id == chat_id:
                return group_info
        logging.error("群组找不到:%s", chat_id)

    def init_group_user_list(self, group_info: GroupInfo):
        page_size = 20
        page_token = ""
        group_info.members = []
        while True:
            url = f"https://open.feishu.cn/open-apis/im/v1/chats/{group_info.chat_id}/members"
            req_data = {"page_size": page_size, "page_token": page_token}
            res = self._get(url, params=req_data)
            res_json = json.loads(res.text)
            res_data = res_json["data"]
            page_token = res_data["page_token"]
            items = res_data["items"]
            for item in items:
                memberitem = GroupMember.parse_obj(item)
                group_info.members.append(memberitem)
            if not res_data["has_more"]:
                break
            # total=res_data["member_total"]
        logging.debug("获取成员数:{len(group_info.members)}")

    def get_group_user_byid(self, group_info: GroupInfo, userid: str) -> GroupMember:
        if len(group_info.members) == 0:
            self.init_group_user_list(group_info)
        for userinfo in group_info.members:
            if userinfo.member_id == userid:
                return userinfo
        logging.error("群组%s找不到:%s", group_info.name, userid)

    def get_group_user_info(self, group_info: GroupInfo, username: str) -> GroupMember:
        if len(group_info.members) == 0:
            self.init_group_user_list(group_info)
        for userinfo in group_info.members:
            if userinfo.name == username:
                return userinfo
        logging.error("群组%s找不到:%s", group_info.name, username)

    def send_msg(self, receive_type, userid, sendtext="", sendcard=None):
        url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={receive_type}"
        req_data = {"receive_id": userid, "uuid": str(uuid.uuid4())}
        # print(f'sendtext内容:{sendtext}')
        # print(f'sendcard内容:{sendcard}')
        if sendtext:
            if isinstance(sendtext, str):
                req_data["msg_type"] = "text"
                req_data["content"] = json.dumps({"text": sendtext})
            else:
                req_data["msg_type"] = "post"
                req_data["content"] = json.dumps(sendtext)
        elif sendcard:
            req_data["msg_type"] = "interactive"
            req_data["content"] = json.dumps(sendcard)  # {"card": sendcard}
        logging.debug(req_data)
        res = self._post(url, json_data=req_data)
        # print(res.text)
        res_json = json.loads(res.text)
        if res_json["code"] == 0:
            logging.info("receive_type:%s userid:%s 发送成功", receive_type, userid)
            return True
        raise RuntimeError(f"发送失败：{res.text}")

    def send_msg_to_user(self, userid: str, sendtext: str):
        return self.send_msg("open_id", userid, sendtext=sendtext)

    def send_msg_to_group(self, groupid: str, sendtext: str):
        return self.send_msg("chat_id", groupid, sendtext=sendtext)

    def send_card_to_user(self, userid: str, sendjson: str):
        return self.send_msg("open_id", userid, sendcard=sendjson)

    def send_card_to_group(self, groupid: str, sendjson: str):
        return self.send_msg("chat_id", groupid, sendcard=sendjson)

    def send_feishu_err(self, group_id, author_name, sendtext):
        groupinfo = self.get_group_info_by_id(group_id)
        userinfo = self.get_group_user_info(groupinfo, author_name)
        sendcard = CardMsgRoot()
        sendcard.config.wide_screen_mode = True
        sendcard.header.title.content = "报错"
        sendcard.header.template = "red"
        sendcard.header.title.tag = "plain_text"
        element = MsgCard_Element()
        element.tag = "markdown"
        element.content = sendtext
        sendcard.elements.append(element)
        if userinfo:
            userid = userinfo.member_id
            element.content += f'<at id="{userid}"></at>'
        self.send_card_to_group(group_id, json.loads(sendcard.json(exclude_none=True)))


class MsgCardHelper:
    @staticmethod
    def get_msgroot(text) -> CardMsgRoot:
        res = CardMsgRoot()
        res.header.template = "turquoise"
        res.header.title.tag = "plain_text"
        res.header.title.content = text
        return res

    @staticmethod
    def get_btn_action(btn_text: str, values: Dict) -> MsgCard_ElementAction:
        res = MsgCard_ElementAction()
        res.tag = "button"
        res.text = MsgCard_Text()
        res.text.content = btn_text
        res.text.tag = "plain_text"
        res.type = "primary"
        res.value = values
        return res

    @staticmethod
    def get_btn_action_element() -> MsgCard_Element:
        res = MsgCard_Element()
        res.tag = "action"
        res.actions = []
        return res

    @staticmethod
    def get_br() -> MsgCard_Element:
        br_item = MsgCard_Element()
        br_item.tag = "hr"
        return br_item

    @staticmethod
    def get_markdown_element(text: str) -> MsgCard_Element:
        res = MsgCard_Element()
        res.tag = "div"
        res.text = MsgCard_Text()
        res.text.content = text
        res.text.tag = "lark_md"
        return res

    @staticmethod
    def get_colum(text: str) -> MsgCardColumn:
        res = MsgCardColumn()
        content1 = MsgCardHelper.get_markdown_element(text)
        res.elements.append(content1)
        return res

    @staticmethod
    def get_colum_element(texts: List[str]) -> MsgCard_Element:
        res = MsgCard_Element()
        res.tag = "column_set"
        res.flex_mode = "stretch"
        res.background_style = "grey"
        res.columns = []
        for item in texts:
            res.columns.append(MsgCardHelper.get_colum(item))
        return res
