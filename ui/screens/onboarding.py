"""
Экран первого запуска — ввод API_ID и API_HASH
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Input, Button, Static
from textual.containers import Container, Vertical
from textual.binding import Binding


HELP_TEXT = """Для работы нужны API ключи Telegram.

1. Открой https://my.telegram.org
2. Войди под своим номером телефона  
3. Перейди в «API development tools»
4. Создай приложение
5. Скопируй api_id и api_hash сюда"""


class OnboardingScreen(Screen):
    """Первый запуск: ввод api_id и api_hash"""

    BINDINGS = [
        Binding("ctrl+q", "app.quit", "Выход"),
    ]

    CSS = """
    OnboardingScreen {
        align: center middle;
    }
    #box {
        width: 60;
        height: auto;
        border: solid $primary;
        padding: 1 2;
    }
    #title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    #help {
        color: $text-muted;
        margin-bottom: 1;
    }
    Input {
        margin-bottom: 1;
    }
    #error {
        color: $error;
        height: 1;
    }
    Button {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="box"):
            yield Label("tgtui — настройка API", id="title")
            yield Static(HELP_TEXT, id="help")
            yield Input(placeholder="api_id (только цифры)", id="api_id")
            yield Input(placeholder="api_hash", id="api_hash")
            yield Label("", id="error")
            yield Button("Продолжить →", id="submit", variant="primary")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "submit":
            self._submit()

    def on_input_submitted(self, event: Input.Submitted):
        self._submit()

    def _submit(self):
        api_id_val = self.query_one("#api_id", Input).value.strip()
        api_hash_val = self.query_one("#api_hash", Input).value.strip()
        error = self.query_one("#error", Label)

        if not api_id_val.isdigit():
            error.update("api_id должен состоять только из цифр")
            return
        if len(api_hash_val) < 10:
            error.update("api_hash слишком короткий")
            return

        # Сохраняем и переходим дальше
        from core.config import load_config, save_config
        config = load_config()
        config["app"]["api_id"] = api_id_val
        config["app"]["api_hash"] = api_hash_val
        save_config(config)

        self.app.post_message(self.app.ConfigSaved(int(api_id_val), api_hash_val))
