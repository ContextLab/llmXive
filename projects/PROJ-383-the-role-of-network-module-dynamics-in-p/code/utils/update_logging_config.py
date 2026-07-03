"""
Update logging configuration to support subject exclusion logging.

This module extends the existing logging infrastructure to support
structured logging of subject exclusions with context information.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime

# Import existing configuration
from utils.config import set_all_seeds


class ExclusionFormatter(logging.Formatter):
    """Custom formatter for exclusion events with JSON context."""
    
    def format(self, record):
        if hasattr(record, 'exclusion_context'):
            # Format as structured JSON for exclusion events
            context = record.exclusion_context
            return json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "subject_id": context.get("subject_id"),
                "exclusion_type": context.get("exclusion_type"),
                "reason": context.get("reason"),
                "details": {k: v for k, v in context.items() if k not in ["subject_id", "exclusion_type", "reason", "timestamp"]}
            })
        return super().format(record)


def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    include_console: bool = True
) -> logging.Logger:
    """
    Setup logging infrastructure with support for exclusion events.
    
    Args:
        log_file: Path to log file (optional)
        level: Logging level
        include_console: Whether to include console output
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('llmXive')
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    file_formatter = ExclusionFormatter()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Console handler
    if include_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


def log_subject_exclusion(
    subject_id: str,
    reason: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a subject exclusion event with context.
    
    Args:
        subject_id: Subject identifier
        reason: Reason for exclusion
        context: Additional context information
    """
    logger = logging.getLogger('llmXive')
    
    record = logger.makeRecord(
        name='llmXive',
        level=logging.WARNING,
        fn='',
        lno=0,
        msg=reason,
        args=(),
        exc_info=None
    )
    
    record.exclusion_context = {
        "subject_id": subject_id,
        "reason": reason,
        **(context or {})
    }
    
    logger.handle(record)


def log_memory_usage(
    subject_id: Optional[str] = None,
    current_rss: Optional[float] = None,
    peak_rss: Optional[float] = None,
    limit_gb: float = 7.0
) -> None:
    """
    Log memory usage information.
    
    Args:
        subject_id: Optional subject identifier
        current_rss: Current RSS in GB
        peak_rss: Peak RSS in GB
        limit_gb: Memory limit in GB
    """
    logger = logging.getLogger('llmXive')
    
    msg_parts = []
    if subject_id:
        msg_parts.append(f"Subject {subject_id}: ")
    
    if current_rss is not None:
        msg_parts.append(f"Current RSS: {current_rss:.2f}GB")
    
    if peak_rss is not None:
        msg_parts.append(f"Peak RSS: {peak_rss:.2f}GB")
    
    if current_rss is not None and current_rss > limit_gb * 0.9:
        msg_parts.append(f"WARNING: Approaching limit ({limit_gb}GB)")
    
    if msg_parts:
        logger.info(" ".join(msg_parts))


def main() -> None:
    """
    Main function to demonstrate logging configuration.
    
    This function sets up logging and logs sample events
    to verify the configuration is working correctly.
    """
    # Setup logging
    log_file = Path("data/logs/test_logging.log")
    setup_logging(
        log_file=log_file,
        level=logging.INFO,
        include_console=True
    )
    
    logger = logging.getLogger('llmXive')
    
    # Log sample events
    logger.info("Logging configuration test started")
    
    log_subject_exclusion(
        subject_id="100307",
        reason="Missing behavioral data",
        context={
            "exclusion_type": "missing_behavioral_scores",
            "missing_fields": ["accuracy_2back"]
        }
    )
    
    log_subject_exclusion(
        subject_id="100408",
        reason="Excessive motion",
        context={
            "exclusion_type": "excessive_motion",
            "mean_fd": 0.25,
            "threshold": 0.2
        }
    )
    
    log_memory_usage(
        subject_id="100509",
        current_rss=5.2,
        peak_rss=5.8,
        limit_gb=7.0
    )
    
    logger.info("Logging configuration test completed")
    
    print(f"Logs written to {log_file}")


if __name__ == "__main__":
    main()