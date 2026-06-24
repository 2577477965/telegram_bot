"""
每日定时总结任务
每天早上 6:00 自动总结前一天的群消息。
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telegram.ext import ContextTypes

from config import (
    DB_PATH,
    SUMMARY_CHAT_ID,
    SUMMARY_TIMEZONE,
    MESSAGE_RETENTION_DAYS,
    SEND_TO_TELEGRAM,
)
from db import (
    get_messages_by_date_range,
    get_distinct_chats,
    cleanup_old_messages,
)
from summarizer import summarize_messages
from wechat import send_message as wechat_send, format_for_wechat
from utils import setup_logger

logger = setup_logger("daily_summary")


async def daily_summary_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """每日定时回调：总结昨天的群消息并发送给指定联系人"""
    tz = ZoneInfo(SUMMARY_TIMEZONE)
    now = datetime.now(tz)
    yesterday = (now - timedelta(days=1)).date()
    date_str = yesterday.isoformat()
    start = f"{date_str}T00:00:00"
    end = f"{date_str}T23:59:59"

    logger.info(f"开始生成 {date_str} 的每日总结...")

    try:
        # 获取所有有消息的群组
        chats = await get_distinct_chats(DB_PATH, start, end)

        if not chats:
            await context.bot.send_message(
                chat_id=int(SUMMARY_CHAT_ID),
                text=f"📭 {date_str} 所有群组均无消息记录",
            )
            logger.info(f"{date_str} 无消息，跳过总结")
            return

        # 获取所有消息
        messages = await get_messages_by_date_range(DB_PATH, start, end)

        # 逐群总结
        for chat_info in chats:
            chat_id = chat_info["chat_id"]
            chat_title = chat_info["chat_title"] or str(chat_id)

            chat_messages = [m for m in messages if m["chat_id"] == chat_id]

            summary = await summarize_messages(chat_title, chat_messages, date_str)

            if SEND_TO_TELEGRAM:
                try:
                    await context.bot.send_message(
                        chat_id=int(SUMMARY_CHAT_ID),
                        text=summary,
                    )
                except Exception as e:
                    logger.error(f"发送总结失败 ({chat_title}): {e}")

            # 同步推送到企业微信
            wechat_text = format_for_wechat(chat_title, date_str, summary)
            await wechat_send(wechat_text)

        logger.info(f"{date_str} 每日总结完成，共 {len(chats)} 个群组")

        # 清理旧消息
        retention_cutoff = (
            yesterday - timedelta(days=MESSAGE_RETENTION_DAYS)
        ).isoformat()
        await cleanup_old_messages(DB_PATH, retention_cutoff)

    except Exception as e:
        logger.error(f"每日总结任务失败: {e}")
        try:
            await context.bot.send_message(
                chat_id=int(SUMMARY_CHAT_ID),
                text=f"⚠️ {date_str} 每日总结生成失败，请检查日志",
            )
        except Exception:
            pass