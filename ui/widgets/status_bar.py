"""
Нижняя строка: горячие клавиши + статус сети
"""
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Label
from textual.containers import Horizontal


HINTS = {
    "main": "^Q Выход  ←→ Панели  R Ответить  E Изменить  D Удалить  ^F Поиск  F1 ?",
    "auth": "^Q Выход  Enter Подтвердить",
    "onboarding": "^Q Выход  Enter Продолжить",
}


class StatusBar(Widget):
    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        dock: bottom;
        background: $primary;
    }
    StatusBar Horizontal {
        height: 1;
    }
    #hints {
        color: $background;
        width: 1fr;
        content-align: left middle;
        padding-left: 1;
    }
    #connection {
        color: $background;
        width: auto;
        content-align: right middle;
        padding-right: 1;
    }
    """

    def __init__(self, mode: str = "main"):
        super().__init__()
        self._mode = mode
        self._connected = True

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(HINTS.get(self._mode, ""), id="hints")
            yield Label("● онлайн", id="connection")

    def set_connected(self, connected: bool):
        self._connected = connected
        label = self.query_one("#connection", Label)
        if connected:
            label.update("● онлайн")
            label.remove_class("offline")
        else:
            label.update("○ нет сети")
            label.add_class("offline")

    def set_hints(self, mode: str):
        self._mode = mode
        self.query_one("#hints", Label).update(HINTS.get(mode, ""))
