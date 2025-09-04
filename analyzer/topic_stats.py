"""
离线主题统计 + 舆论领袖
"""
import os, sys
sys.path.append(os.path.abspath("."))

from collections import Counter, defaultdict
import pickle
from datetime import datetime
import matplotlib
matplotlib.use("Agg")  # 无窗口环境
import matplotlib.pyplot as plt

from analyzer.db_ops import get_hit_list, get_cursor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

# 设置中文字体（Windows 用 SimHei，Linux/Mac 用 DejaVu Sans）
rcParams['font.family'] = 'SimHei'          # Windows
# rcParams['font.family'] = 'DejaVu Sans'   # Linux/Mac
rcParams['axes.unicode_minus'] = False      # 解决负号方块

def topic_stats(days=30):
    rows = get_hit_list(limit=10000)
    if not rows:
        print("[WARN] 无命中数据，请先跑 keyword_match")
        return

    # 1. 关键词频率
    kw_counter = Counter([r["keyword"] for r in rows])

    # 2. 舆论领袖（Top 用户）
    user_counter = Counter([r["username"] for r in rows])

    # 3. 热点时间线（按日）
    daily = defaultdict(int)
    for r in rows:
        d = r["created_at"].strftime("%Y-%m-%d")
        daily[d] += 1

    # 4. 画图
    plt.figure(figsize=(8, 4))
    plt.bar(kw_counter.keys(), kw_counter.values())
    plt.title("关键词热度")
    plt.tight_layout()
    os.makedirs("static/img", exist_ok=True)
    plt.savefig("static/img/kw_bar.png")
    plt.close()

    # 5. 存入表（可选）
    with get_cursor() as cur:
        cur.execute("DELETE FROM topic_stats")  # 先清旧数据
        for kw, freq in kw_counter.items():
            cur.execute("""
                INSERT INTO topic_stats(date, keyword, freq, top_user)
                VALUES(CURDATE(), %s, %s, %s)
            """, (kw, freq, user_counter.most_common(1)[0][0]))

    print("[DONE] 主题统计完成，图表已保存到 static/img/kw_bar.png")
    return {"keywords": kw_counter.most_common(10),
            "users": user_counter.most_common(10),
            "daily": dict(daily)}

if __name__ == "__main__":
    topic_stats()