# -*- coding: utf-8 -*-
import contextlib
import json
import pathlib
import re
import typing
from itertools import chain

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

# 引入新的工具函数
from utils import current_date, logger, write_json_file, debug_print

url = "https://github.com/trending?since=daily"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

retries = Retry(
    total=3, backoff_factor=1, status_forcelist=[k for k in range(400, 600)]
)


@contextlib.contextmanager
def request_session():
    s = requests.session()
    try:
        s.headers.update(headers)
        s.mount("http://", HTTPAdapter(max_retries=retries))
        s.mount("https://", HTTPAdapter(max_retries=retries))
        yield s
    finally:
        s.close()


class WebSiteGitHub:
    @staticmethod
    def get_raw() -> str:
        ret = ""
        try:
            with request_session() as s:
                resp = s.get(url, timeout=30)
                ret = resp.text
        except Exception as _:
            logger.exception("get data failed")
            raise
        return ret

    @staticmethod
    def clean_raw(html_content: str) -> typing.List[typing.Dict[str, typing.Any]]:
        ret: typing.List[typing.Dict[str, typing.Any]] = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            articles = soup.find_all('article', class_='Box-row')
            
            for article in articles:
                try:
                    repo_link = article.find('h2').find('a')
                    if not repo_link: continue
                    
                    full_name = re.sub(r'\s+', ' ', repo_link.get_text().strip())
                    parts = [part.strip() for part in full_name.split('/')]
                    if len(parts) != 2: continue
                    
                    owner, repo_name = parts
                    repo_url = "https://github.com" + repo_link.get('href', '')
                    
                    desc_elem = article.find('p', class_=['col-9', 'color-fg-muted'])
                    description = desc_elem.get_text().strip() if desc_elem else ""
                    
                    lang_elem = article.find('span', {'itemprop': 'programmingLanguage'})
                    language = lang_elem.get_text().strip() if lang_elem else ""
                    
                    stars_link = article.find('a', href=lambda x: x and x.endswith('/stargazers'))
                    stars = stars_link.get_text().strip() if stars_link else "0"
                    
                    forks_link = article.find('a', href=lambda x: x and x.endswith('/forks'))
                    forks = forks_link.get_text().strip() if forks_link else "0"
                    
                    repo_info = {
                        "owner": owner,
                        "repo": repo_name,
                        "title": f"{owner}/{repo_name}",
                        "url": repo_url,
                        "description": description,
                        "language": language,
                        "stars": stars,
                        "forks": forks,
                    }
                    ret.append(repo_info)
                except Exception as e:
                    logger.warning(f"解析单个仓库信息失败: {str(e)}")
                    continue
        except Exception as e:
            logger.exception(f"解析 HTML 失败: {str(e)}")
            raise
        return ret

    @staticmethod
    def read_already_download(
        full_path: str,
    ) -> typing.List[typing.Dict[str, typing.Any]]:
        content: typing.List[typing.Dict[str, typing.Any]] = []
        if pathlib.Path(full_path).exists():
            with open(full_path, encoding='utf-8') as fd:
                content = json.loads(fd.read())
        return content

    @staticmethod
    def merge_data(
        cur: typing.List[typing.Dict[str, typing.Any]],
        another: typing.List[typing.Dict[str, typing.Any]],
    ):
        merged_dict: typing.Dict[str, typing.Dict[str, typing.Any]] = {}
        for item in chain(cur, another):
            # 使用 URL 作为 key 来去重
            merged_dict[item["url"]] = item
        return list(merged_dict.values())

    def run(self):
        dir_name = "github"
        debug_print(f"开始抓取 {dir_name}", "GITHUB")
        
        try:
            raw_html = self.get_raw()
            cleaned_data = self.clean_raw(raw_html)

            if not cleaned_data:
                debug_print("没有抓取到新数据", "GITHUB")
                return {"success": False}

            cur_date = current_date()
            raw_path = f"./raw/{dir_name}/{cur_date}.json"

            already_download_data = self.read_already_download(raw_path)
            merged_data = self.merge_data(cleaned_data, already_download_data)

            write_json_file(raw_path, merged_data)
            debug_print(f"数据已写入到 {raw_path}", "GITHUB")
            
            return {
                "success": True,
                "data_count": len(merged_data)
            }
        except Exception as e:
            logger.exception(f"执行 GitHub 任务失败: {e}")
            return {"success": False}


if __name__ == "__main__":
    github_obj = WebSiteGitHub()
    result = github_obj.run()
    if result["success"]:
        print(f"GitHub Trending 抓取成功，共 {result['data_count']} 条数据。")
