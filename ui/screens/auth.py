"""
Экран авторизации: телефон → код → (2FA пароль)
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Input, Button, LoadingIndicator
from textual.containers import Container
from textual.binding import Binding
from textual.message import Message


class AuthScreen(Screen):
    """Логин через номер телефона"""

    BINDINGS = [
        Binding("ctrl+q", "app.quit", "Выход"),
    ]

    CSS = """
    AuthScreen {
        align: center middle;
    }
    #box {
        width: 56;
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
    #hint {
        color: $text-muted;
        margin-bottom: 1;
    }
    Input { margin-bottom: 1; }
    #error { color: $error; height: 1; }
    Button { width: 100%; }
    LoadingIndicator { height: 1; }
    """

    class AuthSuccess(Message):
        pass

    def __init__(self, tg_client):
        super().__init__()
        self.tg_client = tg_client
        self._phone = ""
        self._phone_code_hash = ""
        self._stage = "phone"  # phone | code | password

    def compose(self) -> ComposeResult:
        with Container(id="box"):
            yield Label("tgtui — Вход", id="title")
            yield Label("Введите номер телефона (с кодом страны):", id="hint")
            yield Input(placeholder="+79991234567", id="input_field")
            yield Label("", id="error")
            yield Button("Отправить код →", id="submit", variant="primary")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "submit":
            self.run_worker(self._handle_submit(), exclusive=True)

    def on_input_submitted(self, _):
        self.run_worker(self._handle_submit(), exclusive=True)

    async def _handle_submit(self):
        field = self.query_one("#input_field", Input)
        error = self.query_one("#error", Label)
        btn = self.query_one("#submit", Button)
        value = field.value.strip()
        error.update("")
        btn.disabled = True

        if self._stage == "phone":
            await self._do_phone(value, field, error, btn)
        elif self._stage == "code":
            await self._do_code(value, field, error, btn)
        elif self._stage == "password":
            await self._do_password(value, field, error, btn)

        btn.disabled = False

    async def _do_phone(self, phone, field, error, btn):
        from core.auth import send_code
        if not phone.startswith("+"):
            error.update("Номер должен начинаться с +")
            return
        result = await send_code(self.tg_client, phone)
        if result["ok"]:
            self._phone = phone
            self._phone_code_hash = result["phone_code_hash"]
            self._stage = "code"
            self.query_one("#hint", Label).update(
                f"Код отправлен на {phone}.\nВведите код из Telegram:"
            )
            field.value = ""
            field.placeholder = "12345"
            btn.label = "Войти →"
        else:
            error.update(result["error"])

    async def _do_code(self, code, field, error, btn):
        from core.auth import sign_in_with_code
        result = await sign_in_with_code(
            self.tg_client, self._phone, code, self._phone_code_hash
        )
        if result["ok"]:
            self.post_message(self.AuthSuccess())
        elif result.get("need_password"):
            self._stage = "password"
            self.query_one("#hint", Label).update(
                "Включена двухфакторная аутентификация.\nВведите пароль:"
            )
            field.value = ""
            field.placeholder = "пароль"
            field.password = True
            btn.label = "Войти →"
        else:
            error.update(result["error"])

    async def _do_password(self, password, field, error, btn):
        from core.auth import sign_in_with_password
        result = await sign_in_with_password(self.tg_client, password)
        if result["ok"]:
            self.post_message(self.AuthSuccess())
        else:
            error.update(result["error"])
