import time
import ahocorasick, pymysql, os, sys
sys.path.append(os.path.abspath("."))
from config import MYSQL, KEYWORDS

conn = pymysql.connect(**MYSQL)
cur  = conn.cursor()

A = ahocorasick.Automaton()
for idx, kw in enumerate(KEYWORDS):
    A.add_word(kw, (idx, kw))
A.make_automaton()

cur.execute("SELECT id,content FROM weibo_raw")

start = time.time()  # 关键词匹配处理开始

for row in cur.fetchall():
    for _, (_, kw) in A.iter(row[1]):
        cur.execute("INSERT INTO keyword_hit(weibo_id,keyword,hit_content) VALUES(%s,%s,%s)",
                    (row[0], kw, row[1]))

conn.commit()
end = time.time()  # 关键词匹配处理结束

print(f"匹配完成，关键词匹配处理时间: {end - start:.3f} 秒")