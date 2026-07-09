import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

# Configure module logger
logger = logging.getLogger(__name__)

def exponential_backoff_retry(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.

    Args:
        func: The function to retry.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        backoff_factor: Multiplier for delay after each retry.
        exceptions: Tuple of exception classes to catch and retry.

    Returns:
        The wrapped function.
    """
    def wrapper(*args, **kwargs) -> Any:
        delay = base_delay
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if attempt == max_retries:
                    logger.error(f"Max retries exceeded for {func.__name__}: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                time.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)
    return wrapper

def calculate_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hex digest of the file checksum.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    hash_func = hashlib.new(algorithm)
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def log_api_provenance(
    log_path: Union[str, Path],
    query_type: str,
    source: str,
    params: Dict[str, Any],
    status: str,
    record_count: Optional[int] = None,
    error_message: Optional[str] = None,
    duration_seconds: Optional[float] = None
) -> None:
    """
    Log API query details and filtering decisions to a JSONL file.

    Args:
        log_path: Path to the log file (e.g., data/logs/api_log.jsonl).
        query_type: Type of query (e.g., 'flare_fetch', 'exoplanet_fetch', 'filter_decision').
        source: Data source (e.g., 'MAST', 'NASA Exoplanet Archive').
        params: Dictionary of query parameters or filtering criteria.
        status: Status of the operation ('success', 'failure', 'warning').
        record_count: Number of records returned or affected (optional).
        error_message: Error message if status is 'failure' or 'warning' (optional).
        duration_seconds: Duration of the operation in seconds (optional).
    """
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "query_type": query_type,
        "source": source,
        "params": params,
        "status": status,
        "record_count": record_count,
        "error_message": error_message,
        "duration_seconds": duration_seconds
    }

    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')

    logger.info(f"Logged API provenance: {query_type} from {source} - {status}")
