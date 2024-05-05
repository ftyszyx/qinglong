import json
import os

from tasks import CheckIn


def task_map():
    result = {}
    for cls in CheckIn.__subclasses__():
        check_name = cls.__name__.lower()
        if check_name:
            result[check_name] = (cls.name, cls)
    return result


task_map = task_map()

notice_map = {
    "DINGTALK_ACCESS_TOKEN": "",
    "DINGTALK_SECRET": "",
}


def env2list(key):
    try:
        value = json.loads(os.getenv(key, []).strip()) if os.getenv(key) else []
        if isinstance(value, list):
            value = value
        else:
            value = []
    except Exception as e:
        print(e)
        value = []
    return value


def env2str(key):
    try:
        value = os.getenv(key, "") if os.getenv(key) else ""
        if isinstance(value, str):
            value = value.strip()
        elif isinstance(value, bool):
            value = value
        else:
            value = None
    except Exception as e:
        print(e)
        value = None
    return value


def get_checkin_info(data):
    result = {}
    if isinstance(data, dict):
        for one in task_map.keys():
            result[one.lower()] = data.get(one, [])
    else:
        for one in task_map.keys():
            result[one.lower()] = env2list(one)
    return result


def get_notice_info(data):
    result = {}
    if isinstance(data, dict):
        for one in notice_map.keys():
            result[one.lower()] = data.get(one, None)
    else:
        for one in notice_map.keys():
            result[one.lower()] = env2str(one)
    return result