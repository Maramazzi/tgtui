"""
Главный экран: чаты + сообщения
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Horizontal
from textual.binding import Binding
from textual.widgets import Label

from ui.widgets.chat_list import ChatList
from ui.widgets.message_view import MessageView
from ui.widgets.input_bar import InputBar
from ui.widgets.status_bar import StatusBar


class MainScreen(Screen):

    BINDINGS = [
        Binding("ctrl+q", "app.quit", "Выход"),
        Binding("ctrl+f", "search", "Поиск"),
        Binding("tab", "switch_panel", "Переключить панель"),
        Binding("left", "focus_chats", show=False),
        Binding("right", "focus_messages", show=False),
        Binding("f1", "show_help", "Помощь"),
    ]

    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
    }
    #main_row {
        height: 1fr;
        layout: horizontal;
    }
    """

    def __init__(self, tg_client, cache, config):
        super().__init__()
        self.tg_client = tg_client
        self.cache = cache
        self.config = config
        self._current_chat_id = None
        self._current_chat_type = ""
        self._panel = "chats"  # chats | messages

    def compose(self) -> ComposeResult:
        with Horizontal(id="main_row"):
            yield ChatList()
            yield MessageView()
        yield InputBar()
        yield StatusBar(mode="main")

    async def on_mount(self):
        await self._load_data()
        self.tg_client.on_new_message(self._on_new_message)

    async def _load_data(self):
        dialogs = await self.tg_client.load_dialogs()
        folders = await self.tg_client.load_folders()
        self.query_one(ChatList).load_dialogs(
            [dict(d) for d in dialogs] if not isinstance(dialogs[0], dict) else dialogs,
            [dict(f) for f in folders] if folders and not isinstance(folders[0], dict) else folders,
        )

    # ── Chat selected ────────────────────────────────────────

    async def on_chat_list_chat_selected(self, event: ChatList.ChatSelected):
        self._current_chat_id = event.chat_id
        self._current_chat_type = event.chat_type
        mv = self.query_one(MessageView)
        me = await self.tg_client.get_me()
        mv.set_chat(event.chat_name, event.chat_type, me.id)

        messages = await self.tg_client.load_messages(event.chat_id)
        mv.load_messages(messages)
        await self.tg_client.mark_read(event.chat_id)

        # Показываем/скрываем поле ввода для каналов
        ib = self.query_one(InputBar)
        ib.display = True
        if event.chat_type == "channel":
            ib.display = False

        self.action_focus_messages()

    # ── Messages actions ─────────────────────────────────────

    async def on_message_view_reply_requested(self, event: MessageView.ReplyRequested):
        ib = self.query_one(InputBar)
        ib.set_reply(event.msg_id, event.text)
        ib.focus_input()

    async def on_message_view_edit_requested(self, event: MessageView.EditRequested):
        ib = self.query_one(InputBar)
        ib.set_edit(event.msg_id, event.text)
        ib.focus_input()

    async def on_message_view_delete_requested(self, event: MessageView.DeleteRequested):
        if self._current_chat_id:
            await self.tg_client.delete_message(self._current_chat_id, event.msg_id)

    async def on_message_view_load_more(self, _):
        if not self._current_chat_id:
            return
        mv = self.query_one(MessageView)
        if mv._messages:
            oldest_id = mv._messages[0]["id"]
            more = await self.tg_client.load_messages(
                self._current_chat_id, offset_id=oldest_id
            )
            mv._messages = more + mv._messages
            mv._render()

    # ── Input bar ────────────────────────────────────────────

    async def on_input_bar_message_sent(self, event: InputBar.MessageSent):
        if not self._current_chat_id:
            return
        if event.edit_id:
            await self.tg_client.edit_message(
                self._current_chat_id, event.edit_id, event.text
            )
        else:
            await self.tg_client.send_message(
                self._current_chat_id, event.text, reply_to=event.reply_to
            )

    async def on_input_bar_typing_started(self, _):
        if self._current_chat_id:
            await self.tg_client.send_typing(self._current_chat_id)

    # ── New messages (realtime) ──────────────────────────────

    async def _on_new_message(self, event):
        msg = event.message
        if self._current_chat_id and msg.peer_id and hasattr(msg.peer_id, "user_id"):
            if msg.peer_id.user_id == self._current_chat_id or msg.chat_id == self._current_chat_id:
                sender_name = ""
                if msg.sender:
                    sender_name = getattr(msg.sender, "first_name", "") or ""
                self.query_one(MessageView).append_message({
                    "id": msg.id,
                    "chat_id": self._current_chat_id,
                    "sender_id": msg.sender_id or 0,
                    "sender_name": sender_name,
                    "text": msg.text or "",
                    "date": msg.date.isoformat(),
                    "media_type": None,
                    "reply_to_id": None,
                    "edited": 0,
                    "reactions": None,
                })

    # ── Panel switching ──────────────────────────────────────

    def action_switch_panel(self):
        if self._panel == "chats":
            self.action_focus_messages()
        else:
            self.action_focus_chats()

    def action_focus_chats(self):
        self._panel = "chats"
        self.query_one(ChatList).focus()

    def action_focus_messages(self):
        self._panel = "messages"
        self.query_one(MessageView).focus()

    def action_search(self):
        # этап 6
        pass

    def action_show_help(self):
        # этап 7
        pass
