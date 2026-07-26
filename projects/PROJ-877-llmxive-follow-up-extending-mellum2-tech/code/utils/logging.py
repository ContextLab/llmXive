"""
Robust error handling and logging infrastructure.
Handles parse errors, timeouts, OOMs, and network issues gracefully.
"""
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any
from functools import wraps
import time

from config import PROJECT_ROOT, RESULTS_DIR

# Custom Exceptions
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class ParseError(PipelineError):
    """Exception for parsing failures."""
    def __init__(self, message: str, file_path: Optional[str] = None, line_num: Optional[int] = None):
        self.file_path = file_path
        self.line_num = line_num
        context = f" at {file_path}:{line_num}" if file_path and line_num else ""
        super().__init__(f"Parse error{context}: {message}")

class TimeoutError(PipelineError):
    """Exception for timeout failures."""
    def __init__(self, message: str, duration: float = 0.0):
        self.duration = duration
        super().__init__(f"Timeout after {duration:.2f}s: {message}")

class OOMError(PipelineError):
    """Exception for out-of-memory failures."""
    def __init__(self, message: str, memory_info: Optional[dict] = None):
        self.memory_info = memory_info
        super().__init__(f"Out of memory: {message}")

class NetworkError(PipelineError):
    """Exception for network failures."""
    def __init__(self, message: str, url: Optional[str] = None):
        self.url = url
        super().__init__(f"Network error{f' ({url})' if url else ''}: {message}")

class ChunkContext:
    """Context manager for tracking chunk processing."""
    def __init__(self, chunk_id: str, logger: logging.Logger):
        self.chunk_id = chunk_id
        self.logger = logger
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"Starting chunk: {self.chunk_id}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type is None:
            self.logger.info(f"Completed chunk: {self.chunk_id} in {duration:.2f}s")
        else:
            self.logger.error(f"Failed chunk: {self.chunk_id} after {duration:.2f}s: {exc_val}")
        return False

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (optional, based on env)
    if os.getenv("ENABLE_LOG_FILE", "false").lower() == "true":
        log_dir = RESULTS_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)

    return logger

def retry_on_transient_errors(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    exceptions: tuple = (NetworkError, ConnectionError, OSError)
) -> Callable:
    """Decorator to retry functions on transient errors."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    wait_time = backoff_factor ** attempt
                    logger = kwargs.get("logger") or get_logger(func.__module__)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    time.sleep(wait_time)
            
            raise last_exception
        return wrapper
    return decorator

def handle_parse_error(error: ParseError, logger: logging.Logger) -> None:
    """Handle parse errors gracefully."""
    logger.error(f"Parse error handled: {error}")
    # Could log to a separate error file if needed

def handle_timeout_error(error: TimeoutError, logger: logging.Logger) -> None:
    """Handle timeout errors gracefully."""
    logger.error(f"Timeout error handled: {error}")

def handle_oom_error(error: OOMError, logger: logging.Logger) -> None:
    """Handle OOM errors gracefully."""
    logger.critical(f"OOM error handled: {error}")
    # OOM is critical; might need to trigger cleanup or alert

def handle_network_error(error: NetworkError, logger: logging.Logger) -> None:
    """Handle network errors gracefully."""
    logger.error(f"Network error handled: {error}")

def main():
    """Demo logging functionality."""
    logger = get_logger("logging_demo")
    
    try:
        with ChunkContext("demo_chunk_001", logger):
            logger.info("Processing demo chunk...")
            raise ParseError("Simulated parse failure", "demo.py", 42)
    except ParseError as e:
        handle_parse_error(e, logger)
    
    logger.info("Demo completed.")

if __name__ == "__main__":
    main()
