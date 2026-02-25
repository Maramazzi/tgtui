"""
Главный Textual App — точка входа TUI
"""
from textual.app import App, ComposeResult
from textual.message import Message

from ui.screens.onboarding import OnboardingScreen
from ui.screens.auth import AuthScreen
from ui.screens.main import MainScreen
from core.config import load_config, is_configured
from core.cache import Cache
from core.logger import get_logger

log = get_logger("app")


class TgTuiApp(App):
    """Главное приложение"""

    TITLE = "tgtui"

    CSS = """
    Screen {
        background: $background;
    }
    """

    class ConfigSaved(Message):
        def __init__(self, api_id: int, api_hash: str):
            super().__init__()
            self.api_id = api_id
            self.api_hash = api_hash

    def __init__(self, theme_name: str = "dark"):
        super().__init__()
        self.config = load_config()
        self.cache = Cache()
        self._tg_client = None
        self._theme_name = theme_name

    async def on_mount(self):
        await self.cache.connect()

        if not is_configured(self.config):
            await self.push_screen(OnboardingScreen())
        else:
            await self._start_telegram()

    async def _start_telegram(self):
        from core.auth import create_client, is_authorized
        api_id = int(self.config["app"]["api_id"])
        api_hash = self.config["app"]["api_hash"]

        tg = await create_client(api_id, api_hash)

        if await is_authorized(tg):
            await self._launch_main(tg)
        else:
            auth_screen = AuthScreen(tg)
            await self.push_screen(auth_screen)

    async def _launch_main(self, tg):
        from core.client import TGClient
        self._tg_client = TGClient(tg, self.cache, self.config)
        await self._tg_client.start()
        await self.switch_screen(MainScreen(self._tg_client, self.cache, self.config))

    # ── Message handlers ─────────────────────────────────────

    async def on_tg_tui_app_config_saved(self, event: ConfigSaved):
        self.config["app"]["api_id"] = str(event.api_id)
        self.config["app"]["api_hash"] = event.api_hash
        await self.pop_screen()
        await self._start_telegram()

    async def on_auth_screen_auth_success(self, event: AuthScreen.AuthSuccess):
        tg = self.screen.tg_client
        await self.pop_screen()
        await self._launch_main(tg)

    async def on_unmount(self):
        await self.cache.close()
        if self._tg_client:
            await self._tg_client.tg.disconnect()
