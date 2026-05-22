# main.py

import concurrent.futures
import time
from website_36kr import WebSite36Kr
from website_github import WebSiteGitHub
from website_juejin import WebSiteJueJin
from website_sspai import WebSiteSSPai
from website_weread import WebSiteWeRead
from utils import debug_print

def run_website_task(website_obj, website_name):
    try:
        debug_print("开始执行任务", website_name)
        result = website_obj.run()
        if result and result.get("success"):
            debug_print(f"任务执行成功，获取到 {result.get('data_count', 0)} 条数据", website_name)
            return True
        else:
            debug_print("任务执行失败或未返回成功状态", website_name)
            return False
    except Exception as e:
        debug_print(f"任务执行异常: {str(e)}", website_name)
        return False

def main():
    debug_print("开始执行所有网站任务")

    all_websites = [
        (WebSite36Kr(), "36KR"),
        (WebSiteGitHub(), "GITHUB"),
        (WebSiteJueJin(), "JUEJIN"),
        (WebSiteSSPai(), "SSPAI"),
        (WebSiteWeRead(), "WEREAD"),
    ]

    successful_tasks = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(all_websites)) as executor:
        future_to_website = {
            executor.submit(run_website_task, website_obj, website_name): website_name
            for website_obj, website_name in all_websites
        }

        for future in concurrent.futures.as_completed(future_to_website):
            website_name = future_to_website[future]
            try:
                success = future.result()
                if success:
                    successful_tasks += 1
                    debug_print(f"✓ {website_name} 任务成功完成")
                else:
                    debug_print(f"✗ {website_name} 任务失败")
            except Exception as e:
                debug_print(f"✗ {website_name} 任务在主线程中捕获到异常: {str(e)}")

    debug_print(f"所有网站任务执行完成，成功 {successful_tasks}/{len(all_websites)} 个任务")

if __name__ == "__main__":
    main()
