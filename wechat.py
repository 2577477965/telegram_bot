"""
企业微信 Webhook 通知模块
通过企业微信机器人发送消息到微信群。
"""
import httpx
from config import WECHAT_WEBHOOK_URL, PROXY_URL
from utils import setup_logger

logger = setup_logger("wechat")


async def send_message(text: str) -> bool:
    """发送 Markdown 消息到企业微信群"""
    if not WECHAT_WEBHOOK_URL:
        return False

    # 企业微信消息限制 4096 字符
    if len(text) > 4000:
        text = text[:4000] + "\n\n...(内容过长已截断)"

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": text,
        },
    }

    try:
        async with httpx.AsyncClient(
            proxy=PROXY_URL or None,
            verify=False,
            timeout=15,
        ) as client:
            resp = await client.post(WECHAT_WEBHOOK_URL, json=payload)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("errcode") == 0:
                    logger.info("微信推送成功")
                    return True
                else:
                    logger.error(f"微信推送失败: {result}")
                    return False
            else:
                logger.error(f"微信推送 HTTP {resp.status_code}")
                return False
    except Exception as e:
        logger.error(f"微信推送异常: {e}")
        return False


def format_for_wechat(chat_title: str, date: str, summary: str) -> str:
    """格式化为企业微信 Markdown 格式"""
    return (
        f"## {chat_title} — {date} 消息摘要\n\n"
        f"{summary}\n\n"
        f"> 由 AI 自动生成 · {date}"
    )