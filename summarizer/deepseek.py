"""
DeepSeek API 总结模块
使用 DeepSeek 大模型对群聊消息进行智能总结。
"""
import httpx
from openai import AsyncOpenAI

from config import DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL, PROXY_URL
from utils import setup_logger

logger = setup_logger("summarizer")

MAX_PROMPT_CHARS = 8000

# 创建带代理的 HTTP 客户端
_http_client = None
if PROXY_URL:
    _http_client = httpx.AsyncClient(proxy=PROXY_URL, timeout=60.0)

SYSTEM_PROMPT = """你是一个专业的群聊消息总结助手。你的任务是对给定的群聊消息记录进行精炼总结。

请按照以下格式输出总结：

📌 **今日话题**
- 列出群内讨论的主要话题，每个话题一句话概括

🔑 **关键讨论**
- 提炼出有深度的讨论内容，包括不同的观点和论据

📋 **待办事项**
- 如果有人在聊天中提到了需要做的事情，列出来

💡 **其他亮点**
- 有趣的发言、分享的链接、重要通知等

注意：
- 语言简洁明了，用中文输出
- 忽略纯粹的表情、灌水、无意义重复内容
- 如果消息太少无法总结，如实说明"""


def _format_messages(messages: list[dict]) -> str:
    """将消息列表格式化为 prompt 文本"""
    lines = []
    total = len(messages)

    for msg in messages:
        name = msg.get("username") or msg.get("first_name") or str(msg.get("user_id", "unknown"))
        time_str = msg.get("message_date", "")
        # 提取时间中的 HH:MM 部分
        if "T" in time_str:
            time_str = time_str.split("T")[1][:5]
        text = msg.get("text", "")

        prefix = f"[{time_str}] {name}"
        if msg.get("reply_to_message_id"):
            prefix += " (回复)"

        lines.append(f"{prefix}: {text}")

    formatted = "\n".join(lines)

    if len(formatted) > MAX_PROMPT_CHARS:
        truncated_lines = []
        char_count = 0
        shown = 0
        for line in lines:
            if char_count + len(line) > MAX_PROMPT_CHARS - 100:
                break
            truncated_lines.append(line)
            char_count += len(line) + 1
            shown += 1
        formatted = "\n".join(truncated_lines)
        formatted += f"\n\n...(共 {total} 条消息，已截断前 {shown} 条)"

    return formatted


async def summarize_messages(
    chat_title: str, messages: list[dict], date: str
) -> str:
    """
    对群聊消息进行 AI 总结

    Args:
        chat_title: 群组名称
        messages: 消息列表
        date: 日期字符串 (YYYY-MM-DD)

    Returns:
        总结文本
    """
    if not messages:
        return f"📊 {chat_title}：{date} 无消息记录"

    user_prompt = (
        f"群名称：{chat_title}\n"
        f"日期：{date}\n"
        f"消息总数：{len(messages)}\n\n"
        f"--- 消息记录 ---\n"
        f"{_format_messages(messages)}\n"
        f"--- 消息记录结束 ---\n\n"
        f"请对以上群聊消息进行总结。"
    )

    try:
        client = AsyncOpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            http_client=_http_client,
        )

        response = await client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2048,
            temperature=0.3,
        )

        summary = response.choices[0].message.content
        logger.info(f"总结成功: {chat_title} ({date}), {len(messages)} 条消息")
        return f"📊 **{chat_title}** — {date} 消息摘要\n\n{summary}"

    except Exception as e:
        logger.error(f"DeepSeek API 调用失败: {e}")
        return (
            f"📊 **{chat_title}** — {date} 消息摘要\n\n"
            f"⚠️ AI 总结生成失败，请稍后重试。\n"
            f"当日消息数：{len(messages)}"
        )