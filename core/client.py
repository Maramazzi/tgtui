"""
Обёртка над Telethon — загрузка диалогов, сообщений, отправка и т.д.
"""
from telethon import TelegramClient, events
from telethon.tl.types import (
    User, Chat, Channel,
    MessageMediaPhoto, MessageMediaDocument,
    MessageMediaWebPage,
    DocumentAttributeAudio, DocumentAttributeVideo,
    DocumentAttributeSticker,
)
from telethon.tl.functions.messages import GetDialogFiltersRequest
from datetime import datetime
from core.logger import get_logger

log = get_logger("client")


def _dialog_type(entity) -> str:
    if isinstance(entity, User):
        return "bot" if entity.bot else "user"
    if isinstance(entity, Channel):
        return "channel" if entity.broadcast else "supergroup"
    return "group"


def _media_type(msg) -> str | None:
    if not msg.media:
        return None
    if isinstance(msg.media, MessageMediaPhoto):
        return "photo"
    if isinstance(msg.media, MessageMediaDocument):
        doc = msg.media.document
        for attr in doc.attributes:
            if isinstance(attr, DocumentAttributeAudio):
                return "voice" if attr.voice else "audio"
            if isinstance(attr, DocumentAttributeVideo):
                return "video"
            if isinstance(attr, DocumentAttributeSticker):
                return "sticker"
        return "document"
    if isinstance(msg.media, MessageMediaWebPage):
        return "webpage"
    return "unknown"


class TGClient:
    def __init__(self, client: TelegramClient, cache, config: dict):
        self.tg = client
        self.cache = cache
        self.config = config
        self._me = None
        self._new_message_callbacks = []

    async def start(self):
        await self.tg.connect()
        self._me = await self.tg.get_me()
        log.debug(f"Logged in as {self._me.first_name} id={self._me.id}")
        self._register_handlers()

    async def get_me(self):
        if not self._me:
            self._me = await self.tg.get_me()
        return self._me

    def on_new_message(self, callback):
        """Регистрируем callback для новых сообщений"""
        self._new_message_callbacks.append(callback)

    def _register_handlers(self):
        @self.tg.on(events.NewMessage())
        async def _handler(event):
            for cb in self._new_message_callbacks:
                await cb(event)

    # ── Dialogs ──────────────────────────────────────────────

    async def load_dialogs(self) -> list[dict]:
        """Загружаем диалоги и сохраняем в кэш"""
        dialogs_raw = await self.tg.get_dialogs(limit=100)
        result = []
        for d in dialogs_raw:
            entity = d.entity
            last_msg = ""
            if d.message:
                last_msg = d.message.text or f"[{_media_type(d.message) or 'медиа'}]"

            result.append({
                "id": d.id,
                "name": d.name or "Без имени",
                "username": getattr(entity, "username", None) or "",
                "unread": d.unread_count,
                "last_msg": last_msg[:100],
                "last_date": d.date.isoformat() if d.date else "",
                "type": _dialog_type(entity),
                "folder_id": 0,
                "pinned": 1 if d.pinned else 0,
            })

        await self.cache.upsert_dialogs(result)
        return result

    # ── Folders ──────────────────────────────────────────────

    async def load_folders(self) -> list[dict]:
        try:
            result = await self.tg(GetDialogFiltersRequest())
            folders = []
            for i, f in enumerate(result.filters):
                if hasattr(f, "title"):
                    folders.append({"id": f.id, "title": f.title, "ord": i})
            await self.cache.upsert_folders(folders)
            return folders
        except Exception as e:
            log.debug(f"load_folders error: {e}")
            return []

    # ── Messages ─────────────────────────────────────────────

    async def load_messages(self, chat_id: int, limit: int = 50, offset_id: int = 0) -> list[dict]:
        messages_raw = await self.tg.get_messages(chat_id, limit=limit, offset_id=offset_id)
        result = []
        for msg in messages_raw:
            sender_name = ""
            if msg.sender:
                s = msg.sender
                sender_name = getattr(s, "first_name", "") or getattr(s, "title", "") or ""

            result.append({
                "id": msg.id,
                "chat_id": chat_id,
                "sender_id": msg.sender_id or 0,
                "sender_name": sender_name,
                "text": msg.text or "",
                "date": msg.date.isoformat(),
                "media_type": _media_type(msg),
                "media_path": None,
                "reply_to_id": msg.reply_to_msg_id if msg.is_reply else None,
                "edited": 1 if msg.edit_date else 0,
                "reactions": None,
            })

        if result:
            await self.cache.upsert_messages(result)
        return list(reversed(result))

    # ── Send / Edit / Delete ─────────────────────────────────

    async def send_message(self, chat_id: int, text: str, reply_to: int = None):
        return await self.tg.send_message(chat_id, text, reply_to=reply_to)

    async def edit_message(self, chat_id: int, message_id: int, text: str):
        return await self.tg.edit_message(chat_id, message_id, text)

    async def delete_message(self, chat_id: int, message_id: int, revoke: bool = True):
        await self.tg.delete_messages(chat_id, [message_id], revoke=revoke)

    async def send_file(self, chat_id: int, path: str, caption: str = ""):
        return await self.tg.send_file(chat_id, path, caption=caption)

    async def send_typing(self, chat_id: int):
        if self.config["behavior"].get("send_typing"):
            from telethon.tl.types import SendMessageTypingAction
            await self.tg(
                __import__("telethon.tl.functions.messages", fromlist=["SetTypingRequest"])
                .SetTypingRequest(peer=chat_id, action=SendMessageTypingAction())
            )

    async def mark_read(self, chat_id: int):
        await self.tg.send_read_acknowledge(chat_id)

    async def download_media(self, message, path: str = None) -> str | None:
        try:
            result = await self.tg.download_media(message, file=path)
            return str(result) if result else None
        except Exception as e:
            log.debug(f"download_media error: {e}")
            return None
