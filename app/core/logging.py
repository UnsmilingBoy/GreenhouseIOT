"""Single place to configure logging.

Why: every module does `logger = logging.getLogger(__name__)` and
automatically respects APP_ENV / LOG_LEVEL. No print() in prod code.
"""

import logging
import sys

_configured = False


def configure_logging(level: str = "INFO") -> None:
    global _configured
    if _configured:
        return
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        stream=sys.stdout,
        force=True,
    )
    _configured = True
