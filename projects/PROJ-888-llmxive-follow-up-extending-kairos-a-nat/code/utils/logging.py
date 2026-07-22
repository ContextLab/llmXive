import logging
import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

# Custom Exceptions
class LlmXiveError(Exception):
    """Base exception for llmXive pipeline errors."""
    pass

class DataFetchError(LlmXiveError):
    """Raised when data fetching fails."""
    pass

class QuantizationError(LlmXiveError):
    """Raised when quantization fails or produces invalid results."""
    pass

class ModelLoadError(LlmXiveError):
    """Raised when model loading fails."""
    pass

class ResourceLimitExceeded(LlmXiveError):
    """Raised when resource limits (RAM, time) are exceeded."""
    pass

class ConfigurationError(LlmXiveError):
    """Raised when configuration is invalid."""
    pass

class StatisticalAnalysisError(LlmXiveError):
    """Raised when statistical analysis fails."""
    pass

# Logger Setup
_logger: Optional[logging.Logger] = None
_log_file: Optional[Path] = None

def get_logger(name: str = "llmxive") -> logging.Logger:
    """
    Retrieves or creates a logger instance with standardized formatting.
    Ensures only one logger instance per name is created and configured.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        if _logger.level == logging.NOTSET:
            _logger.setLevel(logging.INFO)
            console_handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            _logger.addHandler(console_handler)
            # Log to file if LOG_FILE env var is set
            log_file = os.getenv('LLMXIVE_LOG_FILE')
            if log_file:
                _log_file = Path(log_file)
                file_handler = logging.FileHandler(_log_file)
                file_handler.setFormatter(formatter)
                _logger.addHandler(file_handler)
    return _logger

def log_error_and_raise(error_class: type, message: str, **kwargs) -> None:
    """
    Logs an error message using the provided error class and raises the exception.
    """
    logger = get_logger()
    logger.error(f"{error_class.__name__}: {message}", extra=kwargs)
    raise error_class(message)

class LogContext:
    """
    Context manager to log resource snapshots and task progress.
    Used to track quantization levels, noise seeds, and peak RAM usage.
    """
    def __init__(self, task_name: str, config: Dict[str, Any]):
        self.task_name = task_name
        self.config = config
        self.logger = get_logger()
        self.start_time = None
        self.peak_memory_mb = 0.0
        self.metrics = {}

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"--- Starting Task: {self.task_name} ---")
        self.logger.info(f"Configuration: {json.dumps(self.config, indent=2)}")
        self.log_resource_snapshot("Start")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        self.log_resource_snapshot("End")
        
        self.logger.info(f"--- Completed Task: {self.task_name} ---")
        self.logger.info(f"Duration: {duration:.2f}s")
        self.logger.info(f"Peak RAM Usage: {self.peak_memory_mb:.2f} MB")
        
        if exc_type is not None:
            self.logger.error(f"Task failed with exception: {exc_type.__name__}: {exc_val}")
            return False
        return True

    def log_resource_snapshot(self, stage: str):
        """Logs current resource usage and updates peak memory."""
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()
            current_ram_mb = mem_info.rss / (1024 * 1024)
            cpu_percent = process.cpu_percent()
            
            if current_ram_mb > self.peak_memory_mb:
                self.peak_memory_mb = current_ram_mb

            self.logger.info(
                f"[{stage}] RAM: {current_ram_mb:.2f} MB (Peak: {self.peak_memory_mb:.2f} MB), CPU: {cpu_percent}%"
            )
        except ImportError:
            self.logger.warning(f"[{stage}] psutil not available, skipping resource snapshot.")

    def log_metric(self, key: str, value: Any):
        """Logs a specific metric (e.g., quantization level, noise seed)."""
        self.metrics[key] = value
        self.logger.info(f"Metric: {key} = {value}")

def log_metric(key: str, value: Any, task_name: Optional[str] = None):
    """
    Standalone function to log a metric if not inside a context.
    """
    logger = get_logger()
    logger.info(f"[{task_name or 'Global'}] Metric: {key} = {value}")

def validate_config_required(config: Dict[str, Any], required_keys: List[str]) -> None:
    """
    Validates that all required keys exist in the configuration dictionary.
    Raises ConfigurationError if any are missing.
    """
    missing = [k for k in required_keys if k not in config]
    if missing:
        log_error_and_raise(ConfigurationError, f"Missing required config keys: {missing}")

def log_resource_snapshot(stage: str, task_name: Optional[str] = None):
    """
    Logs a resource snapshot without a context manager.
    """
    logger = get_logger()
    try:
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        current_ram_mb = mem_info.rss / (1024 * 1024)
        cpu_percent = process.cpu_percent()
        
        logger.info(
            f"[{task_name or 'Global'}] [{stage}] RAM: {current_ram_mb:.2f} MB, CPU: {cpu_percent}%"
        )
    except ImportError:
        logger.warning(f"[{task_name or 'Global'}] [{stage}] psutil not available.")