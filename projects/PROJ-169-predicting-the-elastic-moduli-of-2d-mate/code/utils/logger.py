import logging
import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional
from rich.console import Console

_logger_instance = None
_console = Console()

def configure_log_file(log_path: Path):
    """Configure file logging with structured JSON output for bias checks."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create file handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    
    # Use JSON formatter for structured logs (critical for bias analysis)
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            # Include extra fields if present
            if hasattr(record, 'extra_data'):
                log_data.update(record.extra_data)
            return json.dumps(log_data)

    file_handler.setFormatter(JsonFormatter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []
    root_logger.addHandler(file_handler)

def get_logger(name: str = "llmXive") -> logging.Logger:
    """Get a configured logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = logging.getLogger(name)
        _logger_instance.setLevel(logging.DEBUG)
        if not _logger_instance.handlers:
            # Console handler for human-readable output
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            _logger_instance.addHandler(console_handler)
    return _logger_instance

def log_bias_check(logger: logging.Logger, report: Dict[str, Any]):
    """Log bias check results with structured formatting.
    
    This function ensures bias analysis results are logged in a structured way
    that can be parsed by downstream analysis tools. The log includes:
    - Exclusion counts by reason
    - Family distribution statistics
    - Flags for potential data bias
    
    Args:
        logger: Logger instance to use
        report: Dictionary containing bias check results with keys:
            - 'exclusion_counts': dict of reason -> count
            - 'family_distribution': dict of family_id -> count
            - 'bias_flags': list of strings describing detected biases
    """
    # Log structured JSON for programmatic parsing
    extra_data = {
        "event_type": "bias_check",
        "exclusion_counts": report.get("exclusion_counts", {}),
        "family_distribution": report.get("family_distribution", {}),
        "bias_flags": report.get("bias_flags", [])
    }
    
    # Create a record with extra data
    record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "",
        0,
        f"Bias Check Report: {json.dumps(report, indent=2)}",
        (),
        None
    )
    record.extra_data = extra_data
    logger.handle(record)
    
    # Also print a human-readable summary
    _console.print(f"[bold blue]Bias Check Summary:[/bold blue]")
    _console.print(f"  Exclusions: {report.get('exclusion_counts', {})}")
    _console.print(f"  Families: {len(report.get('family_distribution', {}))}")
    if report.get('bias_flags'):
        _console.print(f"  [yellow]Flags:[/yellow] {report['bias_flags']}")

def log_exclusion_reason(logger: logging.Logger, reason: str, count: int):
    """Log exclusion reasons for data filtering with structured formatting.
    
    This function logs why specific material entries were excluded during
    data filtering. It ensures these reasons are captured in a structured
    format for bias analysis.
    
    Args:
        logger: Logger instance to use
        reason: String describing the exclusion reason (e.g., "missing_tensor", "non_2d")
        count: Number of entries excluded for this reason
    """
    extra_data = {
        "event_type": "exclusion",
        "reason": reason,
        "count": count
    }
    
    record = logger.makeRecord(
        logger.name,
        logging.WARNING,
        "",
        0,
        f"Exclusion: {reason} (count: {count})",
        (),
        None
    )
    record.extra_data = extra_data
    logger.handle(record)
    
    _console.print(f"[yellow]Exclusion:[/yellow] {reason} ([dim]{count} entries[/dim])")

def log_training_metrics(logger: logging.Logger, epoch: int, loss: float, metrics: Dict[str, float], memory_peak: float):
    """Log training metrics in structured format.
    
    Args:
        logger: Logger instance
        epoch: Current epoch number
        loss: Training loss value
        metrics: Dictionary of evaluation metrics (e.g., mape, rmse)
        memory_peak: Peak memory usage in GB
    """
    extra_data = {
        "event_type": "training_metrics",
        "epoch": epoch,
        "loss": loss,
        "metrics": metrics,
        "memory_peak_gb": memory_peak
    }
    
    record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "",
        0,
        f"Epoch {epoch}: loss={loss:.4f}, metrics={metrics}",
        (),
        None
    )
    record.extra_data = extra_data
    logger.handle(record)

def log_model_checkpoint(logger: logging.Logger, path: str, metrics: Dict[str, float]):
    """Log model checkpoint creation.
    
    Args:
        logger: Logger instance
        path: Path to saved model checkpoint
        metrics: Dictionary of metrics at checkpoint time
    """
    extra_data = {
        "event_type": "checkpoint",
        "path": path,
        "metrics": metrics
    }
    
    record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "",
        0,
        f"Checkpoint saved: {path}",
        (),
        None
    )
    record.extra_data = extra_data
    logger.handle(record)