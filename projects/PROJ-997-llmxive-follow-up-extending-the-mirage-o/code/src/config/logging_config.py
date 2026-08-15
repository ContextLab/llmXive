import logging
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import time

def ensure_log_dir(log_dir: Path = Path("logs")):
    log_dir.mkdir(parents=True, exist_ok=True)

class JsonLineFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": time.time(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        # Add extra fields if present
        if hasattr(record, 'sample_id'):
            log_record['sample_id'] = record.sample_id
        if hasattr(record, 'status'):
            log_record['status'] = record.status
        if hasattr(record, 'error_code'):
            log_record['error_code'] = record.error_code
        
        return json.dumps(log_record)

def setup_logger(name: str, log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

    # File handler if log_file is provided
    if log_file:
        ensure_log_dir(log_file.parent)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(JsonLineFormatter())
        logger.addHandler(fh)

    return logger

def log_sample_progress(
    logger: logging.Logger,
    sample_id: str,
    status: str,
    error_code: Optional[str] = None,
    message: Optional[str] = None
):
    """
    Logs sample progress in JSON lines format.
    """
    extra = {
        'sample_id': sample_id,
        'status': status
    }
    if error_code:
        extra['error_code'] = error_code
    
    msg = message or f"Sample {sample_id} processed with status {status}"
    if status == 'error':
        logger.error(msg, extra=extra)
    elif status == 'skipped':
        logger.warning(msg, extra=extra)
    else:
        logger.info(msg, extra=extra)
