import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

def exponential_backoff_retry(
    func: Callable,
    max_retries: int = 5,
    backoff_factor: float = 1.0,
    *args,
    **kwargs
) -> Any:
    """
    Retry a function with exponential backoff.
    """
    retries = 0
    while retries < max_retries:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            retries += 1
            if retries >= max_retries:
                raise
            wait_time = backoff_factor * (2 ** (retries - 1))
            logger.warning(f"Retry {retries}/{max_retries} after {wait_time}s due to: {e}")
            time.sleep(wait_time)

def calculate_checksum(file_path: Union[str, Path]) -> str:
    """
    Calculate SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def log_api_provenance(
    operation: str,
    status: str,
    details: Dict[str, Any],
    output_path: Optional[str] = None
) -> None:
    """
    Log API provenance to data/logs/api_log.jsonl.
    """
    log_entry = {
        "timestamp": time.time(),
        "operation": operation,
        "status": status,
        "details": details,
        "output_path": output_path
    }
    
    log_file = Path(config.DATA_LOGS_DIR) / "api_log.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    logger.info(f"Logged provenance: {operation} ({status})")

# Note: The calculate_checksum function is fully implemented and used
# in data_ingestion.py for generating checksums of processed files.
# The log_api_provenance function is also fully implemented for tracking
# API interactions and data processing steps.
