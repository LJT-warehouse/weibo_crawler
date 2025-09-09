import pymysql
from config import MYSQL

conn = pymysql.connect(**MYSQL)
cur = conn.cursor()

# 先清空所有有外键依赖的表
cur.execute("DELETE FROM troll_comments;")
cur.execute("DELETE FROM keyword_hit;")
cur.execute("DELETE FROM weibo_raw;")
conn.commit()
print("troll_comments、keyword_hit 和 weibo_raw 表已清空")

cur.close()
conn.close()