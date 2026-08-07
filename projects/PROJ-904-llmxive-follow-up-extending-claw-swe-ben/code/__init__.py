"""
llmXive Follow-up: Context Fidelity vs. Model Scaling Trade-offs
"""
import logging
from pathlib import Path

# Configure root logger for the package
def _setup_logger() -> logging.Logger:
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = _setup_logger()
