"""
Directory Setup Utility.
"""
import os
import sys
import logging
from utils import get_logger

logger = get_logger(__name__)

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)
    logger.info(f"Ensured directory: {path}")

def main() -> None:
    dirs = [
        "data/raw",
        "data/processed",
        "results/statistics",
        "results/plots",
        "results/sensitivity",
        "results/methodology"
    ]
    for d in dirs:
        ensure_dir(d)
