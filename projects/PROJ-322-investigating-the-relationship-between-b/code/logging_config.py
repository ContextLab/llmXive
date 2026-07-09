"""
Logging infrastructure configuration for llmXive project.

Initializes file handlers with rotation and console output.
Configures memory hooks to emit warnings when RAM usage approaches 6GB.
"""
import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "data" / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

# Default configuration
DEFAULT_LOG_LEVEL = logging.INFO
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Memory warning threshold (85% of 6GB limit)
MEMORY_WARNING_THRESHOLD_GB = 5.1
MEMORY_LIMIT_GB = 6.0

# Global logger instance
_logger: Optional[logging.Logger] = None
_memory_hook_enabled: bool = False

# Custom log record attribute for memory state
class MemoryLogRecord(logging.LogRecord):
    """LogRecord extension to include memory usage."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ram_gb = get_current_ram_gb_safe()

def get_current_ram_gb_safe() -> float:
    """
    Safely get current RAM usage in GB.
    Returns 0.0 if memory check fails.
    """
    try:
        from memory_monitor import get_current_ram_gb
        return get_current_ram_gb()
    except Exception:
        return 0.0

def _ensure_log_dir() -> None:
    """Ensure the log directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def _check_memory_and_log() -> None:
    """
    Check current RAM usage and log a warning if it approaches the limit.
    
    This function is called explicitly by the pipeline or via hooks.
    """
    if not _memory_hook_enabled:
        return
    
    try:
        from memory_monitor import get_current_ram_gb, is_limit_exceeded
        
        current_ram = get_current_ram_gb()
        logger = logging.getLogger("llmXive")
        
        if current_ram >= MEMORY_LIMIT_GB:
            logger.critical(f"CRITICAL: Memory limit exceeded! Current: {current_ram:.2f} GB, Limit: {MEMORY_LIMIT_GB} GB")
        elif current_ram >= MEMORY_WARNING_THRESHOLD_GB:
            logger.warning(f"Time Limit Warning: RAM usage approaching limit. Current: {current_ram:.2f} GB, Threshold: {MEMORY_WARNING_THRESHOLD_GB} GB, Limit: {MEMORY_LIMIT_GB} GB")
    except ImportError:
        # memory_monitor not yet available or import failed
        pass
    except Exception as e:
        # Log any unexpected errors but don't crash the pipeline
        logger = logging.getLogger("llmXive")
        logger.debug(f"Memory check failed during logging hook: {str(e)}")

class MemoryCheckingFilter(logging.Filter):
    """
    Logging filter that checks memory before allowing a log record to pass.
    This effectively acts as a hook to emit warnings based on current state.
    """
    def filter(self, record):
        # Perform the memory check before the log is emitted
        _check_memory_and_log()
        return True

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create the project logger with file and console handlers.
    
    Args:
        name: Logger name (defaults to 'llmXive')
        
    Returns:
        Configured logger instance
    """
    global _logger
    
    if _logger is not None and _logger.name == name:
        return _logger
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(DEFAULT_LOG_LEVEL)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    _ensure_log_dir()
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(DEFAULT_LOG_LEVEL)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    # Add memory checking filter to both handlers
    mem_filter = MemoryCheckingFilter()
    file_handler.addFilter(mem_filter)
    console_handler.addFilter(mem_filter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    _logger = logger
    return logger

def initialize_logging(memory_hooks: bool = True) -> None:
    """
    Initialize the logging infrastructure.
    
    Args:
        memory_hooks: If True, enable memory monitoring hooks that check RAM
                    before logging and emit warnings when approaching limits.
    
    This function should be called once at the start of the application.
    """
    global _memory_hook_enabled
    
    get_logger()
    logger = logging.getLogger("llmXive")
    logger.info("Logging infrastructure initialized")
    logger.info(f"Log file: {LOG_FILE}")
    
    # Enable memory monitoring hooks if requested
    _memory_hook_enabled = memory_hooks
    if memory_hooks:
        logger.info(f"Memory monitoring hooks enabled (warning threshold: {MEMORY_WARNING_THRESHOLD_GB:.2f} GB)")
    else:
        logger.info("Memory monitoring hooks disabled")

def set_log_level(level: int) -> None:
    """
    Set the logging level for all handlers.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.WARNING)
    """
    logger = get_logger()
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

def log_memory_warning() -> None:
    """
    Explicitly trigger a memory check and log warning if needed.
    
    This can be called manually at critical points in the pipeline.
    """
    _check_memory_and_log()

if __name__ == "__main__":
    # Test the logging configuration
    initialize_logging(memory_hooks=True)
    logger = get_logger()
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test memory warning hook
    logger.info("Testing memory monitoring hook...")
    log_memory_warning()
    
    logger.info("Logging test completed successfully")
