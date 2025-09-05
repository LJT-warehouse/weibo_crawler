from flask import Flask, render_template_string, redirect, request, render_template
import pymysql
from config import MYSQL
from analyzer.db_ops import get_cursor

app = Flask(__name__)
conn = pymysql.connect(**MYSQL, cursorclass=pymysql.cursors.DictCursor)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/hits")
def hits():
    with get_cursor() as cur:
        cur.execute("""
            SELECT h.keyword,
                   w.username,
                   w.content,
                   w.created_at
            FROM keyword_hit h
            JOIN weibo_raw w ON h.weibo_id = w.id
            ORDER BY w.id DESC
        """)
        rows = cur.fetchall()

    # 纯 HTML 字符串输出，不依赖模板文件
    html = f"""
    <!doctype html>
    <title>命中微博列表</title>
    <link rel="stylesheet"
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <div class="container mt-4">
      <h3>共命中 {len(rows)} 条微博</h3>
      <table class="table table-bordered">
        <thead>
          <tr><th>关键词</th><th>用户</th><th>内容</th><th>时间</th></tr>
        </thead>
        <tbody>
          {"".join(
              f"<tr><td>{r['keyword']}</td><td>{r['username']}</td>"
              f"<td>{r['content'][:120]}...</td><td>{r['created_at']}</td></tr>"
              for r in rows
          )}
        </tbody>
      </table>
    </div>
    """
    return html

@app.route("/weibo/<int:weibo_id>")
def view(weibo_id):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM keyword_hit WHERE weibo_id=%s", (weibo_id,))
    if cur.fetchone():
        return "<h2>⚠️ 该微博含敏感内容，已被屏蔽</h2>"
    return f"<h3>微博 {weibo_id} 内容正常，可正常浏览</h3>"

@app.route("/dashboard")
def dashboard():
    from analyzer.topic_stats import topic_stats
    data = topic_stats()   # 实时生成
    return render_template_string("""
<!doctype html>
<title>主题统计仪表盘</title>
<link rel="stylesheet"
 href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
<div class="container mt-4">
  <h2>主题热度与舆论领袖</h2>

  <!-- 关键词柱状图 -->
  <img src="{{ url_for('static', filename='img/kw_bar.png') }}" class="img-fluid mb-4">

  <!-- 关键词 TOP10 -->
  <h4>关键词 TOP10</h4>
  <table class="table table-sm">
    <tr><th>关键词</th><th>频次</th></tr>
    {% for kw,f in data.keywords %}
      <tr><td>{{ kw }}</td><td>{{ f }}</td></tr>
    {% endfor %}
  </table>

  <!-- 舆论领袖 TOP10 -->
  <h4>舆论领袖 TOP10</h4>
  <table class="table table-sm">
    <tr><th>用户</th><th>发帖数</th></tr>
    {% for u,f in data.users %}
      <tr><td>{{ u }}</td><td>{{ f }}</td></tr>
    {% endfor %}
  </table>
</div>
""", data=data)

@app.route("/troll")
def troll_demo():
    conn = pymysql.connect(**MYSQL, cursorclass=pymysql.cursors.DictCursor)
    cur = conn.cursor()
    cur.execute("SELECT * FROM troll_comments ORDER BY id DESC LIMIT 100")
    rows = cur.fetchall()
    return render_template("troll.html", comments=rows)

if __name__ == "__main__":
    app.run(debug=True)