"""Logging configuration — provides a factory that returns named loggers with file and console handlers."""

import logging
import os
from logging.handlers import RotatingFileHandler

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "trading_bot.log")

_FILE_FORMAT = "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s"
_CONSOLE_FORMAT = "%(levelname)-5s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 3

# Third-party loggers that produce noise at DEBUG/INFO level
_SILENT_LOGGERS = ("urllib3", "urllib3.connectionpool", "binance")

_configured = False


def _configure_root() -> None:
    """Set up file and console handlers on the root logger (idempotent)."""
    global _configured
    if _configured:
        return

    os.makedirs(_LOG_DIR, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(_FILE_FORMAT, datefmt=_DATE_FORMAT)

    # --- File handler (INFO, rotating) ---
    file_handler = RotatingFileHandler(
        _LOG_FILE,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # --- Console handler (INFO) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT, datefmt=_DATE_FORMAT))

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Silence noisy third-party loggers
    for name in _SILENT_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger backed by rotating file and console handlers.

    Args:
        name: Logger name — typically ``__name__`` of the calling module.

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    _configure_root()
    return logging.getLogger(name)
