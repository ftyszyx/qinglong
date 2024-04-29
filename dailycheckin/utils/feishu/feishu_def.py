from typing import List, Any, Dict
from pydantic import BaseModel


class GroupMember(BaseModel):
    member_id: str = ""
    member_id_type: str = ""
    name: str = ""
    tenant_key: str = ""


class GroupInfo(BaseModel):
    avatar: str = ""
    chat_id: str = ""
    description: str = ""
    external: bool = False
    name: str = ""
    owner_id: str = ""
    owner_id_type: str = ""
    tenant_key: str = ""
    members: List[GroupMember] = []


class MsgCard_Text(BaseModel):
    content: str = ""
    tag: str = ""


class MsgCard_Config(BaseModel):
    wide_screen_mode: bool = True


class MsgCard_Extra(BaseModel):
    tag: str = ""
    text: MsgCard_Text = None
    type: str = ""
    url: str = ""


class MsgCard_ElementAction(BaseModel):
    tag: str = ""
    url: str = ""
    type: str = ""
    text: MsgCard_Text = None
    value: Dict[str, Any] = None


class MsgCardColumn(BaseModel):
    tag: str = "column"
    width: str = "auto"
    weight: int = None
    vertical_align: str = None
    elements = []


class MsgCard_Element(BaseModel):
    extra: MsgCard_Extra = None
    tag: str = ""
    content: str = None
    text: MsgCard_Text = None
    flex_mode: str = None
    background_style: str = None
    columns: List[MsgCardColumn] = None
    actions: List[MsgCard_ElementAction] = None


class MsgCard_Title(BaseModel):
    content: str = ""
    tag: str = ""


class MsgCard_Header(BaseModel):
    template: str = ""
    title: MsgCard_Title = MsgCard_Title()
