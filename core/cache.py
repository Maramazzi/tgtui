"""
SQLite кэш через aiosqlite.
"""
import aiosqlite
from datetime import datetime
from core.config import CACHE_FILE
from core.logger import get_logger

log = get_logger("cache")

SCHEMA = """
CREATE TABLE IF NOT EXISTS dialogs (
    id          INTEGER PRIMARY KEY,
    name        TEXT,
    username    TEXT,
    unread      INTEGER DEFAULT 0,
    last_msg    TEXT,
    last_date   TEXT,
    type        TEXT,
    folder_id   INTEGER DEFAULT 0,
    pinned      INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    id          INTEGER,
    chat_id     INTEGER,
    sender_id   INTEGER,
    sender_name TEXT,
    text        TEXT,
    date        TEXT,
    media_type  TEXT,
    media_path  TEXT,
    reply_to_id INTEGER,
    edited      INTEGER DEFAULT 0,
    reactions   TEXT,
    PRIMARY KEY (id, chat_id)
);

CREATE TABLE IF NOT EXISTS media (
    message_id  INTEGER,
    chat_id     INTEGER,
    type        TEXT,
    file_id     TEXT,
    file_name   TEXT,
    duration    INTEGER,
    width       INTEGER,
    height      INTEGER,
    PRIMARY KEY (message_id, chat_id)
);

CREATE TABLE IF NOT EXISTS folders (
    id      INTEGER PRIMARY KEY,
    title   TEXT,
    ord     INTEGER DEFAULT 0
);
"""


class Cache:
    def __init__(self):
        self.db: aiosqlite.Connection | None = None

    async def connect(self):
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.db = await aiosqlite.connect(CACHE_FILE)
        self.db.row_factory = aiosqlite.Row
        await self.db.executescript(SCHEMA)
        await self.db.commit()
        log.debug("Cache connected")

    async def close(self):
        if self.db:
            await self.db.close()

    # ── Dialogs ──────────────────────────────────────────────

    async def upsert_dialogs(self, dialogs: list[dict]):
        await self.db.executemany(
            """INSERT INTO dialogs (id, name, username, unread, last_msg, last_date, type, folder_id, pinned)
               VALUES (:id, :name, :username, :unread, :last_msg, :last_date, :type, :folder_id, :pinned)
               ON CONFLICT(id) DO UPDATE SET
                 name=excluded.name, unread=excluded.unread,
                 last_msg=excluded.last_msg, last_date=excluded.last_date,
                 folder_id=excluded.folder_id, pinned=excluded.pinned""",
            dialogs,
        )
        await self.db.commit()

    async def get_dialogs(self, folder_id: int = 0) -> list:
        if folder_id == -1:  # все
            cur = await self.db.execute(
                "SELECT * FROM dialogs ORDER BY pinned DESC, last_date DESC"
            )
        else:
            cur = await self.db.execute(
                "SELECT * FROM dialogs WHERE folder_id=? ORDER BY pinned DESC, last_date DESC",
                (folder_id,),
            )
        return await cur.fetchall()

    # ── Messages ─────────────────────────────────────────────

    async def upsert_messages(self, messages: list[dict]):
        await self.db.executemany(
            """INSERT INTO messages
               (id, chat_id, sender_id, sender_name, text, date, media_type, media_path, reply_to_id, edited, reactions)
               VALUES (:id, :chat_id, :sender_id, :sender_name, :text, :date, :media_type, :media_path, :reply_to_id, :edited, :reactions)
               ON CONFLICT(id, chat_id) DO UPDATE SET
                 text=excluded.text, edited=excluded.edited, reactions=excluded.reactions""",
            messages,
        )
        # Оставляем только последние 200 сообщений на чат
        await self.db.execute(
            """DELETE FROM messages WHERE (id, chat_id) NOT IN (
                 SELECT id, chat_id FROM messages WHERE chat_id=?
                 ORDER BY date DESC LIMIT 200
               )""",
            (messages[0]["chat_id"],) if messages else (0,),
        )
        await self.db.commit()

    async def get_messages(self, chat_id: int, limit: int = 50, offset: int = 0) -> list:
        cur = await self.db.execute(
            "SELECT * FROM messages WHERE chat_id=? ORDER BY date DESC LIMIT ? OFFSET ?",
            (chat_id, limit, offset),
        )
        rows = await cur.fetchall()
        return list(reversed(rows))

    # ── Folders ──────────────────────────────────────────────

    async def upsert_folders(self, folders: list[dict]):
        await self.db.executemany(
            "INSERT INTO folders (id, title, ord) VALUES (:id, :title, :ord) ON CONFLICT(id) DO UPDATE SET title=excluded.title",
            folders,
        )
        await self.db.commit()

    async def get_folders(self) -> list:
        cur = await self.db.execute("SELECT * FROM folders ORDER BY ord")
        return await cur.fetchall()
