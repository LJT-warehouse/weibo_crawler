"""
数据库通用读写封装
"""
import pymysql
from contextlib import contextmanager
from config import MYSQL

@contextmanager
def get_cursor():
    """
    上下文管理器：自动获取并关闭游标
    用法：
        with get_cursor() as cur:
            cur.execute(...)
    """
    conn = pymysql.connect(**MYSQL)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    try:
        yield cur
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

# ---------- 常用快捷函数 ----------
def insert_weibo(row_dict):
    """
    向 weibo_raw 表插入一条记录
    row_dict 必须包含：username,content,created_at,reposts,comments,likes,keyword,raw_json
    """
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO weibo_raw
            (username,content,created_at,reposts,comments,likes,keyword,raw_json)
            VALUES(%(username)s,%(content)s,%(created_at)s,
                   %(reposts)s,%(comments)s,%(likes)s,%(keyword)s,%(raw_json)s)
        """, row_dict)
        return cur.lastrowid   # 返回自增 id

def insert_hit(weibo_id, keyword, hit_content):
    """
    向 keyword_hit 插一条命中记录
    """
    with get_cursor() as cur:
        cur.execute("""
            INSERT INTO keyword_hit(weibo_id,keyword,hit_content)
            VALUES(%s,%s,%s)
        """, (weibo_id, keyword, hit_content))

def get_weibo_without_hit():
    """
    取出尚未做过关键词匹配的 weibo_raw 记录
    返回：List[Dict]
    """
    with get_cursor() as cur:
        cur.execute("""
            SELECT id,content
            FROM weibo_raw
            WHERE id NOT IN (SELECT DISTINCT weibo_id FROM keyword_hit)
        """)
        return cur.fetchall()

def get_hit_list(limit=100):
    """
    获取最新命中微博列表
    """
    with get_cursor() as cur:
        cur.execute("""
            SELECT w.id,w.username,w.content,w.created_at,h.keyword
            FROM weibo_raw w
            JOIN keyword_hit h ON w.id=h.weibo_id
            ORDER BY w.created_at DESC
            LIMIT %s
        """, (limit,))
        return cur.fetchall()