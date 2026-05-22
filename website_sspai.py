# -*- coding: utf-8 -*-
import contextlib
import json
import pathlib
import typing
from itertools import chain

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils import current_date, debug_print, logger, write_json_file

url = "https://sspai.com/api/v1/article/tag/page/get?limit=50&tag=热门文章"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
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


class WebSiteSSPai:
    @staticmethod
    def get_raw() -> dict:
        ret = {}
        try:
            with request_session() as s:
                resp = s.get(url, timeout=30)
                ret = resp.json()
        except:
            logger.exception("get data failed")
            raise
        return ret

    @staticmethod
    def clean_raw(raw_data: dict) -> typing.List[typing.Dict[str, typing.Any]]:
        ret: typing.List[typing.Dict[str, typing.Any]] = []
        for item in raw_data.get("data", []):
            ret.append(
                {
                    "title": item["title"],
                    "url": f"https://sspai.com/post/{item['id']}",
                }
            )
        return ret

    @staticmethod
    def read_already_download(
        full_path: str,
    ) -> typing.List[typing.Dict[str, typing.Any]]:
        content: typing.List[typing.Dict[str, typing.Any]] = []
        if pathlib.Path(full_path).exists():
            with open(full_path) as fd:
                content = json.loads(fd.read())
        return content



    @staticmethod
    def merge_data(
        cur: typing.List[typing.Dict[str, typing.Any]],
        another: typing.List[typing.Dict[str, typing.Any]],
    ):
        merged_dict: typing.Dict[str, typing.Any] = {}
        for item in chain(cur, another):
            merged_dict[item["url"]] = item["title"]

        return [{"url": k, "title": v} for k, v in merged_dict.items()]



    def run(self):
        dir_name = "sspai"
        debug_print(f"开始抓取 {dir_name}", "SSPAI")

        raw_data = self.get_raw()
        cleaned_data = self.clean_raw(raw_data)
        
        # 如果抓取失败或没有新数据，提前返回
        if not cleaned_data:
            debug_print("没有抓取到新数据", "SSPAI")
            return { "success": False }

        cur_date = current_date()
        raw_path = f"./raw/{dir_name}/{cur_date}.json"

        # 读取当天已有的数据进行合并
        already_download_data = self.read_already_download(raw_path)
        merged_data = self.merge_data(cleaned_data, already_download_data)

        # 只写入纯净的 JSON 文件
        write_json_file(raw_path, merged_data)
        debug_print(f"数据已写入到 {raw_path}", "SSPAI")

        # 返回成功状态和数据，供 main.py 判断
        return {
            "success": True,
            "data_count": len(merged_data)
        }


if __name__ == "__main__":
    sspai_obj = WebSiteSSPai()
    result = sspai_obj.run()
    if result["success"]:
        print(f"SSPai 热榜抓取成功，共 {result['data_count']} 条数据。")
