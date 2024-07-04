import requests
from tasks import TaskBase
import shutil
import os
from tasks.utils.FileTool import unzip_dir


class BLog(TaskBase):
    name = "博客更新"

    def __init__(self, check_item: dict):
        self._session = requests.session()
        self._check_item = check_item
        self._session.headers.update(
            {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.64",
                "Referer": "https://docs.github.com/",
                "Accept": "application/vnd.github+json",
                "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                "Connection": "keep-alive",
            }
        )

    def main(self):
        ower = self._check_item.get("github_ower")
        repo = self._check_item.get("github_repo")
        token = self._check_item.get("github_token")
        dest_path = self._check_item.get("dest_path")
        url = f"https://api.github.com/repos/{ower}/{repo}/releases/latest"
        print(f"get owner:{ower} repo:{repo} token:{token} ")
        self._session.headers.update(
            {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "Authorization": f"Bearer {token}"}
        )
        response = self._session.get(url)
        # print(f'get res:{response.text}')
        json_data = response.json()
        download_url = json_data.get("assets")[0].get("browser_download_url")
        download_url = "https://mirror.ghproxy.com/" + download_url
        release_name = json_data.get("name")
        if dest_path is None or dest_path.strip() == "":
            dest_path = os.path.join(os.path.abspath(os.curdir), "blog_dist")
        if os.path.exists(dest_path) is False:
            os.makedirs(dest_path)
        print(f"get release_name:{release_name} download_url:{download_url} dest_path:{dest_path}")
        local_file_path = os.path.join(dest_path, f"{release_name}.zip")
        if os.path.exists(local_file_path):
            print("no new blog release")
            return
        if os.path.exists(dest_path) is False:
            os.makedirs(dest_path)

        file_res = self._session.get(download_url)
        with open(local_file_path, "wb") as f:
            f.write(file_res.content)
        blog_tmp_path = os.path.join(dest_path, "web_tmp")
        if os.path.exists(blog_tmp_path):
            shutil.rmtree(blog_tmp_path, ignore_errors=True)
        unzip_dir(local_file_path, blog_tmp_path, showlog=False)
        blog_path = os.path.join(dest_path, "web")
        if os.path.exists(blog_path):
            shutil.rmtree(blog_path, ignore_errors=True)
        shutil.move(os.path.join(blog_tmp_path, "blog/docs/.vitepress/dist"), blog_path)
        return f"download blog success,save path:{local_file_path}\n url:{download_url}"
