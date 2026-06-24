"""
/help 命令处理器
"""
from telegram import Update
from telegram.ext import ContextTypes


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /help 命令"""
    help_text = (
        "📖 **帮助菜单**\n\n"
        "**可用命令：**\n"
        "/start - 开始使用机器人\n"
        "/help - 显示此帮助信息\n\n"
        "**其他功能：**\n"
        "• 发送任意消息，机器人会回复你\n\n"
        "💡 如需添加新功能，请在 `handlers/` 目录下添加新的处理器。"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")