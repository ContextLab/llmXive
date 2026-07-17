import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from tqdm import tqdm

def get_logger(name: str, level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """Get or create a logger with console and optional file output."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def setup_progress_bar(total: int, desc: str = "Processing") -> tqdm:
    """Set up a progress bar for long-running tasks."""
    return tqdm(total=total, desc=desc, unit="task")

def log_metric(logger: logging.Logger, metric_name: str, value: Any, stage: str = "") -> None:
    """Log a metric value."""
    message = f"{stage} - {metric_name}: {value}" if stage else f"{metric_name}: {value}"
    logger.info(message)

def log_error_summary(logger: logging.Logger, error: Exception, context: str = "") -> None:
    """Log an error with context."""
    message = f"{context} - Error: {str(error)}" if context else f"Error: {str(error)}"
    logger.error(message)

def main():
    """Main entry point for logger testing."""
    logger = get_logger("test_logger", level=logging.DEBUG, log_file="logs/test_logger.log")
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    log_metric(logger, "accuracy", 0.95, "Validation")
    log_error_summary(logger, Exception("Test error"), "During processing")

if __name__ == "__main__":
    main()
