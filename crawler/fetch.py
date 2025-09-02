"""
移动端微博关键词抓取脚本
免 Cookie，直接跑
"""

import requests
import pymysql
import json
import sys
import os

# 让脚本无论在哪都能 import config
sys.path.append(os.path.abspath("."))
from config import MYSQL

# 连接数据库
conn = pymysql.connect(**MYSQL)
cur = conn.cursor(pymysql.cursors.DictCursor)

# 移动端接口用的极简 headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"
}

def fetch(keyword="高考", pages=1):
    """
    keyword: 搜索关键词
    pages  : 抓取页数（每页 10 条左右）
    """
    total = 0
    for page in range(1, pages + 1):
        url = (
            "https://m.weibo.cn/api/container/getIndex"
            f"?containerid=100103type=1&q={keyword}&page_type=searchall&page={page}"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[ERROR] page {page} 请求失败：{e}")
            continue

        cards = data.get("data", {}).get("cards", [])
        if not cards:
            print(f"[INFO] 第 {page} 页无数据")
            continue

        for card in cards:
            mblog = card.get("mblog")
            if not mblog:
                continue

            cur.execute(
                """
                INSERT INTO weibo_raw
                (username, content, created_at,
                 reposts, comments, likes,
                 keyword, raw_json)
                VALUES
                (%s, %s, STR_TO_DATE(%s,'%%a %%b %%d %%H:%%i:%%s +0800 %%Y'),
                 %s, %s, %s, %s, %s)
                """,
                (
                    mblog["user"]["screen_name"],
                    mblog["text"],
                    mblog["created_at"],
                    mblog.get("reposts_count", 0),
                    mblog.get("comments_count", 0),
                    mblog.get("attitudes_count", 0),
                    keyword,
                    json.dumps(mblog, ensure_ascii=False),
                ),
            )
            total += 1

        conn.commit()
        print(f"[INFO] 第 {page} 页写入 {len(cards)} 条")

    print(f"[DONE] 共写入 {total} 条微博")
    cur.close()
    conn.close()


if __name__ == "__main__":
    fetch(keyword="高考", pages=1)  # 先抓 1 页测试