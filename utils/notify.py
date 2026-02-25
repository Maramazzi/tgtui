"""
Системные уведомления: Linux (notify-send) и macOS (osascript)
"""
import sys
import subprocess
from core.logger import get_logger

log = get_logger("notify")


def send_notification(title: str, body: str):
    try:
        if sys.platform == "darwin":
            script = f'display notification "{body}" with title "{title}"'
            subprocess.Popen(["osascript", "-e", script],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform.startswith("linux"):
            subprocess.Popen(["notify-send", title, body],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        log.debug("notify tool not found")
    except Exception as e:
        log.debug(f"notify error: {e}")
