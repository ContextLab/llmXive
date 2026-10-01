import logging
import os
import sys
from pathlib import Path
from typing import Optional
import json
import datetime

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure logging handlers."""
    logger = logging.getLogger()
    logger.setLevel(log_level)

    if logger.handlers:
        logger.handlers.clear()

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler for derivation logs
    log_dir = Path("data/derivation_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_dir / "pipeline.log")
    fh.setLevel(log_level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

def write_skipped_record_jsonl(record: dict, log_path: str):
    """Write a record to JSONL log file."""
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')
