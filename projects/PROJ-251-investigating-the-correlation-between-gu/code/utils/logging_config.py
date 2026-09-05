import logging
import os
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

# Ensure logs directory exists
LOGS_DIR = Path(__file__).parent.parent.parent / "data" / "results"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Global storage for exclusion statistics to be written at the end of a run
_exclusion_stats: list[dict] = []
_sample_sizes: list[int] = []

def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger instance."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # File handler
    log_file = LOGS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def log_exclusion_count(count: int, reason: str) -> None:
    """Logs exclusion statistics."""
    logger = get_logger(__name__)
    logger.info(f"Excluded {count} records: {reason}")
    _exclusion_stats.append({"count": count, "reason": reason})

def log_sample_size(count: int) -> None:
    """Logs the final sample size."""
    logger = get_logger(__name__)
    logger.info(f"Final sample size: {count}")
    _sample_sizes.append(count)

def log_error_context(error: Exception, context: str = "") -> None:
    """Logs an error with context."""
    logger = get_logger(__name__)
    logger.error(f"{context}: {str(error)}", exc_info=True)

def flush_exclusion_stats() -> None:
    """Writes accumulated exclusion stats to a JSON file in data/results/."""
    if not _exclusion_stats and not _sample_sizes:
        return

    stats_file = LOGS_DIR / "exclusion_statistics.json"
    output = {
        "exclusions": _exclusion_stats,
        "final_sample_sizes": _sample_sizes,
        "timestamp": datetime.now().isoformat()
    }
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    
    # Reset global state
    _exclusion_stats.clear()
    _sample_sizes.clear()

def reset_exclusion_stats() -> None:
    """Resets the global exclusion statistics counters."""
    _exclusion_stats.clear()
    _sample_sizes.clear()