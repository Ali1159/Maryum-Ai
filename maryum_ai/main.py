from __future__ import annotations

import logging

from .config import ConfigError, load_config
from .logging_utils import setup_logging


def main() -> int:
    setup_logging()
    try:
        config = load_config()
    except ConfigError as exc:
        logging.error(str(exc))
        return 2

    try:
        from .gui import run_gui
    except ModuleNotFoundError as exc:
        logging.error(
            "Missing GUI dependency (%s). Install GTK/PyGObject and retry.", exc.name
        )
        return 3

    run_gui(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
