"""
Правая панель: сообщения
"""
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, ListView, ListItem, RichLog
from textual.containers import Vertical, ScrollableContainer
from textual.binding import Binding
from textual.message import Message
from datetime import datetime


MEDIA_ICONS = {
    "photo": "🖼",
    "voice": "🎤",
    "audio": "🎵",
    "video": "📹",
    "sticker": "🎭",
    "document": "📄",
    "webpage": "🔗",
}


class MessageView(Widget):

    BINDINGS = [
        Binding("up", "scroll_up", show=False),
        Binding("down", "scroll_down", show=False),
        Binding("r", "reply", "Ответить"),
        Binding("e", "edit", "Изменить"),
        Binding("d", "delete", "Удалить"),
        Binding("y", "yank", "Копировать"),
        Binding("s", "save_media", "Скачать"),
        Binding("pageup", "page_up", show=False),
        Binding("pagedown", "page_down", show=False),
    ]

    DEFAULT_CSS = """
    MessageView {
        width: 1fr;
    }
    #chat_header {
        height: 1;
        background: $primary-darken-2;
        padding: 0 1;
        color: $text;
    }
    #msg_scroll {
        height: 1fr;
        padding: 0 1;
    }
    #typing_label {
        height: 1;
        color: $text-muted;
        padding: 0 1;
    }
    .msg-mine {
        text-align: right;
        color: $success;
    }
    .msg-other {
        color: $text;
    }
    .msg-system {
        text-align: center;
        color: $text-muted;
    }
    .msg-selected {
        background: $primary-darken-3;
    }
    """

    class ReplyRequested(Message):
        def __init__(self, msg_id: int, text: str):
            super().__init__()
            self.msg_id = msg_id
            self.text = text

    class EditRequested(Message):
        def __init__(self, msg_id: int, text: str):
            super().__init__()
            self.msg_id = msg_id
            self.text = text

    class DeleteRequested(Message):
        def __init__(self, msg_id: int):
            super().__init__()
            self.msg_id = msg_id

    class LoadMore(Message):
        pass

    def __init__(self):
        super().__init__()
        self._messages = []
        self._my_id = None
        self._chat_name = ""
        self._chat_type = ""
        self._selected_idx = -1

    def compose(self) -> ComposeResult:
        yield Label("", id="chat_header")
        yield ScrollableContainer(
            ListView(id="msg_list"),
            id="msg_scroll"
        )
        yield Label("", id="typing_label")

    def set_chat(self, name: str, chat_type: str, my_id: int):
        self._chat_name = name
        self._chat_type = chat_type
        self._my_id = my_id
        header = self.query_one("#chat_header", Label)
        ro = " [только чтение]" if chat_type == "channel" else ""
        header.update(f" {name}{ro}")

    def load_messages(self, messages: list):
        self._messages = messages
        self._render()

    def append_message(self, msg: dict):
        self._messages.append(msg)
        self._render()
        # Скролл вниз при новом сообщении
        self.query_one("#msg_scroll", ScrollableContainer).scroll_end(animate=False)

    def _render(self):
        lv = self.query_one("#msg_list", ListView)
        lv.clear()

        for i, msg in enumerate(self._messages):
            text = self._format_msg(msg)
            is_mine = msg["sender_id"] == self._my_id
            item = ListItem(Label(text), id=f"msg_{msg['id']}")
            item._msg_data = msg
            item._is_mine = is_mine
            if is_mine:
                item.add_class("msg-mine")
            lv.append(item)

        self.query_one("#msg_scroll", ScrollableContainer).scroll_end(animate=False)

    def _format_msg(self, msg: dict) -> str:
        time_str = ""
        if msg.get("date"):
            try:
                dt = datetime.fromisoformat(msg["date"])
                time_str = dt.strftime("%H:%M")
            except Exception:
                pass

        sender = msg.get("sender_name", "")
        text = msg.get("text", "")
        media = msg.get("media_type")
        edited = " ✎" if msg.get("edited") else ""

        # Медиа
        if media and media != "webpage":
            icon = MEDIA_ICONS.get(media, "📎")
            media_str = f" {icon} [{media}]"
        else:
            media_str = ""

        # Reply
        reply_str = ""
        if msg.get("reply_to_id"):
            reply_str = "↩ "

        is_mine = msg["sender_id"] == self._my_id
        if is_mine:
            return f"{reply_str}{text}{media_str}{edited}  {time_str}"
        else:
            name_part = f"{sender}: " if sender else ""
            return f"{time_str}  {reply_str}{name_part}{text}{media_str}{edited}"

    def set_typing(self, name: str, typing: bool):
        label = self.query_one("#typing_label", Label)
        label.update(f"{name} печатает..." if typing else "")

    def action_reply(self):
        lv = self.query_one("#msg_list", ListView)
        if lv.highlighted_child and hasattr(lv.highlighted_child, "_msg_data"):
            msg = lv.highlighted_child._msg_data
            self.post_message(self.ReplyRequested(msg["id"], msg.get("text", "")))

    def action_edit(self):
        lv = self.query_one("#msg_list", ListView)
        if lv.highlighted_child and hasattr(lv.highlighted_child, "_msg_data"):
            msg = lv.highlighted_child._msg_data
            if msg["sender_id"] == self._my_id:
                self.post_message(self.EditRequested(msg["id"], msg.get("text", "")))

    def action_delete(self):
        lv = self.query_one("#msg_list", ListView)
        if lv.highlighted_child and hasattr(lv.highlighted_child, "_msg_data"):
            msg = lv.highlighted_child._msg_data
            self.post_message(self.DeleteRequested(msg["id"]))

    def action_yank(self):
        lv = self.query_one("#msg_list", ListView)
        if lv.highlighted_child and hasattr(lv.highlighted_child, "_msg_data"):
            text = lv.highlighted_child._msg_data.get("text", "")
            try:
                import pyperclip
                pyperclip.copy(text)
            except Exception:
                pass

    def action_save_media(self):
        pass  # реализуем в этапе 5

    def action_scroll_up(self):
        lv = self.query_one("#msg_list", ListView)
        if lv.index == 0:
            self.post_message(self.LoadMore())
        lv.action_cursor_up()

    def action_scroll_down(self):
        self.query_one("#msg_list", ListView).action_cursor_down()

    def action_page_up(self):
        sc = self.query_one("#msg_scroll", ScrollableContainer)
        sc.scroll_page_up()

    def action_page_down(self):
        sc = self.query_one("#msg_scroll", ScrollableContainer)
        sc.scroll_page_down()
