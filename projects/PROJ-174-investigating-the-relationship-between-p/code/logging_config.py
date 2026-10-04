"""
Logging configuration and quality report management.
Provides centralized logging setup and quality report tracking.
"""
import logging
import os
import csv
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

_logger_instance: Optional[logging.Logger] = None

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None):
    """
    Configure the root logger for the application.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional path to log file
    """
    global _logger_instance
    
    if _logger_instance is not None:
        return _logger_instance
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    _logger_instance = root_logger
    return _logger_instance

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def initialize_quality_report(report_path: Path):
    """
    Initialize the quality report CSV file with headers.
    
    Args:
        report_path: Path to the quality report CSV file
    """
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not report_path.exists():
        with open(report_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['exclusion_type', 'count'])

def write_quality_entry(report_path: Path, exclusion_type: str, count: int):
    """
    Append an exclusion entry to the quality report.
    
    Args:
        report_path: Path to the quality report CSV file
        exclusion_type: Type of exclusion (e.g., 'blink_loss', 'missing_data')
        count: Number of excluded items
    """
    report_path = Path(report_path)
    with open(report_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([exclusion_type, count])

class LoggingContext:
    """
    Context manager for tracking exclusions and writing quality reports.
    """
    def __init__(self, report_path: Path):
        self.report_path = Path(report_path)
        self.exclusions: Dict[str, int] = {}
        
    def add_exclusion(self, exclusion_type: str, count: int = 1):
        """
        Record an exclusion event.
        
        Args:
            exclusion_type: Type of exclusion
            count: Number of items excluded (default: 1)
        """
        if exclusion_type in self.exclusions:
            self.exclusions[exclusion_type] += count
        else:
            self.exclusions[exclusion_type] = count
        
        # Write immediately to file
        write_quality_entry(self.report_path, exclusion_type, count)
        
    def write_report(self, output_path: Optional[Path] = None):
        """
        Write all accumulated exclusions to the report file.
        
        Args:
            output_path: Optional path to write the final report (defaults to report_path)
        """
        output_path = output_path or self.report_path
        # Entries are already written in add_exclusion, so we just ensure the file exists
        if not output_path.exists():
            initialize_quality_report(output_path)

def main():
    """Main entry point for testing logging config."""
    test_path = Path("results/test_quality_report.csv")
    initialize_quality_report(test_path)
    
    ctx = LoggingContext(test_path)
    ctx.add_exclusion("test_blink_loss", 5)
    ctx.add_exclusion("test_missing_data", 3)
    
    assert test_path.exists(), "Report file should exist"
    print("Logging config test passed.")

if __name__ == "__main__":
    main()