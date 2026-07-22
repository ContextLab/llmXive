import logging
import json
import hashlib
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Union

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }
        return json.dumps(log_obj)

def setup_logging(log_file: Optional[Union[str, Path]] = None, level: int = logging.INFO):
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root_logger.addHandler(ch)
    
    # File handler if specified
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        root_logger.addHandler(fh)

def calculate_checksum(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logging.getLogger(__name__).error(f"Checksum calculation failed: {e}")
        return ""

def log_checksum(file_path: Path, logger: logging.Logger):
    checksum = calculate_checksum(file_path)
    if checksum:
        logger.info(f"Checksum for {file_path}: {checksum}")
    return checksum

def create_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.setLevel(logging.INFO)
    return logger

def main():
    setup_logging()
    logger = create_logger("LoggingConfig")
    logger.info("Logging configuration initialized.")

if __name__ == "__main__":
    main()