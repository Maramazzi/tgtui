"""
Управление конфигурацией ~/.config/tgtui/config.toml
"""
import os
import toml
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "tgtui"
CONFIG_FILE = CONFIG_DIR / "config.toml"
SESSION_FILE = CONFIG_DIR / "session"
DOWNLOADS_DIR = CONFIG_DIR / "downloads"
CACHE_FILE = CONFIG_DIR / "cache.db"
LOG_FILE = CONFIG_DIR / "debug.log"

DEFAULT_CONFIG = {
    "app": {
        "api_id": "",
        "api_hash": "",
        "theme": "dark",          # dark | light | no_color
        "language": "ru",
    },
    "behavior": {
        "send_typing": True,       # отправлять статус "печатает"
        "notify": True,            # системные уведомления
        "media_auto_preview": True,
        "download_dir": str(DOWNLOADS_DIR),
        "messages_per_page": 50,
    },
}


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_config_dir()
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = toml.load(f)
    # Мёрджим с дефолтами на случай новых ключей
    merged = DEFAULT_CONFIG.copy()
    for section, values in data.items():
        if section in merged:
            merged[section].update(values)
        else:
            merged[section] = values
    return merged


def save_config(config: dict):
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        toml.dump(config, f)


def is_configured(config: dict) -> bool:
    """Проверяем есть ли api_id и api_hash"""
    return bool(config["app"].get("api_id")) and bool(config["app"].get("api_hash"))
