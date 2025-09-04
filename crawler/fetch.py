"""
移动端微博关键词抓取脚本
免 Cookie，直接跑
"""

import requests
import pymysql
import json
import sys
import os
from urllib.parse import quote

# 让脚本无论在哪都能 import config
sys.path.append(os.path.abspath("."))
from config import MYSQL

# 连接数据库
conn = pymysql.connect(** MYSQL)
cur = conn.cursor(pymysql.cursors.DictCursor)

# 完善请求头，避免被识别为爬虫
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Referer": "https://m.weibo.cn/search/",
    "X-Requested-With": "XMLHttpRequest"
}

def fetch(keyword="高考", pages=1):
    """
    keyword: 搜索关键词
    pages  : 抓取页数（每页 10 条左右）
    """
    total = 0
    # 对关键词进行URL编码
    encoded_keyword = quote(keyword)
    
    for page in range(1, pages + 1):
        # 修正containerid参数，添加正确的分隔符
        url = (
            "https://m.weibo.cn/api/container/getIndex"
            f"?containerid=100103type%3D1%26q%3D{encoded_keyword}"
            f"&page_type=searchall&page={page}"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            # 打印响应状态，便于调试
            print(f"[DEBUG] 第{page}页响应状态: {data.get('ok')}")
            
            # 如果API返回错误状态，停止抓取
            if data.get('ok') != 1:
                print(f"[ERROR] 第{page}页API返回错误: {data.get('msg', '未知错误')}")
                break
                
        except Exception as e:
            print(f"[ERROR] page {page} 请求失败：{e}")
            continue

        cards = data.get("data", {}).get("cards", [])
        if not cards:
            print(f"[INFO] 第 {page} 页无数据")
            continue

        page_count = 0
        for card in cards:
            # 尝试从不同结构中获取微博数据
            mblog = card.get("mblog") or card.get("card_group", [{}])[0].get("mblog")
            if not mblog:
                continue

            try:
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
                page_count += 1
            except Exception as e:
                print(f"[ERROR] 插入数据失败: {e}")
                conn.rollback()

        conn.commit()
        print(f"[INFO] 第 {page} 页写入 {page_count} 条")

    print(f"[DONE] 共写入 {total} 条微博")
    cur.close()
    conn.close()


if __name__ == "__main__":
    fetch(keyword="高考", pages=1)  # 先抓 1 页测试
