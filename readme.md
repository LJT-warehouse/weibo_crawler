下面给出**使用MySQL数据库**、以**新浪微博**为目标的**B级实验详细分步指导**，每一步都包含**命令、代码、截图建议、注意事项**，你可以直接照做。  
分为五大部分，每部分都给出**MySQL建表、插入、查询语句**，并配套Python代码。

---

## ✅环境准备（一次性完成）

| 工具     | 安装命令（Windows/Mac通用）                                  |
| -------- | ------------------------------------------------------------ |
| MySQL    | [官网下载](https://dev.mysql.com/downloads/mysql/) 或 `brew install mysql` |
| Python库 | `pip install requests beautifulsoup4 pymysql flask pyahocorasick matplotlib lxml` |

- 启动MySQL服务：
```bash
mysql -u root -p
```

- 创建数据库：
```sql
CREATE DATABASE weibo_crawler CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE weibo_crawler;
```

---

## ✅Part1：数据捕获（微博内容抓取 → 存入MySQL）

### Step1：创建数据表

```sql
CREATE TABLE weibo_raw (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100),
    content TEXT,
    created_at DATETIME,
    reposts INT DEFAULT 0,
    comments INT DEFAULT 0,
    likes INT DEFAULT 0,
    keyword VARCHAR(50),
    raw_json JSON,
    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Step2：Python爬虫抓取微博（关键词“高考”）

```python
import requests
import pymysql
import json
from bs4 import BeautifulSoup
import time

# 连接MySQL
conn = pymysql.connect(host='localhost', user='root', password='你的密码', db='weibo_crawler', charset='utf8mb4')
cursor = conn.cursor()

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Cookie': '你的微博Cookie'
}

def fetch_weibo(keyword, page=1):
    url = f'https://weibo.com/ajax/search/topics?q={keyword}&page={page}'
    res = requests.get(url, headers=headers)
    data = res.json()
    for card in data['data']['cards']:
        if 'mblog' not in card:
            continue
        m = card['mblog']
        username = m['user']['screen_name']
        content = BeautifulSoup(m['text'], 'lxml').get_text()
        created_at = m['created_at']
        reposts = m.get('reposts_count', 0)
        comments = m.get('comments_count', 0)
        likes = m.get('attitudes_count', 0)

        cursor.execute("""
            INSERT INTO weibo_raw (username, content, created_at, reposts, comments, likes, keyword, raw_json)
            VALUES (%s, %s, STR_TO_DATE(%s, '%%a %%b %%d %%H:%%i:%%s +0800 %%Y'), %s, %s, %s, %s, %s)
        """, (username, content, created_at, reposts, comments, likes, keyword, json.dumps(m, ensure_ascii=False)))
    conn.commit()

# 抓5页
for i in range(1, 6):
    fetch_weibo('高考', page=i)
    time.sleep(2)

cursor.close()
conn.close()
```

---

## ✅Part2：协议还原（HTTP结构分析）

> 使用Fiddler/浏览器开发者工具，分析请求：

- **请求URL**：`https://weibo.com/ajax/search/topics?q=高考&page=1`
- **请求方法**：GET
- **Headers**：Cookie、User-Agent
- **响应格式**：JSON → 解析字段如上

---

## ✅Part3：关键词匹配（AC自动机 → 存入命中表）

### Step1：创建关键词命中表

```sql
CREATE TABLE keyword_hit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    weibo_id INT,
    keyword VARCHAR(50),
    hit_content TEXT,
    FOREIGN KEY (weibo_id) REFERENCES weibo_raw(id)
);
```

### Step2：关键词匹配并插入命中记录

```python
import ahocorasick

# 构建AC自动机
keywords = ['高考', '作弊', '泄题', '焦虑']
A = ahocorasick.Automaton()
for idx, key in enumerate(keywords):
    A.add_word(key, (idx, key))
A.make_automaton()

# 查询并匹配
cursor = conn.cursor()
cursor.execute("SELECT id, content FROM weibo_raw")
for row in cursor.fetchall():
    weibo_id, content = row
    for end_index, (idx, key) in A.iter(content):
        cursor.execute("""
            INSERT INTO keyword_hit (weibo_id, keyword, hit_content)
            VALUES (%s, %s, %s)
        """, (weibo_id, key, content))
conn.commit()
```

---

## ✅Part4：控管响应（网页重定向）

### Step1：Flask拦截器（关键词命中即跳转）

```python
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

@app.route('/weibo/<int:weibo_id>')
def view_weibo(weibo_id):
    cursor.execute("SELECT keyword FROM keyword_hit WHERE weibo_id = %s", (weibo_id,))
    hits = cursor.fetchall()
    if hits:
        return redirect('/blocked')
    return f"微博内容正常，ID={weibo_id}"

@app.route('/blocked')
def blocked():
    return "<h2>⚠️该微博包含敏感内容，已被屏蔽。</h2>"

if __name__ == '__main__':
    app.run(debug=True)
```

---

## ✅Part5：界面展示（Flask + MySQL）

### Step1：查询展示页面

```python
@app.route('/')
def index():
    cursor.execute("""
        SELECT w.id, w.username, w.content, w.created_at, h.keyword
        FROM weibo_raw w
        JOIN keyword_hit h ON w.id = h.weibo_id
        ORDER BY w.created_at DESC
    """)
    rows = cursor.fetchall()
    return render_template_string("""
    <h2>关键词命中微博列表</h2>
    <table border=1>
      <tr><th>ID</th><th>用户</th><th>内容</th><th>时间</th><th>关键词</th></tr>
      {% for r in rows %}
      <tr>
        <td>{{ r[0] }}</td>
        <td>{{ r[1] }}</td>
        <td>{{ r[2][:100] }}...</td>
        <td>{{ r[3] }}</td>
        <td>{{ r[4] }}</td>
      </tr>
      {% endfor %}
    </table>
    """, rows=rows)
```

---

## ✅MySQL常用查询（用于展示）

| 目的               | SQL                                                          |
| ------------------ | ------------------------------------------------------------ |
| 每个关键词出现次数 | `SELECT keyword, COUNT(*) FROM keyword_hit GROUP BY keyword;` |
| 高频用户           | `SELECT username, COUNT(*) FROM weibo_raw GROUP BY username ORDER BY COUNT(*) DESC LIMIT 10;` |
| 最新命中微博       | `SELECT * FROM keyword_hit ORDER BY id DESC LIMIT 20;`       |

---

## ✅截图建议（用于报告）

| 步骤        | 截图内容                               |
| ----------- | -------------------------------------- |
| MySQL表结构 | `SHOW TABLES;` + `DESCRIBE weibo_raw;` |
| 插入数据    | `SELECT * FROM weibo_raw LIMIT 5;`     |
| 关键词命中  | `SELECT * FROM keyword_hit LIMIT 5;`   |
| Flask界面   | 浏览器打开 `http://localhost:5000/`    |
| 控管跳转    | 访问命中微博跳转 `/blocked` 页         |

---

## ✅下一步建议（可选A级）

- 加入**情感分析**字段（SnowNLP）
- 加入**用户画像**（性别、地区、粉丝数）
- 使用**词云图**展示关键词频率
- 支持**实时抓包**（mitmproxy）

---

如需我帮你打包完整的**Flask项目结构（含SQL脚本）**或**生成开题PPT**，请继续告诉我。