"""
群消息收集处理器
静默收集所有群聊文本消息，存入 SQLite 数据库。
"""
from telegram import Update
from telegram.ext import ContextTypes

from config import DB_PATH
from db import insert_message
from utils import setup_logger

logger = setup_logger("collector")


async def collector_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """收集群聊中的文本消息"""
    msg = update.effective_message
    if not msg or not msg.text:
        return

    text = msg.text.strip()
    if not text:
        return

    chat = update.effective_chat
    user = update.effective_user

    message_data = {
        "message_id": msg.message_id,
        "chat_id": chat.id,
        "chat_title": chat.title or str(chat.id),
        "user_id": user.id if user else 0,
        "username": user.username if user else None,
        "first_name": user.first_name if user else None,
        "text": text,
        "reply_to_message_id": (
            msg.reply_to_message.message_id
            if msg.reply_to_message
            else None
        ),
        "message_date": msg.date.isoformat(),
    }

    await insert_message(DB_PATH, message_data)