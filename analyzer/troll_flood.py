"""
离线生成正能量/灌水评论并写入 troll_comments
"""
from analyzer.db_ops import get_cursor, get_hit_list
import random, datetime

# 100 条“正能量/灌水”模板
TEMPLATES = [
    "加油！一切都会好起来！💪",
    "支持正能量！",
    "希望大家都平安！",
    "今天也是元气满满的一天！",
    "一起努力，未来可期！",
    "谢谢分享，学到了！",
    "转发正能量！",
    "愿世界和平！",
    "祝大家开心每一天！",
    "阳光总在风雨后！"
]

def flood_troll(keyword="高考", amount=50):
    hits = get_hit_list(limit=9999)
    targets = [h for h in hits if h["keyword"] == keyword]
    if not targets:
        print("无命中微博，无需淹没")
        return

    with get_cursor() as cur:
        for weibo in targets:
            for _ in range(amount):
                cur.execute("""
                    INSERT INTO troll_comments
                    (target_weibo_id, username, comment)
                    VALUES(%s, %s, %s)
                """, (
                    weibo["id"],
                    f"水军{random.randint(1000,9999)}",
                    random.choice(TEMPLATES)
                ))
    print(f"[DONE] 已为 {len(targets)} 条微博各生成 {amount} 条控管评论")

if __name__ == "__main__":
    flood_troll(keyword="高考", amount=30)