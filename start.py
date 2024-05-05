import argparse
import json
import os
from datetime import datetime, timedelta

from tasks.configs import task_map, get_checkin_info, get_notice_info
from tasks.utils.message import push_message


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--include", nargs="+", help="任务执行包含的任务列表")
    parser.add_argument("--exclude", nargs="+", help="任务执行排除的任务列表")
    return parser.parse_args()


def check_config(task_list):
    config_path = None
    config_path_list = []
    for one_path in [ "/ql/scripts/config.json", "config.json" ]:
        _config_path = os.path.join(os.getcwd(), one_path)
        config_path_list.append(os.path.normpath(os.path.dirname(_config_path)))
        if os.path.exists(_config_path):
            config_path = os.path.normpath(_config_path)
            break
    if config_path:
        print("使用配置文件路径:", config_path)
        with open(config_path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print("Json 格式错误，请检查 config.json 文件格式是否正确！")
                return False, False
        try:
            notice_info = get_notice_info(data=data)
            _check_info = get_checkin_info(data=data)
            check_info = {}
            for one_check, _ in task_map.items():
                if one_check in task_list:
                    if _check_info.get(one_check.lower()):
                        for _, check_item in enumerate( _check_info.get(one_check.lower(), []) ):
                            if one_check.lower() not in check_info.keys():
                                check_info[one_check.lower()] = []
                            check_info[one_check.lower()].append(check_item)
            return notice_info, check_info
        except Exception as e:
            print(f"配置文件错误: {e}")
            return False, False
    else:
        print(
            "未找到 config.json 配置文件\n请在下方任意目录中添加「config.json」文件:\n"
            + "\n".join(config_path_list)
        )
        return False, False


def checkin():
    print(f"当前时间: {datetime.now()}\n")
    args = parse_arguments()
    include = args.include
    exclude = args.exclude
    if not include:
        include = list(task_map.keys())
    else:
        include = [one for one in include if one in task_map.keys()]
    if not exclude:
        exclude = []
    else:
        exclude = [one for one in exclude if one in task_map.keys()]
    task_list = list(set(include) - set(exclude))
    notice_info, check_info = check_config(task_list)
    if check_info:
        task_name_str = "\n".join(
            [
                f"「{task_map.get(one.upper())[0]}」账号数 : {len(value)}"
                for one, value in check_info.items()
            ]
        )
        print(f"\n---------- 本次执行签到任务如下 ----------\n\n{task_name_str}\n\n")
        content_list = []
        for one_check, check_list in check_info.items():
            check_name, check_func = task_map.get(one_check.upper())
            print(f"----------开始执行「{check_name}」签到----------")
            for index, check_item in enumerate(check_list):
                try:
                    msg = check_func(check_item).main()
                    content_list.append(f"「{check_name}」\n{msg}")
                    print(f"第 {index + 1} 个账号: ✅✅✅✅✅")
                except Exception as e:
                    content_list.append(f"「{check_name}」\n{e}")
                    print(f"第 {index + 1} 个账号: ❌❌❌❌❌\n{e}")
        print("\n\n")
        push_message(content_list=content_list, notice_info=notice_info)
        return


if __name__ == "__main__":
    checkin()
