
import requests

class BLog(CheckIn):
    name = '博客更新'

    def __init__(self,check_item:dict):
        self._session = requests.session()
        self._session.headers.update(
            {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.64",
                "Referer": "https://docs.github.com/",
                "Accept":"application/vnd.github+json",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "Connection": "keep-alive",
            }
        )


    def main(self):
        self._session.