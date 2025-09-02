CREATE DATABASE IF NOT EXISTS weibo_crawler DEFAULT CHARACTER SET utf8mb4;
USE weibo_crawler;

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

CREATE TABLE keyword_hit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    weibo_id INT,
    keyword VARCHAR(50),
    hit_content TEXT,
    FOREIGN KEY (weibo_id) REFERENCES weibo_raw(id)
);

CREATE INDEX kw_idx ON keyword_hit(keyword);