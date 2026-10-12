"""
Simple logging configuration used by the pipeline.
"""

import logging
from llmxive_toolkit import get_logger

def setup_logging(name: str = __name__) -> None:
    """
    Configure a module‑level logger.
    """
    logger = get_logger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s – %(message)s")
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
