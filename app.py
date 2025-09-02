from flask import Flask, render_template_string, redirect, request
import pymysql
from config import MYSQL

app = Flask(__name__)
conn = pymysql.connect(**MYSQL, cursorclass=pymysql.cursors.DictCursor)

@app.route("/")
def index():
    cur = conn.cursor()
    cur.execute("""
        SELECT w.id,w.username,w.content,w.created_at,h.keyword
        FROM weibo_raw w
        JOIN keyword_hit h ON w.id=h.weibo_id
        ORDER BY w.created_at DESC LIMIT 100
    """)
    rows = cur.fetchall()
    table = "<table border=1><tr><th>ID</th><th>用户</th><th>内容</th><th>关键词</th></tr>"
    for r in rows:
        table += f"<tr><td>{r['id']}</td><td>{r['username']}</td><td>{r['content'][:50]}...</td><td>{r['keyword']}</td></tr>"
    table += "</table>"
    return table

@app.route("/weibo/<int:weibo_id>")
def view(weibo_id):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM keyword_hit WHERE weibo_id=%s", (weibo_id,))
    if cur.fetchone():
        return "<h2>⚠️ 该微博含敏感内容，已被屏蔽</h2>"
    return f"<h3>微博 {weibo_id} 内容正常，可正常浏览</h3>"

if __name__ == "__main__":
    app.run(debug=True)