"""
全局配置模块
从环境变量加载配置，提供统一的配置访问入口。
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Bot 配置
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# 总结配置
SUMMARY_CHAT_ID = os.getenv("SUMMARY_CHAT_ID", "")
SUMMARY_TIME = os.getenv("SUMMARY_TIME", "06:00")
SUMMARY_TIMEZONE = os.getenv("SUMMARY_TIMEZONE", "Asia/Shanghai")

# 数据库配置
DB_PATH = os.getenv("DB_PATH", "data/messages.db")
MESSAGE_RETENTION_DAYS = int(os.getenv("MESSAGE_RETENTION_DAYS", "30"))

# 代理配置（Telegram API 需要代理访问）
PROXY_URL = os.getenv("PROXY_URL", "")

# RSS 频道列表（逗号分隔的频道名，如 zaihuapd,channel2）
RSS_CHANNELS = os.getenv("RSS_CHANNELS", "")

# 企业微信机器人 Webhook
WECHAT_WEBHOOK_URL = os.getenv("WECHAT_WEBHOOK_URL", "")

# 是否发送总结到 Telegram（true/false）
SEND_TO_TELEGRAM = os.getenv("SEND_TO_TELEGRAM", "true").lower() == "true"