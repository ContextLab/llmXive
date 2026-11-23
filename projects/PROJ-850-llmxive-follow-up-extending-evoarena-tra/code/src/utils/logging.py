"""
Structured logging utilities for the project.

This module provides logging functionality for tracking context tokens,
inference time, and success status.
"""
import csv
import os
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.seeding import set_deterministic_seed


def get_logger(name: str = 'evomem') -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name (str): Name of the logger.
    
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Set deterministic seed
    set_deterministic_seed(42)
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
    
    return logger


class ExecutionTimer:
    """
    Context manager for timing code execution.
    """
    
    def __init__(self, operation_name: str):
        """
        Initialize the timer.
        
        Args:
            operation_name (str): Name of the operation being timed.
        """
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        """Start the timer."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer and calculate duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        return False


def log_metrics(metrics: Dict[str, Any], output_path: str = 'data/logs/metrics.csv'):
    """
    Log metrics to a CSV file.
    
    Args:
        metrics (Dict[str, Any]): Metrics to log.
        output_path (str): Path to the output CSV file.
    """
    # Set deterministic seed
    set_deterministic_seed(42)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists to determine if header is needed
    file_exists = os.path.exists(output_path)
    
    with open(output_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=metrics.keys())
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow(metrics)
    
    logger = get_logger()
    logger.info(f"Logged metrics to {output_path}")


def main():
    """Main function to demonstrate logging utilities."""
    # Set deterministic seed
    set_deterministic_seed(42)
    
    logger = get_logger()
    logger.info("Logging utilities initialized")
    
    # Example timing
    with ExecutionTimer("example_operation") as timer:
        time.sleep(0.1)
    
    print(f"Operation took {timer.duration:.4f} seconds")
    
    # Example metrics logging
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'operation': 'example',
        'duration': timer.duration,
        'success': True
    }
    log_metrics(metrics)


if __name__ == '__main__':
    main()