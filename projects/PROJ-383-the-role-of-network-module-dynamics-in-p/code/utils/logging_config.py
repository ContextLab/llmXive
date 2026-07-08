import logging
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

LOG_DIR = Path("data/logs")
LOG_FILE_NAME = "pipeline_events.log"
EXCLUSION_LOG_FILE_NAME = "exclusions.jsonl"
MEMORY_LOG_FILE_NAME = "memory_events.jsonl"

_logger: Optional[logging.Logger] = None
_exclusion_handler: Optional[logging.Handler] = None
_memory_handler: Optional[logging.Handler] = None

class ExclusionFormatter(logging.Formatter):
    """Custom formatter for exclusion events to JSONL."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "subject_id": getattr(record, "subject_id", None),
            "reason": getattr(record, "reason", None),
            "details": getattr(record, "details", {}),
        }
        return json.dumps(log_data)

class MemoryFormatter(logging.Formatter):
    """Custom formatter for memory events to JSONL."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "current_rss_mb": getattr(record, "current_rss_mb", None),
            "peak_rss_mb": getattr(record, "peak_rss_mb", None),
            "limit_mb": getattr(record, "limit_mb", None),
            "action": getattr(record, "action", None),
        }
        return json.dumps(log_data)

def setup_logging(
    log_level: int = logging.INFO,
    console: bool = True,
    file: bool = True,
) -> logging.Logger:
    """
    Initialize the global logger with standard, exclusion, and memory handlers.
    Ensures log directories exist.
    """
    global _logger, _exclusion_handler, _memory_handler

    if _logger is not None:
        return _logger

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    _logger = logging.getLogger("llmXive")
    _logger.setLevel(log_level)
    _logger.handlers.clear()

    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(log_level)
        ch.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        _logger.addHandler(ch)

    if file:
        fh = logging.FileHandler(LOG_DIR / LOG_FILE_NAME)
        fh.setLevel(log_level)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        _logger.addHandler(fh)

    exclusion_file = LOG_DIR / EXCLUSION_LOG_FILE_NAME
    _exclusion_handler = logging.FileHandler(exclusion_file)
    _exclusion_handler.setLevel(logging.INFO)
    _exclusion_handler.setFormatter(ExclusionFormatter())
    _logger.addHandler(_exclusion_handler)

    memory_file = LOG_DIR / MEMORY_LOG_FILE_NAME
    _memory_handler = logging.FileHandler(memory_file)
    _memory_handler.setLevel(logging.INFO)
    _memory_handler.setFormatter(MemoryFormatter())
    _logger.addHandler(_memory_handler)

    return _logger

def log_subject_exclusion(
    subject_id: str,
    reason: str,
    details: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Log a subject exclusion event to both standard log and exclusion JSONL.
    """
    if logger is None:
        logger = _logger
    if logger is None:
        raise RuntimeError("Logging not initialized. Call setup_logging() first.")

    log_record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "",
        0,
        f"Subject {subject_id} excluded: {reason}",
        (),
        None,
    )
    log_record.subject_id = subject_id
    log_record.reason = reason
    log_record.details = details or {}

    if _exclusion_handler:
        _exclusion_handler.emit(log_record)
    
    # Also emit to standard log for visibility
    logger.info(f"EXCLUSION: Subject {subject_id} excluded due to {reason}", extra={
        "subject_id": subject_id,
        "reason": reason,
    })

def log_memory_usage(
    current_rss_mb: float,
    peak_rss_mb: float,
    limit_mb: float,
    action: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Log a memory usage event to the memory JSONL and standard log.
    """
    if logger is None:
        logger = _logger
    if logger is None:
        raise RuntimeError("Logging not initialized. Call setup_logging() first.")

    log_record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "",
        0,
        f"Memory usage: {current_rss_mb:.1f}MB (Peak: {peak_rss_mb:.1f}MB, Limit: {limit_mb:.1f}MB)",
        (),
        None,
    )
    log_record.current_rss_mb = current_rss_mb
    log_record.peak_rss_mb = peak_rss_mb
    log_record.limit_mb = limit_mb
    log_record.action = action

    if _memory_handler:
        _memory_handler.emit(log_record)

    logger.info(
        f"MEMORY: {current_rss_mb:.1f}MB used, {peak_rss_mb:.1f}MB peak. Action: {action or 'monitoring'}",
        extra={
            "current_rss_mb": current_rss_mb,
            "peak_rss_mb": peak_rss_mb,
            "limit_mb": limit_mb,
            "action": action,
        }
    )

def get_exclusion_summary(logger: Optional[logging.Logger] = None) -> Dict[str, int]:
    """
    Read the exclusion JSONL file and return a summary of exclusion counts by reason.
    """
    if logger is None:
        logger = _logger
    if logger is None:
        return {}

    exclusion_file = LOG_DIR / EXCLUSION_LOG_FILE_NAME
    if not exclusion_file.exists():
        return {}

    summary: Dict[str, int] = {}
    try:
        with open(exclusion_file, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    reason = data.get("reason", "unknown")
                    summary[reason] = summary.get(reason, 0) + 1
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return summary

def main():
    """
    Simple CLI test for logging infrastructure.
    """
    setup_logging()
    log = logging.getLogger("llmXive")
    
    log.info("Testing logging infrastructure...")
    
    log_subject_exclusion("sub-001", "Missing behavioral scores", {"file": "missing.csv"})
    log_subject_exclusion("sub-002", "Excessive motion", {"mean_fd": 0.25})
    
    log_memory_usage(1024.5, 2048.0, 7168.0, "checkpoint")
    log_memory_usage(6800.0, 6900.0, 7168.0, "warning_high")
    
    summary = get_exclusion_summary()
    log.info(f"Exclusion Summary: {summary}")
    
    print("Logging test complete. Check data/logs/ for output files.")

if __name__ == "__main__":
    main()
