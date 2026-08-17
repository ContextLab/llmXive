"""
llmXive Automated Science Pipeline - Ceramic Weibull Modulus Prediction.

This package provides the core infrastructure for data ingestion, descriptor
computation, modeling, and reporting.
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure logs directory exists
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

# Setup logging
def setup_logger(name: str, log_file: str = None, level: int = logging.INFO):
    """Configure a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler
    if log_file:
        fh = logging.FileHandler(PROJECT_ROOT / "logs" / log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

logger = setup_logger("llmXive", "pipeline.log")

# Base classes (defined in contracts.schemas)
from contracts.schemas import CeramicEntry, DescriptorSet, ModelResult

__all__ = [
    "CeramicEntry",
    "DescriptorSet",
    "ModelResult",
    "logger",
    "PROJECT_ROOT"
]
