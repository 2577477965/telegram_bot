"""
/summary 命令处理器
支持手动触发指定日期的群消息总结。
用法：/summary [日期(YYYY-MM-DD)]，不填日期默认总结昨天
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from config import DB_PATH, SUMMARY_CHAT_ID, SUMMARY_TIMEZONE, SEND_TO_TELEGRAM
from db import get_messages_by_date_range, get_distinct_chats
from summarizer import summarize_messages
from wechat import send_message as wechat_send, format_for_wechat
from utils import setup_logger

logger = setup_logger("summary")


async def summary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /summary 命令"""
    tz = ZoneInfo(SUMMARY_TIMEZONE)
    now = datetime.now(tz)
    today = now.date()

    # 解析日期参数
    args = context.args
    if args:
        try:
            target_date = datetime.strptime(args[0], "%Y-%m-%d").date()
        except ValueError:
            await update.message.reply_text(
                "❌ 日期格式错误，请使用 YYYY-MM-DD 格式。\n"
                "例如：/summary 2026-06-21"
            )
            return

        if target_date > today:
            await update.message.reply_text("❌ 不能总结未来的日期")
            return
    else:
        target_date = today - timedelta(days=1)

    date_str = target_date.isoformat()
    start = f"{date_str}T00:00:00"
    end = f"{date_str}T23:59:59"

    await update.message.reply_text(f"⏳ 正在生成 {date_str} 的群消息总结...")

    try:
        # 获取所有有消息的群组
        chats = await get_distinct_chats(DB_PATH, start, end)

        if not chats:
            await update.message.reply_text(f"📭 {date_str} 没有任何群消息记录")
            return

        # 获取所有消息
        messages = await get_messages_by_date_range(DB_PATH, start, end)

        # 遍历每个群组生成总结
        for chat_info in chats:
            chat_id = chat_info["chat_id"]
            chat_title = chat_info["chat_title"] or str(chat_id)

            # 筛选该群的消息
            chat_messages = [m for m in messages if m["chat_id"] == chat_id]

            # 生成总结
            summary = await summarize_messages(chat_title, chat_messages, date_str)

            # 发送到 Telegram
            if SEND_TO_TELEGRAM:
                try:
                    await context.bot.send_message(
                        chat_id=int(SUMMARY_CHAT_ID),
                        text=summary,
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    logger.error(f"发送总结失败 ({chat_title}): {e}")
                    await context.bot.send_message(
                        chat_id=int(SUMMARY_CHAT_ID),
                        text=summary,
                    )

            # 同步推送到企业微信
            wechat_text = format_for_wechat(chat_title, date_str, summary)
            await wechat_send(wechat_text)

        await update.message.reply_text(
            f"✅ {date_str} 的群消息总结已生成并发送"
        )

    except Exception as e:
        logger.error(f"总结失败: {e}")
        await update.message.reply_text(f"❌ 总结生成失败: {e}")