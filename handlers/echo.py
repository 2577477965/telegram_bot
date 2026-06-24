"""
回声消息处理器
处理用户发送的普通文本消息。
"""
from telegram import Update
from telegram.ext import ContextTypes


async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """回声处理：将用户消息原样返回"""
    user_text = update.message.text
    await update.message.reply_text(f"🔊 你说：{user_text}")