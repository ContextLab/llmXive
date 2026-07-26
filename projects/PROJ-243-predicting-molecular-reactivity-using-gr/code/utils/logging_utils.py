"""
Logging utilities for the project.
"""
import os
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Optional, Dict, Any
from config import get_config

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_file: Optional path to a log file.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if log_file is provided
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger by name."""
    return logging.getLogger(name)

def log_metric(key: str, value: Any, timestamp: Optional[datetime] = None) -> None:
    """
    Log a metric to the metrics file.
    
    Args:
        key: Metric key.
        value: Metric value.
        timestamp: Optional timestamp.
    """
    if timestamp is None:
        timestamp = datetime.now()
        
    from config import get_config
    cfg = get_config()
    metrics_file = os.path.join(cfg['artifacts_dir'], 'metrics.json')
    
    metrics = []
    if os.path.exists(metrics_file):
        try:
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
        except json.JSONDecodeError:
            metrics = []
            
    metrics.append({
        "key": key,
        "value": value,
        "timestamp": timestamp.isoformat()
    })
    
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)

def flush_metrics() -> None:
    """Flush metrics to disk (no-op if already written)."""
    pass

def get_metrics() -> list:
    """Get all logged metrics."""
    from config import get_config
    cfg = get_config()
    metrics_file = os.path.join(cfg['artifacts_dir'], 'metrics.json')
    
    if os.path.exists(metrics_file):
        with open(metrics_file, 'r') as f:
            return json.load(f)
    return []

def log_execution_summary(summary: Dict[str, Any]) -> None:
    """Log an execution summary."""
    from config import get_config
    cfg = get_config()
    summary_file = os.path.join(cfg['artifacts_dir'], 'execution_summary.json')
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

def main():
    """Main entry point for testing logging."""
    logger = setup_logging()
    logger.info("Logging utils loaded.")
    log_metric("test", "value", datetime.now())
    print("Metrics logged.")

if __name__ == "__main__":
    main()
