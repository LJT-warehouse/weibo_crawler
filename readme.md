# Weibo Crawler 与关键词命中演示

一个基于 Python 的微博数据抓取、关键词匹配与可视化演示项目。项目提供：
- 抓取移动端微博搜索结果并写入 MySQL
- 使用 AC 自动机进行关键词命中，生成命中列表
- 通过 Flask 展示命中微博列表、简单仪表盘
- 本地“水军评论”离线模拟（仅写本地数据库，不会向官网发送评论）

> 合规提醒：本项目仅用于课程实验与技术学习。请遵守目标网站的服务条款及法律法规，合理控制访问频次，不要用于任何滥用、刷量、绕过风控的行为。

---

## 目录结构

```
weibo_crawler/
  app.py                      # Flask Web 入口
  config.py                   # 数据库、关键词、Cookie 等配置
  requirements.txt            # 依赖列表
  sql/
    init_db.sql               # 初始化数据库与表结构
  crawler/
    fetch.py                  # 移动端接口抓取脚本（免 Cookie，可选带 Cookie）
  analyzer/
    db_ops.py                 # 数据库读写封装
    keyword_match.py          # 关键词命中写入 keyword_hit
    topic_stats.py            # 关键词/用户统计（仪表盘使用）
    troll_flood.py            # 本地“水军评论”离线模拟（写 troll_comments）
  templates/
    dashboard.html            # 仪表盘模板
    troll.html                # 离线评论展示
  static/
    img/kw_bar.png            # 示例图片（可替换）
```

---

## 环境要求

- Python 3.9+
- MySQL 5.7+（推荐 8.0）
- 操作系统：Windows/macOS/Linux

---

## 快速开始（Windows PowerShell 示例）

1) 克隆并安装依赖

```powershell
cd D:\weibo_crawler
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) 初始化数据库

```powershell
# 确保已安装并启动 MySQL，记住 root 密码
mysql -u root -p < .\sql\init_db.sql
```

3) 配置 `config.py`

- 将 `MYSQL["password"]` 改为你的实际密码
- 可在 `KEYWORDS` 中增删关键词
- 如遇风控（状态码 432/403），可将浏览器中 `m.weibo.cn` 的 Cookie 粘贴到 `WEIBO_COOKIE`

4) 抓取微博（写入 `weibo_raw`）

```powershell
python .\crawler\fetch.py
```

默认抓取关键词“高考”的 1 页数据。若要调整，在 `fetch.py` 末尾修改：

```python
if __name__ == "__main__":
    fetch(keyword="高考", pages=1)
```

5) 关键词命中（写入 `keyword_hit`）

```powershell
python .\analyzer\keyword_match.py
```

6) 启动 Web 界面

```powershell
python .\app.py
```

浏览器访问：
- 命中列表首页：`http://127.0.0.1:5000/`
- 命中判断示例：`http://127.0.0.1:5000/weibo/<id>`（把 `<id>` 换成实际微博 ID）
- 仪表盘：`http://127.0.0.1:5000/dashboard`
- 离线评论演示：`http://127.0.0.1:5000/troll`

---

## 功能说明

- 抓取：`crawler/fetch.py` 通过移动端公开接口抓取搜索结果，入库到 `weibo_raw`。
- 匹配：`analyzer/keyword_match.py` 使用 `pyahocorasick` 对 `content` 做关键词匹配，将命中写入 `keyword_hit`。
- 拦截示例：访问 `GET /weibo/<id>` 时检查 `keyword_hit` 是否存在该 `weibo_id`，存在则显示“已被屏蔽”。
- 仪表盘：`/dashboard` 展示关键词频次、活跃用户等（示例）。
- 离线评论：`analyzer/troll_flood.py` 生成模板评论写入本地表 `troll_comments`，`/troll` 页面读取展示。

> 说明：项目没有对微博官网执行评论发布操作；“水军评论”仅为本地数据库模拟，用于课程演示。

---

## 数据库结构

执行 `sql/init_db.sql` 创建：

- `weibo_raw`：抓取原始数据（含 `raw_json`）
- `keyword_hit`：命中结果（`weibo_id` 外键引用 `weibo_raw.id`）
- `topic_stats`：主题统计结果表（由 `analyzer/topic_stats.py` 生成并覆盖写入，`date + keyword` 唯一）

如需使用离线评论演示，请建表：

```sql
CREATE TABLE troll_comments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  target_weibo_id INT NOT NULL,
  username VARCHAR(100) NOT NULL,
  comment TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 获取 Cookie（可选，遇到 432/403 时）

1) 在浏览器访问 `https://m.weibo.cn/search` 并登录
2) 打开开发者工具 Network，选择任意 `m.weibo.cn` 请求
3) 复制完整 `Cookie`，粘贴到 `config.py` 的 `WEIBO_COOKIE`

项目会自动把 Cookie 加入请求头，降低被风控概率。

---

## 常见问题（FAQ）

- 报 432/403：
  - 配置有效 `WEIBO_COOKIE`
  - 降低 `pages` 与访问频次，增加间隔
  - 更换网络/账号/UA

- `raw_json JSON` 不支持：
  - 升级 MySQL 至 5.7+；或将字段改为 `LONGTEXT`

- 中文乱码：
  - 确保库与连接均为 `utf8mb4`

- 端口占用：
  - 修改 `app.py`：`app.run(debug=True, port=5001)`

---

## 许可与声明

本项目仅用于教学与研究，不对任何第三方平台施加负载或进行非授权操作。使用者需自行确保使用合规、合法，并对使用后果负责。


