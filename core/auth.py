"""
Авторизация через Telethon.
Используется из TUI-экранов, не запрашивает ввод сам —
вместо этого принимает значения и возвращает статус.
"""
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    PasswordHashInvalidError,
    FloodWaitError,
)
from core.config import SESSION_FILE
from core.logger import get_logger

log = get_logger("auth")


async def create_client(api_id: int, api_hash: str) -> TelegramClient:
    client = TelegramClient(str(SESSION_FILE), api_id, api_hash)
    return client


async def is_authorized(client: TelegramClient) -> bool:
    try:
        return await client.is_user_authorized()
    except Exception as e:
        log.debug(f"is_authorized error: {e}")
        return False


async def send_code(client: TelegramClient, phone: str) -> dict:
    """
    Отправляет код на телефон.
    Возвращает {"ok": True, "phone_code_hash": ...} или {"ok": False, "error": ...}
    """
    try:
        await client.connect()
        result = await client.send_code_request(phone)
        return {"ok": True, "phone_code_hash": result.phone_code_hash}
    except FloodWaitError as e:
        return {"ok": False, "error": f"Слишком много попыток. Подожди {e.seconds} сек."}
    except Exception as e:
        log.debug(f"send_code error: {e}")
        return {"ok": False, "error": str(e)}


async def sign_in_with_code(
    client: TelegramClient, phone: str, code: str, phone_code_hash: str
) -> dict:
    """
    Пробуем войти по коду.
    Возвращает:
      {"ok": True}
      {"ok": False, "need_password": True}  — нужна 2FA
      {"ok": False, "error": "..."}
    """
    try:
        await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
        return {"ok": True}
    except SessionPasswordNeededError:
        return {"ok": False, "need_password": True}
    except PhoneCodeInvalidError:
        return {"ok": False, "error": "Неверный код. Попробуй ещё раз."}
    except PhoneCodeExpiredError:
        return {"ok": False, "error": "Код истёк. Запросим новый."}
    except Exception as e:
        log.debug(f"sign_in_with_code error: {e}")
        return {"ok": False, "error": str(e)}


async def sign_in_with_password(client: TelegramClient, password: str) -> dict:
    """2FA пароль"""
    try:
        await client.sign_in(password=password)
        return {"ok": True}
    except PasswordHashInvalidError:
        return {"ok": False, "error": "Неверный пароль."}
    except Exception as e:
        log.debug(f"sign_in_with_password error: {e}")
        return {"ok": False, "error": str(e)}
