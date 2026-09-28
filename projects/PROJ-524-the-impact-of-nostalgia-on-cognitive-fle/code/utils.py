import os
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root logger."""
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

def log_info(message: str) -> None:
    logging.info(message)

def log_warning(message: str) -> None:
    logging.warning(message)

def log_error(message: str) -> None:
    logging.error(message)

def get_timestamp() -> str:
    """Return current timestamp as ISO format string."""
    return datetime.now().isoformat()

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_dir_hash(dir_path: Path) -> Optional[str]:
    """Compute a combined hash of all files in a directory."""
    if not dir_path.exists():
        return None
    files = sorted(dir_path.glob("*"))
    if not files:
        return None
    combined_hash = hashlib.sha256()
    for f in files:
        if f.is_file():
            file_hash = compute_sha256(f)
            combined_hash.update(file_hash.encode('utf-8'))
    return combined_hash.hexdigest()
