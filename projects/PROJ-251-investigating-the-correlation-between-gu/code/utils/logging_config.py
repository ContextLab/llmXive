import logging
import os
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

# Global logger instance
_logger = None

def get_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """
    Get or create a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    global _logger
    
    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(level)
        
        # Avoid adding handlers multiple times
        if not _logger.handlers:
            # Create console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            
            # Add handler to logger
            _logger.addHandler(console_handler)
    
    return _logger

def log_exclusion_count(column_name: str, count: int, logger: Optional[logging.Logger] = None) -> None:
    """
    Log the number of excluded records for a specific column.
    
    Args:
        column_name: Name of the column being filtered
        count: Number of records excluded
        logger: Logger instance (optional, uses default if not provided)
    """
    log = logger or get_logger()
    log.info(f"Exclusion: {count} records excluded due to missing values in '{column_name}'")

def log_sample_size(n: int, logger: Optional[logging.Logger] = None) -> None:
    """
    Log the final sample size.
    
    Args:
        n: Number of samples in the dataset
        logger: Logger instance (optional, uses default if not provided)
    """
    log = logger or get_logger()
    log.info(f"Final sample size: {n} subjects")

def log_error_context(error: Exception, context: str = "", logger: Optional[logging.Logger] = None) -> None:
    """
    Log an error with additional context.
    
    Args:
        error: The exception that occurred
        context: Additional context information
        logger: Logger instance (optional, uses default if not provided)
    """
    log = logger or get_logger()
    error_msg = f"Error: {str(error)}"
    if context:
        error_msg += f" | Context: {context}"
    log.error(error_msg, exc_info=True)

def flush_exclusion_stats(output_path: Optional[Path] = None) -> None:
    """
    Flush exclusion statistics to a log file.
    
    Args:
        output_path: Path to write the log file (optional)
    """
    if output_path:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write a summary log
        with open(output_path, 'w') as f:
            f.write(f"Exclusion Statistics Log - {datetime.now().isoformat()}\n")
            f.write("=" * 50 + "\n")
            # In a real implementation, we would track these in a global dict
            f.write("Exclusion tracking would be implemented here.\n")

def reset_exclusion_stats() -> None:
    """
    Reset exclusion statistics tracking.
    """
    # In a real implementation, this would reset a global tracking dict
    pass
