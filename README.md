# Telegram 频道消息 AI 总结 Bot

自动抓取 Telegram 公开频道消息，通过 DeepSeek AI 生成每日智能总结，推送到企业微信和 Telegram。

## 功能概述

| 功能 | 说明 |
|---|---|
| RSS 频道抓取 | 每 30 分钟从 `t.me/s/频道名` 抓取公开频道消息 |
| AI 智能总结 | 通过 DeepSeek API 对消息进行智能总结（话题、关键讨论、待办事项） |
| 定时推送 | 每天 06:00 自动生成前一日总结并推送 |
| 手动总结 | 私聊 Bot 发送 `/summary 2026-06-24` 指定日期总结 |
| 企业微信推送 | 通过 Webhook 推送总结到企业微信群 |
| Telegram 推送 | 推送总结到指定 Telegram 联系人（可关闭） |
| SQLite 持久化 | 消息本地存储，支持去重和自动清理 |

## 项目结构

```
telegram_bot/
├── main.py                 # 主入口：启动 Bot、注册定时任务
├── config.py               # 配置管理（从 .env 加载）
├── proxy.py                # 代理模块（自动启动 Shadowsocks 代理）
├── rss_scraper.py          # t.me/s 频道消息抓取（BeautifulSoup 解析）
├── wechat.py               # 企业微信 Webhook 推送模块
├── requirements.txt        # Python 依赖
├── .env / .env.example     # 环境变量配置
├── .gitignore
├── db/                     # 数据库模块
│   ├── __init__.py
│   └── database.py         # SQLite 建表、插入、查询、清理
├── summarizer/             # AI 总结模块
│   ├── __init__.py
│   └── deepseek.py         # DeepSeek API 调用、Prompt 构建
├── handlers/               # Bot 命令处理器
│   ├── __init__.py
│   ├── start.py            # /start 命令
│   ├── help.py             # /help 命令
│   └── summary.py          # /summary 命令（手动触发总结）
├── jobs/                   # 定时任务
│   ├── __init__.py
│   └── summary_job.py      # 每日 06:00 自动总结
└── utils/                  # 工具模块
    ├── __init__.py
    └── logger.py           # 日志工具
```

## 数据流

```
t.me/s/zaihuapd ──(每30分钟抓取)──→ SQLite ──(06:00/手动)──→ DeepSeek API ──→ 企业微信
                                                                         └──→ Telegram
```

## 快速开始

### 1. 环境要求

- Python 3.11+
- 网络代理（Clash / v2rayN 等，用于访问 Telegram 和 DeepSeek API）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 .env

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```ini
# Telegram Bot Token（从 @BotFather 获取）
BOT_TOKEN=你的BotToken

# DeepSeek API（从 platform.deepseek.com 获取）
DEEPSEEK_API_KEY=你的APIKey
DEEPSEEK_MODEL=deepseek-chat

# 接收总结的 Telegram 用户 ID
SUMMARY_CHAT_ID=你的用户ID

# 企业微信机器人 Webhook
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# 定时总结时间（默认早上6点）
SUMMARY_TIME=06:00

# RSS 频道列表（逗号分隔，不含 @）
RSS_CHANNELS=zaihuapd,channel2

# 代理配置
PROXY_URL=http://127.0.0.1:7897

# 是否发送总结到 Telegram（true/false）
SEND_TO_TELEGRAM=true
```

### 4. 启动

```bash
python main.py
```

## 配置说明

| 变量 | 默认值 | 必填 | 说明 |
|---|---|---|---|
| `BOT_TOKEN` | (无) | ✅ | Telegram Bot Token |
| `DEEPSEEK_API_KEY` | (无) | ✅ | DeepSeek API Key |
| `SUMMARY_CHAT_ID` | (无) | ✅ | 接收总结的 TG 用户 ID |
| `WECHAT_WEBHOOK_URL` | (无) | ❌ | 企业微信 Webhook |
| `RSS_CHANNELS` | (无) | ✅ | 频道名，逗号分隔 |
| `PROXY_URL` | (无) | ❌ | HTTP/SOCKS5 代理 |
| `SUMMARY_TIME` | `06:00` | ❌ | 自动总结时间 |
| `SUMMARY_TIMEZONE` | `Asia/Shanghai` | ❌ | 时区 |
| `SEND_TO_TELEGRAM` | `true` | ❌ | 是否发 TG |
| `DB_PATH` | `data/messages.db` | ❌ | 数据库路径 |
| `MESSAGE_RETENTION_DAYS` | `30` | ❌ | 消息保留天数 |

## Bot 命令

| 命令 | 说明 |
|---|---|
| `/start` | 开始使用 |
| `/help` | 查看帮助 |
| `/summary` | 总结昨天的消息 |
| `/summary 2026-06-24` | 总结指定日期的消息 |

## 添加新频道

编辑 `.env` 中的 `RSS_CHANNELS`，逗号分隔即可：

```ini
RSS_CHANNELS=zaihuapd,channel2,channel3
```

重启 Bot 生效。

## 依赖

- `python-telegram-bot[job-queue]` — Telegram Bot SDK
- `openai` — DeepSeek API（兼容 OpenAI 接口）
- `aiosqlite` — 异步 SQLite
- `beautifulsoup4` — HTML 解析（t.me/s 抓取）
- `httpx[socks]` — HTTP 客户端（代理支持）
- `python-dotenv` — 环境变量加载