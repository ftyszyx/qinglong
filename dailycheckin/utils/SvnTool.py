import os
from typing import List
import re
from urllib.parse import urljoin
from .OtherTool import get_cmd_output
from pydantic import BaseModel
from xml.etree import ElementTree
from datetime import datetime
import logging

def check_out(svn_path,dest_path,username=None,passwd=None,log=False):
    if os.path.exists(dest_path) == True:
        raise Exception("path is exit", dest_path)
    auth = _get_auth(username, passwd)
    cmd = f"svn co {auth} {svn_path} {dest_path} "
    print(f'{cmd}')
    ret = os.system(cmd)
    if ret != 0:
        raise Exception("check out Error!:" + svn_path)


# 更新
def update_svn(path, username=None, passwd=None, log=False):
    if os.path.exists(path) == False:
        raise Exception("path not exit", path)
    print("update ", path)
    auth = _get_auth(username, passwd)
    cmd = f"svn update {auth} {path} --non-interactive --accept theirs-full "
    ret = os.system(cmd)
    if ret != 0:
        raise Exception("update Error!:" + path)
    if log:
        print("resolve confilict ", path)
    cmd = f"svn resolve {auth} {path} --depth infinity --accept theirs-full  --non-interactive "
    ret = os.system(cmd)
    if ret != 0:
        raise Exception("reslove Error!:" + path)


def revert_svn(path, username=None, passwd=None, log=False):
    if os.path.exists(path) == False:
        raise Exception("path not exit", path)
    auth = _get_auth(username, passwd)
    command = f"""svn revert {auth} -R {path} """
    ret = os.system(command)
    if log:
        print(command)
    if ret != 0:
        raise Exception("revert Error!:" + path)
    if log:
        print("revert ok!")


def commit_svn(path, comment="auto commit", username=None, passwd=None, log=False):
    if os.path.exists(path) == False:
        raise Exception("path not exit", path)
    auth = _get_auth(username, passwd)
    command = f"""svn ci {auth} {path} -m "{comment}" -q """
    ret = os.system(command)
    if log:
        print(command)
    if ret != 0:
        raise Exception("commit Error!:" + path)
    if log:
        print("commit ok!")


def reslove_conflict(path, username=None, passwd=None, log=False):
    if os.path.exists(path) == False:
        raise Exception("path not exit", path)
    auth = _get_auth(username, passwd)
    cmd = f"svn status {auth} {path}"
    text = get_cmd_output(cmd)
    for linetext in text.splitlines():
        wordlist = re.split(r"\s+", linetext)
        print(wordlist)
        if len(wordlist) >= 2 and wordlist[0] == "C":
            filepath = os.path.join(path, wordlist[1])
            cmd = "svn resolve " + filepath + "--accept theirs-full  --non-interactive "
            ret = os.system(cmd)
            if ret != 0:
                raise Exception(f"reslove confilict err:{path}")
            if log:
                print(f"resolve confilict ok {path} ")


def add_svn(path, username=None, passwd=None, log=False):
    if os.path.exists(path) == False:
        raise Exception("path not exit", path)
    auth = _get_auth(username, passwd)
    command = f"""svn add {auth} {path} --force """
    ret = os.system(command)
    print(command)
    if ret != 0:
        raise Exception("add force Error!:" + path)
    else:
        print("add ok!")


def get_svn_externals(url, username=None, passwd=None, log=False) -> List[str]:
    res: List[str] = []
    auth = _get_auth(username, passwd)
    cmd = f"svn {auth} propget svn:externals -R {url} "
    if log:
        logging.info(f"get_svn_externals cmd:{cmd}")
    lines = get_cmd_output(cmd).splitlines()
    prefix = ""
    for line in lines:
        if len(line) == 0:
            continue
        idx = line.find(" - ")
        if idx > 0:
            prefix = line[0:idx].strip()
            if prefix.endswith("/") is False:
                prefix += "/"
            line = line[idx + 3 :].strip()
        info_arr = line.split(" ")
        path2_url = info_arr[0].strip()
        if path2_url.startswith("^"):
            head_str = path2_url.split("/")[1]
            head_idx = prefix.find(f"/{head_str}/")
            new_prefix = prefix[0 : head_idx + 1]
            path2_url = urljoin(new_prefix, path2_url[2:])
            # print(f"newpre:{new_prefix} headstr:{head_str} url:{path2_url}")
        elif path2_url.startswith("svn:") is False:
            path2_url = urljoin(prefix, path2_url)
        # print(f"res:{path2_url} url:{info_arr[0].strip()} pre:{prefix}")
        res.append(path2_url)
    return res


class SvnLogInfo(BaseModel):
    author: str = ""
    date: datetime = None
    msg: str = ""
    revision: str = ""


def get_svn_log(
    url: str,
    start_date: str,
    end_date: str,
    search=None,
    username=None,
    passwd=None,
    log=False,
) -> List[SvnLogInfo]:
    res: List[SvnLogInfo] = []
    auth = _get_auth(username, passwd)
    search_txt = ""
    if search:
        search_txt = f" --search {search}"
    date_str = "-r " + "{" + start_date + "}" + ":" + "{" + end_date + "}"
    cmd = f"svn {auth} log --xml {search_txt} {date_str} {url}"
    if log:
        logging.info(f"get_svn_log cmd:{cmd}")
    output = get_cmd_output(cmd)
    if len(output.strip()) <= 0:
        return res
    root = ElementTree.fromstring(output)
    for elem in root.findall("logentry"):
        info = SvnLogInfo()
        info.msg = elem.find("msg").text
        info.date = datetime.strptime(elem.find("date").text, "%Y-%m-%dT%H:%M:%S.%fZ")
        info.author = elem.find("author").text
        info.revision = elem.get("revision")
        res.append(info)
    return res


def _get_auth(username=None, password=None):
    auth = ""
    if username and password:
        auth = f"--username {username} --password {password}"
    return auth


def get_svn_ls(url, username=None, password=None, log=False) -> List[str]:
    res: List[str] = []
    auth = _get_auth(username, password)
    cmd = f"svn {auth} ls {url}"
    if log:
        logging.info(f"get svnls cmd:{cmd}")
    output = get_cmd_output(cmd)
    output = output.strip()
    if len(output) == 0:
        return res
    res = output.splitlines()
    return res
