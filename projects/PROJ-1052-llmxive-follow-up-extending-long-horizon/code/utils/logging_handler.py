import logging
import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
import yaml

class ResearchLogFormatter(logging.Formatter):
    """
    Custom formatter that appends structured JSON metrics to log messages.
    Ensures that metrics like `reward_fidelity_level` and `recovery_segment_id`
    are captured in a machine-readable format within the log line.
    """
    def format(self, record):
        # Standard format
        log_msg = super().format(record)
        
        # Check for extra structured data in the record
        if hasattr(record, 'extra_json'):
            try:
                extra_json = json.dumps(record.extra_json)
                return f"{log_msg} | METRICS: {extra_json}"
            except (TypeError, ValueError):
                return log_msg
        return log_msg

class StructuredResearchHandler(logging.FileHandler):
    """
    File handler specifically configured to capture research metrics.
    """
    def emit(self, record):
        # Ensure the directory exists
        if self.stream:
            self.stream.write(self.format(record) + self.terminator)
            self.flush()

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the config.yaml file.
        
    Returns:
        Dictionary containing configuration parameters.
        
    Raises:
        FileNotFoundError: If config file does not exist.
        yaml.YAMLError: If YAML parsing fails.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(
    name: str,
    config: Optional[Dict[str, Any]] = None,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Sets up a logger with file and console handlers based on configuration.
    
    Args:
        name: Name of the logger (usually __name__).
        config: Optional configuration dictionary. If None, loads from 'config.yaml'.
        log_file: Optional override for the log file path.
        
    Returns:
        Configured logger instance.
    """
    if config is None:
        config = load_config()
    
    log_config = config.get('logging', {})
    level_str = log_config.get('level', 'INFO')
    level = getattr(logging, level_str.upper(), logging.INFO)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = ResearchLogFormatter(log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s'))
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    file_path = log_file or log_config.get('file_path', 'logs/run.log')
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = StructuredResearchHandler(file_path)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def log_metric(
    logger: logging.Logger,
    metric_name: str,
    value: Any,
    extra_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs a specific metric with optional extra context.
    This ensures metrics like `reward_fidelity_level` are captured in the log.
    
    Args:
        logger: The logger instance to use.
        metric_name: Name of the metric (e.g., 'reward_fidelity_level').
        value: Value of the metric.
        extra_data: Additional context dictionary to merge into the log entry.
    """
    extra_payload = {metric_name: value}
    if extra_data:
        extra_payload.update(extra_data)
    
    # We attach the payload to the record via a custom attribute
    # The ResearchLogFormatter will pick this up
    logger.info(
        f"Metric logged: {metric_name}={value}",
        extra={'extra_json': extra_payload}
    )
