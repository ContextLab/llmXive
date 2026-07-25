"""
Timing instrumentation utilities for the elastic anisotropy pipeline.
Ensures training completes within the specified time budget.
"""
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from src.utils.config import get_path

logger = logging.getLogger(__name__)

TIME_BUDGET_SECONDS = 3600  # 1 hour

class Timer:
    """Context manager for timing code blocks."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"Starting {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        logger.info(f"Completed {self.operation_name} in {self.duration:.2f} seconds")
        
        if self.duration > TIME_BUDGET_SECONDS:
            logger.error(f"{self.operation_name} exceeded time budget of {TIME_BUDGET_SECONDS}s!")
            return False
        return True
    
    def get_duration(self) -> float:
        return self.duration if self.duration is not None else 0.0

def save_timing_results(timing_data: Dict[str, Any], output_path: Optional[Path] = None):
    """
    Save timing results to a JSON file.
    
    Args:
        timing_data: Dictionary containing timing information
        output_path: Path to save the results. If None, uses default output/timing.json
    """
    if output_path is None:
        output_path = get_path("output/timing.json")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(timing_data, f, indent=2)
    
    logger.info(f"Timing results saved to {output_path}")

def check_time_budget(duration: float, operation_name: str) -> bool:
    """
    Check if the operation completed within the time budget.
    
    Args:
        duration: Duration in seconds
        operation_name: Name of the operation for logging
        
    Returns:
        True if within budget, False otherwise
    """
    if duration > TIME_BUDGET_SECONDS:
        logger.error(f"{operation_name} took {duration:.2f}s, exceeding budget of {TIME_BUDGET_SECONDS}s")
        return False
    else:
        logger.info(f"{operation_name} completed within budget: {duration:.2f}s < {TIME_BUDGET_SECONDS}s")
        return True