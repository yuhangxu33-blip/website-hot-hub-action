# -*- coding: utf-8 -*-
"""
微信读书热榜爬虫
抓取微信读书「飙升榜」（畅销热榜）
接口说明：
  rankType=2  全品类
  gender=1    不限性别
  maxIndex=0  第一页
若需要登录态，可将微信读书的 Cookie 存入 GitHub Secret: WEREAD_COOKIE
"""
import contextlib
import json
import os
import pathlib
import typing
from itertools import chain

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils import current_date, get_weread_id, logger, write_json_file, debug_print

RANK_URL = "https://weread.qq.com/api/rank/newRatingList?rankType=2&gender=1&maxIndex=0"

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    ),
    "Referer": "https://weread.qq.com/",
    "Origin": "https://weread.qq.com",
}

retries = Retry(
    total=3, backoff_factor=1, status_forcelist=[k for k in range(400, 600)]
)


@contextlib.contextmanager
def request_session():
    s = requests.session()
    try:
        headers = dict(BASE_HEADERS)
        # 如果配置了 Cookie（GitHub Secret: WEREAD_COOKIE），自动带上
        cookie = os.environ.get("WEREAD_COOKIE", "")
        if cookie:
            headers["Cookie"] = cookie
        s.headers.update(headers)
        s.mount("http://", HTTPAdapter(max_retries=retries))
        s.mount("https://", HTTPAdapter(max_retries=retries))
        yield s
    finally:
        s.close()


class WebSiteWeRead:
    @staticmethod
    def get_raw() -> dict:
        ret = {}
        try:
            with request_session() as s:
                resp = s.get(RANK_URL, timeout=30)
                resp.raise_for_status()
                ret = resp.json()
        except Exception:
            logger.exception("WeRead: get data failed")
            raise
        return ret

    @staticmethod
    def clean_raw(raw_data: dict) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        WeRead API 返回结构示例：
        {
          "books": [
            {
              "bookId": "12345678",      # 纯数字字符串
              "title": "书名",
              "author": "作者名",
              ...
            }
          ]
        }
        """
        ret: typing.List[typing.Dict[str, typing.Any]] = []
        books = raw_data.get("books", [])
        for item in books:
            book_id = str(item.get("bookId", ""))
            title = item.get("title", "").strip()
            author = item.get("author", "").strip()
            if not book_id or not title:
                continue
            # 将数字 bookId 转成微信读书的 URL 短 ID
            weread_id = get_weread_id(book_id)
            display_title = f"{title}（{author}）" if author else title
            ret.append(
                {
                    "title": display_title,
                    "url": f"https://weread.qq.com/web/bookDetail/{weread_id}",
                }
            )
        return ret

    @staticmethod
    def read_already_download(
        full_path: str,
    ) -> typing.List[typing.Dict[str, typing.Any]]:
        content: typing.List[typing.Dict[str, typing.Any]] = []
        if pathlib.Path(full_path).exists():
            with open(full_path, encoding="utf-8") as fd:
                content = json.loads(fd.read())
        return content

    @staticmethod
    def merge_data(
        cur: typing.List[typing.Dict[str, typing.Any]],
        another: typing.List[typing.Dict[str, typing.Any]],
    ) -> typing.List[typing.Dict[str, typing.Any]]:
        merged_dict: typing.Dict[str, str] = {}
        for item in chain(cur, another):
            merged_dict[item["url"]] = item["title"]
        return [{"url": k, "title": v} for k, v in merged_dict.items()]

    def run(self):
        dir_name = "weread"
        debug_print(f"开始抓取 {dir_name}", "WEREAD")

        try:
            raw_data = self.get_raw()
            cleaned_data = self.clean_raw(raw_data)

            if not cleaned_data:
                debug_print("没有抓取到新数据（API 返回为空或需要 Cookie）", "WEREAD")
                return {"success": False}

            cur_date = current_date()
            raw_path = f"./raw/{dir_name}/{cur_date}.json"

            already_download_data = self.read_already_download(raw_path)
            merged_data = self.merge_data(cleaned_data, already_download_data)

            write_json_file(raw_path, merged_data)
            debug_print(f"数据已写入到 {raw_path}", "WEREAD")

            return {"success": True, "data_count": len(merged_data)}

        except Exception as e:
            logger.exception(f"WeRead 任务失败: {e}")
            return {"success": False}


if __name__ == "__main__":
    obj = WebSiteWeRead()
    result = obj.run()
    if result.get("success"):
        print(f"微信读书热榜抓取成功，共 {result['data_count']} 条数据。")
    else:
        print("微信读书热榜抓取失败（可能需要设置 WEREAD_COOKIE 环境变量）。")
