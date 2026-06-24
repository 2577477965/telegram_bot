"""
t.me/s 频道消息抓取模块
从 Telegram 公开频道预览页抓取消息，存入数据库。
"""
import hashlib
import httpx
from datetime import datetime
from bs4 import BeautifulSoup

from config import DB_PATH, PROXY_URL, RSS_CHANNELS
from db import insert_message
from utils import setup_logger

logger = setup_logger("rss")

# 需要抓取的频道列表（从 .env 中读取，逗号分隔）
CHANNELS = [c.strip() for c in RSS_CHANNELS.split(",") if c.strip()]


def _channel_chat_id(channel: str) -> int:
    """为频道生成一个固定的负 chat_id（使用 MD5 确保确定性）"""
    h = hashlib.md5(channel.encode()).hexdigest()
    return -1000000000000 - (int(h, 16) % 1000000000000)


async def fetch_channel_messages(channel: str) -> list[dict]:
    """从 t.me/s/频道名 抓取消息列表"""
    url = f"https://t.me/s/{channel}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    async with httpx.AsyncClient(
        proxy=PROXY_URL or None,
        verify=False,
        timeout=30,
        follow_redirects=True,
    ) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            logger.warning(f"抓取 {channel} 失败: HTTP {resp.status_code}")
            return []

    return _parse_messages(resp.text, channel)


def _parse_messages(html: str, channel: str) -> list[dict]:
    """解析 t.me/s 页面的 HTML，提取消息"""
    soup = BeautifulSoup(html, "html.parser")
    messages = []

    for msg_div in soup.select(".tgme_widget_message_wrap"):
        try:
            text_div = msg_div.select_one(".tgme_widget_message_text")
            if not text_div:
                continue
            text = text_div.get_text(strip=True)

            time_tag = msg_div.select_one(".tgme_widget_message_date time")
            if time_tag and time_tag.get("datetime"):
                msg_date = time_tag["datetime"]
            else:
                msg_date = datetime.now().isoformat()

            msg_id_attr = msg_div.get("data-post")
            if msg_id_attr:
                msg_id = int(msg_id_attr.split("/")[-1])
            else:
                msg_id = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)

            chat_title = f"@{channel}"

            messages.append({
                "message_id": msg_id,
                "chat_id": _channel_chat_id(channel),
                "chat_title": chat_title,
                "user_id": 0,
                "username": channel,
                "first_name": chat_title,
                "text": text,
                "reply_to_message_id": None,
                "message_date": msg_date,
            })
        except Exception as e:
            logger.debug(f"解析消息失败: {e}")

    return messages


async def scrape_all_channels() -> int:
    """抓取所有配置的频道，返回处理的消息数"""
    total = 0
    for channel in CHANNELS:
        try:
            messages = await fetch_channel_messages(channel)
            for msg in messages:
                await insert_message(DB_PATH, msg)
            total += len(messages)
            logger.info(f"频道 {channel}: 抓取 {len(messages)} 条消息")
        except Exception as e:
            logger.error(f"频道 {channel} 抓取失败: {e}")
    return total