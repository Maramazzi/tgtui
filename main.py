#!/usr/bin/env python3
"""
tgtui — точка входа
Использование:
  tgtui           — запуск
  tgtui --debug   — с логом в ~/.config/tgtui/debug.log
  tgtui --theme light|dark|no_color
"""
import sys
import asyncio


def parse_args():
    args = sys.argv[1:]
    debug = "--debug" in args
    theme = "dark"
    if "--theme" in args:
        idx = args.index("--theme")
        if idx + 1 < len(args):
            theme = args[idx + 1]
    return debug, theme


def run():
    debug, theme = parse_args()

    from core.logger import setup_logging
    setup_logging(debug)

    from ui.app import TgTuiApp
    app = TgTuiApp(theme_name=theme)
    app.run()


if __name__ == "__main__":
    run()
