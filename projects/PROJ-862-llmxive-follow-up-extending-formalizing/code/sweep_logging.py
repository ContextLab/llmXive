"""
Sweep Logging Module for llmXive Pipeline.

Implements FR-011: Logging for sweep progress.
Writes JSON lines to logs/sweep.log with fields:
- current_sigma: float
- pairs_processed: int
- current_rss: float (in MB)
- status: str
"""
import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from memory_monitor import get_rss_memory_mb

# Ensure logs directory exists
LOGS_DIR = "logs"
SWEEP_LOG_PATH = os.path.join(LOGS_DIR, "sweep.log")

def ensure_logs_directory():
    """Create logs directory if it does not exist."""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR, exist_ok=True)

class SweepLogger:
    """
    A dedicated logger for the perturbation sweep process.
    Writes JSON lines to logs/sweep.log.
    """
    
    def __init__(self, log_path: str = SWEEP_LOG_PATH):
        self.log_path = log_path
        ensure_logs_directory()
        
        # Configure file handler for JSON lines
        self.logger = logging.getLogger("sweep_progress")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []
        
        # File handler
        file_handler = logging.FileHandler(self.log_path, mode='a')
        file_handler.setLevel(logging.INFO)
        
        # Custom formatter to output raw JSON
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "current_sigma": getattr(record, 'sigma', None),
                    "pairs_processed": getattr(record, 'pairs_processed', 0),
                    "current_rss": getattr(record, 'rss_mb', 0.0),
                    "status": getattr(record, 'status', 'unknown')
                }
                return json.dumps(log_entry)
        
        file_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(file_handler)

    def log_progress(self, sigma: float, pairs_processed: int, status: str = "processing"):
        """
        Log the current state of the sweep.
        
        Args:
            sigma: Current noise level.
            pairs_processed: Number of pairs processed so far.
            status: Current status string (e.g., 'processing', 'completed', 'failed').
        """
        rss_mb = get_rss_memory_mb()
        self.logger.info(
            "Sweep Progress",
            extra={
                'sigma': sigma,
                'pairs_processed': pairs_processed,
                'rss_mb': rss_mb,
                'status': status
            }
        )

    def log_start(self, sigma: float):
        """Log the start of a new sigma iteration."""
        self.log_progress(sigma, 0, "start")

    def log_step(self, sigma: float, pairs_processed: int):
        """Log a progress step during processing."""
        self.log_progress(sigma, pairs_processed, "processing")

    def log_complete(self, sigma: float, total_pairs: int):
        """Log the successful completion of a sigma iteration."""
        self.log_progress(sigma, total_pairs, "completed")

    def log_error(self, sigma: float, error_msg: str):
        """Log an error during a sigma iteration."""
        rss_mb = get_rss_memory_mb()
        error_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "current_sigma": sigma,
            "pairs_processed": 0,
            "current_rss": rss_mb,
            "status": f"error: {error_msg}"
        }
        # Write directly to file to ensure error is captured even if logger config fails
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(error_record) + '\n')

# Global instance for convenience
sweep_logger = SweepLogger()

def log_sweep_progress(sigma: float, pairs_processed: int, status: str = "processing"):
    """
    Convenience function to log sweep progress.
    
    Args:
        sigma: Current noise level.
        pairs_processed: Number of pairs processed.
        status: Status string.
    """
    sweep_logger.log_progress(sigma, pairs_processed, status)

def log_sweep_start(sigma: float):
    """Log the start of a sigma iteration."""
    sweep_logger.log_start(sigma)

def log_sweep_step(sigma: float, pairs_processed: int):
    """Log a step during processing."""
    sweep_logger.log_step(sigma, pairs_processed)

def log_sweep_complete(sigma: float, total_pairs: int):
    """Log completion of a sigma iteration."""
    sweep_logger.log_complete(sigma, total_pairs)
    
def log_sweep_error(sigma: float, error_msg: str):
    """Log an error during processing."""
    sweep_logger.log_error(sigma, error_msg)
