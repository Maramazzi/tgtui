"""
Медиа утилиты: определение поддержки kitty, открытие файлов
"""
import os
import sys
import subprocess
from pathlib import Path
from core.logger import get_logger

log = get_logger("media")


def supports_kitty_graphics() -> bool:
    """Проверяем поддерживает ли терминал kitty graphics protocol"""
    term = os.environ.get("TERM", "")
    term_program = os.environ.get("TERM_PROGRAM", "")
    return "kitty" in term or term_program in ("iTerm.app", "WezTerm", "ghostty")


def open_file(path: str):
    """Открываем файл внешним приложением"""
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["xdg-open", path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log.debug(f"open_file error: {e}")


def play_audio(path: str):
    """Воспроизводим аудио через доступный плеер"""
    players = []
    if sys.platform == "darwin":
        players = [["afplay", path], ["mpv", "--no-video", path]]
    else:
        players = [["mpv", "--no-video", path], ["ffplay", "-nodisp", "-autoexit", path]]

    for cmd in players:
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            continue
    log.debug("No audio player found")
    return False


def image_to_ascii(path: str, width: int = 20, height: int = 10) -> str:
    """Конвертируем картинку в ASCII через Pillow"""
    try:
        from PIL import Image
        img = Image.open(path).convert("L")
        img = img.resize((width, height))
        chars = " .:-=+*#%@"
        result = []
        for y in range(height):
            row = ""
            for x in range(width):
                pixel = img.getpixel((x, y))
                row += chars[int(pixel / 256 * len(chars))]
            result.append(row)
        return "\n".join(result)
    except Exception as e:
        log.debug(f"image_to_ascii error: {e}")
        return "[изображение]"
