"""
Левая панель: список чатов с папками
"""
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, ListView, ListItem
from textual.containers import Vertical
from textual.binding import Binding
from textual.message import Message
from textual.reactive import reactive


FOLDER_ALL = {"id": -1, "title": "Все"}
FOLDER_ARCHIVE = {"id": 1, "title": "Архив"}


class ChatList(Widget):

    BINDINGS = [
        Binding("up", "cursor_up", show=False),
        Binding("down", "cursor_down", show=False),
        Binding("]", "next_folder", "Следующая папка"),
        Binding("[", "prev_folder", "Предыдущая папка"),
    ]

    DEFAULT_CSS = """
    ChatList {
        width: 28;
        border-right: solid $primary-darken-2;
    }
    #folder_bar {
        height: 1;
        background: $primary-darken-3;
        color: $text;
        padding: 0 1;
        overflow: hidden;
    }
    #chat_list_view {
        height: 1fr;
    }
    .chat-item {
        height: 3;
        padding: 0 1;
    }
    .chat-name {
        text-style: bold;
    }
    .chat-last {
        color: $text-muted;
    }
    .chat-unread {
        color: $success;
        text-style: bold;
    }
    """

    class ChatSelected(Message):
        def __init__(self, chat_id: int, chat_name: str, chat_type: str):
            super().__init__()
            self.chat_id = chat_id
            self.chat_name = chat_name
            self.chat_type = chat_type

    def __init__(self):
        super().__init__()
        self._dialogs = []
        self._folders = [FOLDER_ALL]
        self._folder_idx = 0

    def compose(self) -> ComposeResult:
        yield Label("Все", id="folder_bar")
        yield ListView(id="chat_list_view")

    def load_dialogs(self, dialogs: list, folders: list):
        self._dialogs = dialogs
        self._folders = [FOLDER_ALL] + folders + [FOLDER_ARCHIVE]
        self._render_dialogs()

    def _current_folder_id(self) -> int:
        return self._folders[self._folder_idx]["id"]

    def _render_dialogs(self):
        lv = self.query_one("#chat_list_view", ListView)
        folder_bar = self.query_one("#folder_bar", Label)

        folder = self._folders[self._folder_idx]
        folder_bar.update(
            "  ".join(
                f"[{f['title']}]" if i == self._folder_idx else f['title']
                for i, f in enumerate(self._folders)
            )
        )

        lv.clear()
        fid = folder["id"]

        for d in self._dialogs:
            # фильтрация по папке
            if fid == -1:
                pass  # все
            elif fid == 1 and d["folder_id"] != 1:
                continue
            elif fid not in (-1, 1) and d["folder_id"] != fid:
                continue

            name = d["name"] or "Без имени"
            last = (d["last_msg"] or "")[:25]
            unread = d["unread"] or 0

            unread_str = f" {unread}" if unread else ""
            label_text = f"{name[:20]}{unread_str}\n{last}"

            item = ListItem(Label(label_text), id=f"chat_{d['id']}")
            item._chat_data = dict(d)
            lv.append(item)

    def action_next_folder(self):
        self._folder_idx = (self._folder_idx + 1) % len(self._folders)
        self._render_dialogs()

    def action_prev_folder(self):
        self._folder_idx = (self._folder_idx - 1) % len(self._folders)
        self._render_dialogs()

    def action_cursor_up(self):
        self.query_one("#chat_list_view", ListView).action_cursor_up()

    def action_cursor_down(self):
        self.query_one("#chat_list_view", ListView).action_cursor_down()

    def on_list_view_selected(self, event: ListView.Selected):
        item = event.item
        if hasattr(item, "_chat_data"):
            d = item._chat_data
            self.post_message(self.ChatSelected(d["id"], d["name"], d["type"]))
