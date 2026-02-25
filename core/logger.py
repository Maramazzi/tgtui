"""
Логирование. Активируется флагом --debug
"""
import logging
import sys
from pathlib import Path
from core.config import LOG_FILE

_logger = logging.getLogger("tgtui")
_debug_enabled = False


def setup_logging(debug: bool = False):
    global _debug_enabled
    _debug_enabled = debug

    level = logging.DEBUG if debug else logging.WARNING
    _logger.setLevel(level)

    if debug:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        fh.setFormatter(fmt)
        _logger.addHandler(fh)


def get_logger(name: str = "tgtui") -> logging.Logger:
    return logging.getLogger(name)
