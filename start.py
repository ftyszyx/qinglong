import argparse
import json
import os
from datetime import datetime
from tasks import TaskBase
from tasks.utils.message import push_message
import traceback


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--include", nargs="+", help="任务执行包含的任务列表")
    parser.add_argument("--exclude", nargs="+", help="任务执行排除的任务列表")
    return parser.parse_args()

def run_task(task_list):
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
        config_dic={}
        with open(config_path, encoding="utf-8") as f:
            try:
                config_dic= json.load(f)
            except json.JSONDecodeError:
                print("Json 格式错误，请检查 config.json 文件格式是否正确！")
                return False, False
        try:
            msg_list=[]
            print(f'config dic:{json.dumps(config_dic,indent=4)}')
            for cls in TaskBase.__subclasses__():
                check_name = cls.__name__.lower()
                print(f'check task {check_name}')
                if config_dic.get(check_name) and check_name in task_list:
                    one_task_config= config_dic.get(check_name)
                    print(f'run {cls.name}')
                    try:
                        msg=cls(one_task_config).main()
                        msg_list.append(msg)
                        print(f"run {cls.name} success\n return: {msg}\n")
                    except Exception :
                        print(f"run {cls.name} error: {traceback.format_exc()}\n")
            push_message(content_list=msg_list,config_dic=config_dic)
        except Exception:
            print(f"运行异常: {traceback.format_exc()}")
            return False, False
    else:
        print(
            "未找到 config.json 配置文件\n请在下方任意目录中添加「config.json」文件:\n"
            + "\n".join(config_path_list)
        )
        return False, False


def start():
    print(f"当前时间: {datetime.now()}\n")
    args = parse_arguments()
    include = args.include or []
    exclude = args.exclude or []
    task_list = list(set(include) - set(exclude))
    run_task(task_list)

if __name__ == "__main__":
    try:
        start()
    except Exception:
        print(f"运行异常: {traceback.format_exc()}")
