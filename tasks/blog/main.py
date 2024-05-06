import requests
from tasks import TaskBase
import shutil
import os
from tasks.utils.FileTool import unzip_dir 

class BLog(TaskBase):
    name = '博客更新'
    def __init__(self,check_item:dict):
        self._session = requests.session()
        self._check_item = check_item
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
        ower=self._check_item.get('github_ower')
        repo=self._check_item.get('github_repo')
        token=self._check_item.get('github_token')
        url=f'https://api.github.com/repos/{ower}/{repo}/releases/latest'
        print(f'get owner:{ower} repo:{repo} token:{token} ')
        self._session.headers.update({
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": f"Bearer {token}"})  
        response = self._session.get(url)
        # print(f'get res:{response.text}')
        json_data=response.json()
        download_url=json_data.get('assets')[0].get('browser_download_url')
        print("get download_url:",download_url)
        downlaod_path=os.path.join(os.path.abspath(os.curdir),"blog_dist")
        if os.path.exists(downlaod_path):
            shutil.rmtree(downlaod_path,ignore_errors=True)
        os.makedirs(downlaod_path)
        file_path=os.path.join(downlaod_path,'blog.zip')
        file_res=self._session.get(download_url)
        with open(file_path,'wb') as f:
            f.write(file_res.content)
        unzip_dir(file_path,os.path.join(downlaod_path,'blog'),showlog=False)
        return f'download blog success,save path:{file_path} url:{download_url}'