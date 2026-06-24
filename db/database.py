"""
SQLite 数据库操作模块
提供消息的存储和查询功能。
"""
import os
import aiosqlite
from utils import setup_logger

logger = setup_logger("db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS messages (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id          INTEGER NOT NULL,
    chat_id             INTEGER NOT NULL,
    chat_title          TEXT,
    user_id             INTEGER NOT NULL,
    username            TEXT,
    first_name          TEXT,
    text                TEXT NOT NULL,
    reply_to_message_id INTEGER,
    message_date        TIMESTAMP NOT NULL,
    stored_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message_id, chat_id)
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_messages_chat_date
    ON messages(chat_id, message_date);
"""


async def init_db(db_path: str) -> None:
    """初始化数据库：创建表结构"""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute(CREATE_TABLE_SQL)
        await db.execute(CREATE_INDEX_SQL)
        await db.commit()
    logger.info(f"数据库已初始化: {db_path}")


async def insert_message(db_path: str, msg: dict) -> None:
    """插入一条消息，重复的 (message_id, chat_id) 会被忽略"""
    sql = """
    INSERT OR IGNORE INTO messages
        (message_id, chat_id, chat_title, user_id, username, first_name,
         text, reply_to_message_id, message_date)
    VALUES
        (:message_id, :chat_id, :chat_title, :user_id, :username, :first_name,
         :text, :reply_to_message_id, :message_date)
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute(sql, msg)
            await db.commit()
    except Exception as e:
        logger.error(f"插入消息失败: {e}")


async def get_messages_by_date_range(
    db_path: str, start: str, end: str
) -> list[dict]:
    """查询指定日期范围内的消息"""
    sql = """
    SELECT message_id, chat_id, chat_title, user_id, username, first_name,
           text, reply_to_message_id, message_date
    FROM messages
    WHERE message_date >= ? AND message_date < ?
    ORDER BY chat_id, message_date
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(sql, (start, end))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_distinct_chats(
    db_path: str, start: str, end: str
) -> list[dict]:
    """获取指定日期范围内有消息的群组列表"""
    sql = """
    SELECT chat_id, MAX(chat_title) as chat_title, COUNT(*) as msg_count
    FROM messages
    WHERE message_date >= ? AND message_date < ?
    GROUP BY chat_id
    ORDER BY msg_count DESC
    """
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(sql, (start, end))
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def cleanup_old_messages(db_path: str, before: str) -> int:
    """删除指定日期之前的消息，返回删除数量"""
    sql = "DELETE FROM messages WHERE message_date < ?"
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(sql, (before,))
        await db.commit()
        deleted = cursor.rowcount
        if deleted > 0:
            logger.info(f"已清理 {deleted} 条旧消息 (早于 {before})")
        return deleted