"""
Поле ввода сообщения с поддержкой reply / edit режимов
"""
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label, TextArea
from textual.containers import Vertical
from textual.binding import Binding
from textual.message import Message


class InputBar(Widget):

    BINDINGS = [
        Binding("escape", "cancel", "Отмена"),
        Binding("ctrl+s", "send", "Отправить"),  # доп вариант
    ]

    DEFAULT_CSS = """
    InputBar {
        height: auto;
        max-height: 6;
        border-top: solid $primary-darken-2;
    }
    #reply_bar {
        height: 1;
        color: $text-muted;
        background: $primary-darken-3;
        padding: 0 1;
        display: none;
    }
    #reply_bar.visible {
        display: block;
    }
    #input_area {
        height: auto;
        min-height: 1;
        max-height: 4;
        border: none;
        background: $background;
        padding: 0 1;
    }
    """

    class MessageSent(Message):
        def __init__(self, text: str, reply_to: int | None = None, edit_id: int | None = None):
            super().__init__()
            self.text = text
            self.reply_to = reply_to
            self.edit_id = edit_id

    class TypingStarted(Message):
        pass

    def __init__(self, readonly: bool = False):
        super().__init__()
        self._readonly = readonly
        self._reply_to: int | None = None
        self._reply_text: str = ""
        self._edit_id: int | None = None

    def compose(self) -> ComposeResult:
        yield Label("", id="reply_bar")
        if not self._readonly:
            yield TextArea(id="input_area")
        else:
            yield Label("  [только чтение — канал]", id="input_area")

    def set_reply(self, msg_id: int, text: str):
        self._reply_to = msg_id
        self._reply_text = text
        self._edit_id = None
        bar = self.query_one("#reply_bar", Label)
        bar.update(f"↩ Ответ: {text[:60]}")
        bar.add_class("visible")
        if not self._readonly:
            self.query_one("#input_area", TextArea).focus()

    def set_edit(self, msg_id: int, text: str):
        self._edit_id = msg_id
        self._reply_to = None
        bar = self.query_one("#reply_bar", Label)
        bar.update(f"✎ Редактирование: {text[:60]}")
        bar.add_class("visible")
        if not self._readonly:
            ta = self.query_one("#input_area", TextArea)
            ta.load_text(text)
            ta.focus()

    def clear_mode(self):
        self._reply_to = None
        self._edit_id = None
        self._reply_text = ""
        bar = self.query_one("#reply_bar", Label)
        bar.update("")
        bar.remove_class("visible")
        if not self._readonly:
            self.query_one("#input_area", TextArea).load_text("")

    def action_cancel(self):
        self.clear_mode()

    def on_text_area_changed(self, event: TextArea.Changed):
        self.post_message(self.TypingStarted())

    def on_key(self, event):
        if event.key == "enter" and not event.key == "shift+enter":
            if not self._readonly:
                ta = self.query_one("#input_area", TextArea)
                text = ta.text.strip()
                if text:
                    self.post_message(
                        self.MessageSent(text, self.reply_to, self.edit_id)
                    )
                    self.clear_mode()
                event.prevent_default()

    @property
    def reply_to(self):
        return self._reply_to

    @property
    def edit_id(self):
        return self._edit_id

    def focus_input(self):
        if not self._readonly:
            self.query_one("#input_area", TextArea).focus()
