"""
/start 命令处理器
"""
from telegram import Update
from telegram.ext import ContextTypes


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /start 命令"""
    user = update.effective_user
    welcome_text = (
        f"👋 你好，{user.first_name}！\n\n"
        f"欢迎使用 Bot！以下是可用命令：\n"
        f"/start - 开始使用\n"
        f"/help - 查看帮助\n"
    )
    await update.message.reply_text(welcome_text)