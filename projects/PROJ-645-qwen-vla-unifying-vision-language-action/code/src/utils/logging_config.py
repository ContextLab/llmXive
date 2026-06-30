"""
Logging infrastructure configuration for llmXive research pipeline.

Provides structured JSON logging for reproducibility manifest generation.
"""
import json
import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import threading

# Global logger instance
_logger: Optional[logging.Logger] = None
_handler: Optional[logging.Handler] = None
_lock = threading.Lock()

# Log format keys for structured output
LOG_KEYS = [
    "timestamp", "level", "logger", "message", 
    "module", "function", "line", "seed", "experiment_id"
]

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON log records."""
    
    def __init__(self, extra_fields: Optional[List[str]] = None):
        super().__init__()
        self.extra_fields = extra_fields or []
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        for field in self.extra_fields:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create the project logger with JSON formatting.
    
    Args:
        name: Logger name (default: "llmXive")
        
    Returns:
        Configured logger instance
    """
    global _logger, _handler
    
    with _lock:
        if _logger is None:
            _logger = logging.getLogger(name)
            _logger.setLevel(logging.INFO)
            
            # Avoid duplicate handlers
            if not _logger.handlers:
                _handler = logging.StreamHandler(sys.stdout)
                _handler.setFormatter(JSONFormatter())
                _logger.addHandler(_handler)
                _logger.propagate = False
    
    return _logger

def log_reproducibility_manifest(
    output_path: str,
    seeds: List[int],
    hyperparams: Dict[str, Any],
    versions: Dict[str, str],
    experiment_id: Optional[str] = None
) -> Path:
    """
    Write a reproducibility manifest in JSON format.
    
    Args:
        output_path: Path to write the manifest file
        seeds: List of random seeds used
        hyperparams: Training hyperparameters
        versions: Dictionary of library versions
        experiment_id: Optional experiment identifier
        
    Returns:
        Path to the written manifest file
    """
    logger = get_logger()
    manifest = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "experiment_id": experiment_id or f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "seeds": seeds,
        "hyperparameters": hyperparams,
        "versions": versions,
        "git_commit": versions.get("git_commit", "unknown"),
        "python_version": versions.get("python_version", "unknown"),
        "torch_version": versions.get("torch_version", "unknown"),
        "cuda_available": versions.get("cuda_available", False),
        "log_path": output_path,
    }
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)
    
    logger.info(f"Reproducibility manifest written to {path}")
    return path

def log_event(
    event_type: str,
    message: str,
    extra_data: Optional[Dict[str, Any]] = None,
    seed: Optional[int] = None
) -> None:
    """
    Log a structured event with optional extra data.
    
    Args:
        event_type: Type of event (e.g., "training_start", "eval_complete")
        message: Human-readable message
        extra_data: Additional key-value pairs to include
        seed: Random seed if applicable
    """
    logger = get_logger()
    extra = {"event_type": event_type}
    if extra_data:
        extra.update(extra_data)
    if seed is not None:
        extra["seed"] = seed
    
    logger.info(message, extra=extra)

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    extra_fields: Optional[List[str]] = None
) -> logging.Logger:
    """
    Configure logging for the project.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path to write logs
        extra_fields: List of extra fields to include in JSON output
        
    Returns:
        Configured logger instance
    """
    global _logger, _handler
    
    with _lock:
        _logger = logging.getLogger("llmXive")
        _logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        _logger.handlers.clear()
        
        # Console handler with JSON formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter(extra_fields))
        _logger.addHandler(console_handler)
        
        # Optional file handler
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(JSONFormatter(extra_fields))
            _logger.addHandler(file_handler)
        
        _logger.propagate = False
    
    return _logger

def main():
    """Demonstrate logging configuration and manifest generation."""
    # Setup logging
    logger = setup_logging(
        log_level="INFO",
        extra_fields=["experiment_id", "seed", "batch_size"]
    )
    
    # Log some events
    log_event("experiment_start", "Starting cross-embodiment training", {
        "experiment_id": "demo_001",
        "batch_size": 32
    })
    
    # Simulate training progress
    for epoch in range(1, 4):
        log_event("epoch_complete", f"Completed epoch {epoch}", {
            "experiment_id": "demo_001",
            "batch_size": 32,
            "loss": 0.5 / epoch
        }, seed=42)
    
    # Generate reproducibility manifest
    manifest_path = log_reproducibility_manifest(
        output_path="data/reproducibility_manifest.json",
        seeds=[42, 123, 456, 789, 101112],
        hyperparams={
            "batch_size": 32,
            "learning_rate": 1e-4,
            "epochs": 10,
            "model": "Qwen2-VL-2B"
        },
        versions={
            "git_commit": "abc123def",
            "python_version": "3.10.0",
            "torch_version": "2.3.0",
            "cuda_available": False
        },
        experiment_id="demo_001"
    )
    
    log_event("experiment_complete", f"Manifest saved to {manifest_path}", {
        "experiment_id": "demo_001"
    })
    
    print(f"\nDemonstration complete. Manifest written to: {manifest_path}")

if __name__ == "__main__":
    main()
