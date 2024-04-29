# 此类使用方法：
# from bugly_sdk.bugly import BuglyHelper
# helper = BuglyHelper(qq) #会自动登录bugly并获取bugly基础信息

import json, os, random
import logging
from requests import Response
from requests_html import HTMLSession
from datetime import datetime 
from splinter.browser import Browser
from splinter.element_list import ElementList
import time
from typing import List, Callable
from .bugly_defs import BuglyAppInfo,IssueInfo,CrashInfo,CrashMap,CrashDetailMap,CrashHourInfo


def get_fsn():
    s = [random.randint(0, 255) for _ in range(0, 16)]
    s[6] = 15 & s[6] | 64
    s[8] = 63 & s[8] | 128
    for i in range(len(s)):
        s[i] = "{0:#0{1}x}".format(s[i], 4)[2:4]
    fsn = s[0] + s[1] + s[2] + s[3] + '-' + s[4] + s[5] + '-' + s[6] + s[7] + '-' + s[8] + s[9] + '-' + s[10] + s[11] + \
          s[12] + s[13] + s[14] + s[15]
    return fsn


class BuglyHelper:
    _curpath: str
    _app_list: List[BuglyAppInfo] = []
    _userId = ""
    _qq: int = 0

    def __init__(self, qq: int):
        self._qq = qq
        self._curpath = os.path.abspath(os.curdir)
        self.session = HTMLSession()
        self.session.verify = False  # fiddle抓包
        self.headers = {
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://xui.ptlogin2.qq.com/',
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Content-Type": "application/json;charset=utf-8",
            "Accept": "application/json;charset=utf-8",
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47'
        }
        self._init_cookies()
        self._init_bugly()

    # 获取bugly基础信息
    def _init_bugly(self):
        print("获取bugly基础信息")
        try:
            self._get_user_info()
            self._get_app_list()
        except Exception as e:
            print(f'session过期：重新登录:{str(e)}')
            self.relogin()
            self._init_bugly()

    # 初始化cooike
    def _init_cookies(self):
        cookies_path = os.path.join(self._curpath, "cookie.txt")
        if os.path.exists(cookies_path) == False:
            print('cookies不存在')
            self.relogin()
            return
        with open(os.path.join(self._curpath, "cookie.txt"), 'r', encoding='UTF-8') as fb:
            lines = fb.readlines()
            for item in lines:
                itemarr = item.split('=')
                key = itemarr[0]
                value = itemarr[1]
                value = value.replace('\n', '')
                self.session.cookies[key] = value

    # 保存cookie
    def _dump_cookies(self, cookies: dict):
        with open(os.path.join(self._curpath, "cookie.txt"), 'w', encoding='UTF-8') as fb:
            cooikes_text = ""
            for k, v in cookies.items():
                cooikes_text += f'{k}={v}\n'
            fb.seek(0)
            fb.write(cooikes_text)
            fb.truncate()

    # get请求
    def _get(self, url: str, **kwargs) -> Response:
        kwargs.setdefault('headers', self.headers)
        res = self.session.get(url, timeout=10, **kwargs)
        return res

    # post请求
    def _post(self, url: str, dictdata=None, jsondata=None, **kwargs) -> Response:
        kwargs.setdefault('headers', self.headers)
        ret = self.session.post(url, data=dictdata, json=jsondata, timeout=10, **kwargs)
        return ret

    # 登录bugly流程
    def _dologin(self, browser):
        browser.visit("https://bugly.qq.com/v2/workbench/apps")
        time.sleep(5)
        with browser.get_iframe('ptlogin_iframe') as iframe:
            if not iframe.is_element_present_by_id('qlogin_list', wait_time=5):
                return f'网络异常'
            loginlist: ElementList = iframe.find_by_css('.qlogin_list')
            print("find loginlist ok")
            loginimg = loginlist.first.find_by_css(f'#img_{self._qq}')
            if loginimg is None:
                return f'请先在电脑上登录qq:{self._qq}'
            loginimg.first.parent.click()
            print(f'快速登录中:{self._qq}')
            time.sleep(1)
        print(f'等待跳转bugly') 
        print(f'等待10s')
        time.sleep(10)
        cookies = browser.cookies.all()
        print(f'get cookies:{cookies}')
        self._dump_cookies(cookies)
        self._init_cookies()
        print(f'登录成功')
        return None

    # 登录bugly流程
    def relogin(self):
        print("重新登录bugly")
        browser = Browser('chrome')
        try:
            errtext = self._dologin(browser)
        except Exception as e:
            errtext=f'dologin err:{str(e)}'
            browser.quit()
            raise Exception(f'{errtext}')
        if errtext:
            browser.quit()
            raise Exception(f'{errtext}')
        else:
            browser.quit()

    # 获取问题类型列表
    def get_issue_list(self, app_id: str, platform_id: int, vername: str, start_date: str, end_data: str, max_num: int = 0) -> List[IssueInfo]:
        print(f'get issue list')
        start = 0
        issuelist = []
        page_num = 10
        url = "https://bugly.qq.com/v4/api/old/get-issue-list"
        get_param = {
            "fsn": get_fsn(),
            "pid": platform_id,
            "platformId": platform_id,
            "sortField": "uploadTime",
            "sortOrder": "dec",
            "exceptionTypeList": "Crash,Native",
            "searchType": "errorType",
            "appId": app_id,
            "date": "custom",
            "rows": page_num,
            "startDateStr": start_date,
            "endDateStr": end_data
        }

        if vername:
            get_param["version"] = vername
        breakwhile = False
        while True:
            get_param["start"] = start
            res = self._get(url, params=get_param)
            res_json = json.loads(res.text)
            res_data = res_json["data"]
            totalnum = res_data["numFound"]

            if max_num <= 0:
                max_num = totalnum
            print(f'\r获取issue进度:{len(issuelist)}/{max_num}', end="")
            for item in res_data["issueList"]:
                issue_item = IssueInfo.parse_obj(item)
                issue_item.appId = app_id
                issuelist.append(issue_item)
                if len(issuelist) >= max_num:
                    print(f'获取到了{len(issuelist)} 超过max:{max_num},退出')
                    breakwhile = True
                    break
            if len(issuelist) >= totalnum:
                print(f'获取到了{len(issuelist)},退出')
                break
            if breakwhile:
                break
            start += page_num
        return issuelist

    # 数据该闪退类型的所有崩溃
    def get_issue_detail(self,
                         appid: str,
                         platform_id: int,
                         issue_item: IssueInfo,
                         start_date: str,
                         end_date: str,
                         max_num: int = 0,
                         need_get_func: Callable[[str, str, str, datetime], bool] = None) -> List[CrashInfo]:
        url = f'https://bugly.qq.com/v2/crash-reporting/crashes/{appid}/{issue_item.issueId}'
        get_param = {"fsn": get_fsn(), "pid": platform_id}
        res = self._get(url, params=get_param)
        start = 0
        crash_list: List[CrashInfo] = []
        page_num = 10
        print(f'get issue:{issue_item.issueId} 所有闪退列表')
        getnum = 0
        break_while = False
        while True:
            url2 = f'https://bugly.qq.com/v4/api/old/get-crash-list'
            get_param2 = {
                "fsn": get_fsn(),
                "pid": platform_id,
                "searchType": "detail",
                "exceptionTypeList": "Crash,Native,ExtensionCrash",
                "rows": page_num,
                "appId": appid,
                "platformId": platform_id,
                "issueId": issue_item.issueId
            }
            if start > 0:
                get_param2["start"] = start
            res = self._get(url2, params=get_param2)
            crashlist_resp = json.loads(res.text)
            crashlist_resp_data = crashlist_resp["data"]
            totalnum = crashlist_resp_data["numFound"]
            if max_num <= 0:
                max_num = totalnum
            for _, v in crashlist_resp_data["crashDatas"].items():
                crash_item_info = CrashInfo.parse_obj(v)
                mintime = datetime.strptime(start_date + "-00:00:01", "%Y%m%d-%H:%M:%S")
                maxtime = datetime.strptime(end_date + "-23:59:59", "%Y%m%d-%H:%M:%S")
                uploadtime = datetime.strptime(crash_item_info.uploadTime, "%Y-%m-%d %H:%M:%S %f")

                getnum += 1
                if uploadtime >= mintime and uploadtime <= maxtime:
                    if need_get_func:
                        if need_get_func(appid, issue_item.issueId, crash_item_info.id, uploadtime) is False:
                            continue
                    crash_list.append(crash_item_info)
                    if len(crash_list) >= max_num:
                        break_while = True
                        print(f'问题组:{issue_item.issueId}获取到了{len(crash_list)}个闪退,总共有:{totalnum}个 超过max:{max_num},退出')
                        break
            if break_while:
                break
            if getnum >= totalnum:
                print(f'问题组:{issue_item.issueId}获取到了{len(crash_list)}个闪退,总共有:{totalnum}个,退出')
                break
            start += page_num

        print(f'获取闪退详情:{issue_item.issueId} 闪退数量:{len(crash_list)}')
        # err_num = 0
        getnum = 0
        for crashitem in crash_list:
            crashitem.issueId = issue_item.issueId
            crashitem.appId = appid
            getnum += 1
            print(f'\r问题组:{issue_item.issueId} 获取闪退详情:{crashitem.id} uploadetime:{crashitem.uploadTime} 进度:{getnum}/{len(crash_list)}', end="")
            if not self.getCrashDetail(crashitem, appid, platform_id, issue_item.issueId, crashitem.id, crashitem.crashId):
                continue
        return crash_list

    def getCrashDetail(self, crashitem: CrashInfo, appid: str, pid: int, issuid: str, crash_hash: str, crashId: int) -> (bool):
        max_retrynum = 3
        retrynum = 0
        while (True):
            url3 = f'https://bugly.qq.com/v4/api/old/get-crash-detail'
            get_param3 = {"fsn": get_fsn(), "pid": pid, "appId": appid, "crashHash": crash_hash}
            res3 = self._get(url3, params=get_param3)
            res3_json = json.loads(res3.text)
            guid = crash_hash.replace(":", "-")
            crashitem.url = f'https://bugly.qq.com/v2/crash-reporting/crashes/{appid}/{issuid}/report?pid={pid}&guid={guid}&crashId={crashId}'
            if "detailMap" not in res3_json["data"]:
                errtext = f'闪退信息detailMap获取失败 issue:{issuid} crashid:{crashId} crashHash:{crash_hash} url:{crashitem.url}'
                logging.info(errtext)
                return True
                # raise Exception(f'{errtext}')
            crashitem.crashMap = CrashMap.parse_obj(res3_json["data"]["crashMap"])
            crashitem.detailMap =CrashDetailMap.parse_obj(res3_json["data"]["detailMap"])
            if len(crashitem.detailMap.fileList) == 0:
                errtext = f'闪退信息detailMap获取失败 fillist为空 重试次数:{retrynum} issue:{issuid} crashid:{crashId} crashHash:{crash_hash} url:{crashitem.url}'
                print(errtext)
                if retrynum > max_retrynum:
                    logging.info(f'不再重试 crashHash:{crash_hash}')
                    return True
                retrynum += 1
                print("等待10s")
                time.sleep(10)
            else:
                if retrynum > 0:
                    print(f'闪退信息detailMap获取成功 重试次数:{retrynum} issue:{issuid} crashid:{crashId} crashHash:{crash_hash} url:{crashitem.url}')
                return True

    # 获取bugly的用户信息
    def _get_user_info(self):
        get_param = {"fsn": get_fsn()}
        url = f'https://bugly.qq.com/v4/api/old/info'
        res = self._get(url, params=get_param)
        res_json = json.loads(res.text)
        print(f'获取用户信息成功:{res_json}')
        self._userId = res_json["data"]["userId"]

    # 获取bugly应用列表
    def _get_app_list(self):
        get_param = {"fsn": get_fsn(), "userId": self._userId}
        url = f'https://bugly.qq.com/v4/api/old/app-list'
        res = self._get(url, params=get_param)
        res_json = json.loads(res.text)
        self._app_list.clear()
        applist_str = ""
        for item in res_json["data"]:
            appinfo = BuglyAppInfo.parse_obj(item)
            applist_str += f'{appinfo.appName}-{appinfo.appId}\n'
            self._app_list.append(appinfo)
        print(f'获取用app列表成功:\n{applist_str}')

    # 获取首页崩溃汇总信息
    def get_crash_info(self, appinfo: BuglyAppInfo, start_hour: str, end_hour: str) -> List[CrashHourInfo]:
        url = "https://bugly.qq.com/v4/api/old/get-real-time-hourly-stat"
        get_req = {"appId": appinfo.appId, "pid": appinfo.pid, "type": "crash", "dataType": "realTimeTrendData", "version": -1, "startHour": start_hour, "endHour": end_hour, "fsn": get_fsn()}
        res = self._get(url, params=get_req)
        # print(res.text)
        res_json = json.loads(res.text)
        res_data = res_json["data"]["data"]
        ret: List[CrashHourInfo] = []
        for item in res_data:
            iteminfo = CrashHourInfo.parse_obj(item)
            if iteminfo.accessUser > 0:
                iteminfo.crash_user_rate = iteminfo.crashUser / iteminfo.accessUser
            if iteminfo.accessNum > 0:
                iteminfo.crash_num_rate = iteminfo.crashNum / iteminfo.accessNum
            infotime = datetime.strptime(iteminfo.date, '%Y%m%d%H')
            iteminfo.hour = infotime.hour
            ret.append(iteminfo)
        return ret

    def get_appinfo_by_id(self, appid: str) -> BuglyAppInfo:
        for appinfo in self._app_list:
            if appinfo.appId == appid:
                return appinfo

    def get_appinfo_by_name(self, appname: str) -> BuglyAppInfo:
        for appinfo in self._app_list:
            if appinfo.appName == appname:
                return appinfo

    @property
    def applist(self):
        return self._app_list
