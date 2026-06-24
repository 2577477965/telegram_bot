#test
#test2 2026年6月24日
#test3
#测试更新代码上传
"""
Telegram Bot 主入口
RSS 频道消息抓取 + AI 总结 + 定时推送。
"""
from datetime import time

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler
from telegram.request import HTTPXRequest

from config import (
    BOT_TOKEN,
    DEEPSEEK_API_KEY,
    SUMMARY_CHAT_ID,
    SUMMARY_TIME,
    DB_PATH,
    PROXY_URL,
)
from db import init_db
from jobs import daily_summary_job
from utils import setup_logger
from handlers import (
    start_handler,
    help_handler,
    summary_handler,
)
import proxy
import rss_scraper

logger = setup_logger()


async def post_init(app: Application) -> None:
    """Application 初始化回调：初始化数据库"""
    await init_db(DB_PATH)


def main() -> None:
    """主函数：创建并运行 Bot"""
    # 检查必要配置
    if not BOT_TOKEN:
        logger.error("❌ 未设置 BOT_TOKEN！请在 .env 文件中配置你的 Bot Token。")
        return
    if not DEEPSEEK_API_KEY:
        logger.error("❌ 未设置 DEEPSEEK_API_KEY！请在 .env 文件中配置你的 DeepSeek API Key。")
        return
    if not SUMMARY_CHAT_ID:
        logger.error("❌ 未设置 SUMMARY_CHAT_ID！请在 .env 文件中配置接收总结的 Telegram 用户 ID。")
        return

    # 配置代理
    actual_proxy = PROXY_URL
    if not actual_proxy:
        # 尝试自动启动 Shadowsocks 代理
        proxy_ok = proxy.start_sslocal()
        if proxy_ok:
            actual_proxy = proxy.get_proxy_url()

    # 创建 HTTPX 请求
    # 普通请求
    request = HTTPXRequest(
        proxy=actual_proxy or None,
        connect_timeout=30,
        read_timeout=60,
        write_timeout=30,
    )
    # getUpdates 长轮询请求（需要更长的超时）
    get_updates_request = HTTPXRequest(
        proxy=actual_proxy or None,
        connect_timeout=30,
        read_timeout=60,
        write_timeout=30,
    )

    builder = Application.builder().token(BOT_TOKEN).post_init(post_init)
    builder = builder.request(request)
    builder = builder.get_updates_request(get_updates_request)
    if actual_proxy:
        logger.info(f"使用代理: {actual_proxy}")
    else:
        logger.warning("未配置代理，Bot 可能无法连接 Telegram API")
    application = builder.build()

    # === 注册处理器 ===

    # /summary 命令：手动触发总结
    application.add_handler(CommandHandler("summary", summary_handler))

    # /start 命令
    application.add_handler(CommandHandler("start", start_handler))

    # /help 命令
    application.add_handler(CommandHandler("help", help_handler))

    # === 配置定时任务 ===
    async def rss_scrape_job(context):
        count = await rss_scraper.scrape_all_channels()
        if count > 0:
            logger.info(f"RSS 抓取: {count} 条新消息")

    # 每 30 分钟抓取一次频道消息
    application.job_queue.run_repeating(
        rss_scrape_job,
        interval=1800,
        first=10,
    )
    # 启动时立即抓取一次
    application.job_queue.run_once(rss_scrape_job, when=5)

    hour, minute = map(int, SUMMARY_TIME.split(":"))
    application.job_queue.run_daily(
        daily_summary_job,
        time=time(hour=hour, minute=minute),
        days=(0, 1, 2, 3, 4, 5, 6),
    )
    logger.info(f"📅 每日总结定时任务已设置: {SUMMARY_TIME}")

    logger.info("🤖 Bot 正在启动...")
    logger.info("   按 Ctrl+C 停止运行")

    # 启动轮询（丢弃旧更新，避免 Conflict）
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()