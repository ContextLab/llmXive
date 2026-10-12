"""
Minimal logging configuration helper.

``setup_logging`` returns a logger object.  It accepts an optional ``name``
argument; if omitted the root logger is configured.
"""

import logging
import sys

def setup_logging(name: str = None):
    logger = logging.getLogger(name) if name else logging.getLogger()
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
