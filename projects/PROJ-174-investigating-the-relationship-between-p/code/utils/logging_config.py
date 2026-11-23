import csv
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ensure the results directory exists
RESULTS_DIR = Path("results")
QUALITY_REPORT_PATH = RESULTS_DIR / "quality_report.csv"

# Configure basic logging if not already configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_logging(name: str = "llmXive") -> logging.Logger:
    """Set up and return a logger with the given name."""
    return logging.getLogger(name)

def get_logger(name: str = "llmXive") -> logging.Logger:
    """Get a logger instance, creating it if necessary."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def initialize_quality_report(path: Optional[Path] = None) -> Path:
    """
    Initialize the quality report CSV file with headers if it doesn't exist.
    
    Args:
        path: Optional path to the CSV file. Defaults to results/quality_report.csv.
        
    Returns:
        Path to the initialized file.
    """
    if path is None:
        path = QUALITY_REPORT_PATH
    
    # Ensure the directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists and has content
    if not path.exists() or path.stat().st_size == 0:
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['exclusion_type', 'count'])
        logging.info(f"Initialized quality report at {path}")
    else:
        logging.info(f"Quality report already exists at {path}")
        
    return path

def write_quality_entry(path: Optional[Path] = None, exclusion_type: str = "", count: int = 0) -> None:
    """
    Write an exclusion entry to the quality report CSV.
    
    Args:
        path: Optional path to the CSV file. Defaults to results/quality_report.csv.
        exclusion_type: Type of exclusion (e.g., 'blink', 'missing_data').
        count: Number of exclusions of this type.
    """
    if path is None:
        path = QUALITY_REPORT_PATH
        
    # Ensure the file is initialized
    initialize_quality_report(path)
    
    with open(path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([exclusion_type, count])
    
    logging.info(f"Added exclusion entry: {exclusion_type} = {count}")

class LoggingContext:
    """
    Context manager for logging exclusions and writing quality reports.
    
    This class provides methods to track exclusion types and counts during
    preprocessing and analysis, and writes them to a CSV report.
    """
    
    def __init__(self, log_path: Optional[Path] = None):
        """
        Initialize the LoggingContext.
        
        Args:
            log_path: Optional path to the quality report CSV. 
                     Defaults to results/quality_report.csv.
        """
        self.exclusions: Dict[str, int] = {}
        self.log_path = log_path or QUALITY_REPORT_PATH
        self.logger = get_logger("LoggingContext")
    
    def add_exclusion(self, exclusion_type: str, count: int = 1) -> None:
        """
        Record an exclusion of a specific type.
        
        Args:
            exclusion_type: Type of exclusion (e.g., 'blink', 'missing_data').
            count: Number of exclusions to add (default 1).
        """
        if exclusion_type in self.exclusions:
            self.exclusions[exclusion_type] += count
        else:
            self.exclusions[exclusion_type] = count
        
        self.logger.info(f"Added {count} exclusion(s) of type '{exclusion_type}'")
    
    def write_report(self, path: Optional[Path] = None) -> Path:
        """
        Write all recorded exclusions to the quality report CSV.
        
        This method initializes the CSV file with headers if it doesn't exist,
        then appends all recorded exclusion entries.
        
        Args:
            path: Optional path to the CSV file. Defaults to self.log_path.
                
        Returns:
            Path to the written report file.
        """
        target_path = path or self.log_path
        
        # Initialize the report with headers if needed
        initialize_quality_report(target_path)
        
        # Write all recorded exclusions
        for exclusion_type, count in self.exclusions.items():
            write_quality_entry(target_path, exclusion_type, count)
        
        self.logger.info(f"Wrote {len(self.exclusions)} exclusion entries to {target_path}")
        return target_path
    
    def __enter__(self):
        """Enter the context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and write the report."""
        self.write_report()
        return False

def main():
    """
    Main function to demonstrate the LoggingContext functionality.
    
    This function creates a LoggingContext, adds some sample exclusions,
    and writes the report to verify the CSV initialization and writing.
    """
    print("Testing LoggingContext...")
    
    # Create a context
    with LoggingContext() as ctx:
        # Add some sample exclusions
        ctx.add_exclusion("blink", 15)
        ctx.add_exclusion("missing_data", 5)
        ctx.add_exclusion("low_signal", 3)
        
        # The report will be written automatically on exit
    
    # Verify the file exists and has correct headers
    if QUALITY_REPORT_PATH.exists():
        print(f"Quality report created at {QUALITY_REPORT_PATH}")
        with open(QUALITY_REPORT_PATH, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            print(f"Headers: {headers}")
            assert headers == ['exclusion_type', 'count'], f"Expected headers ['exclusion_type', 'count'], got {headers}"
            rows = list(reader)
            print(f"Data rows: {rows}")
    else:
        print("ERROR: Quality report was not created!")
        raise FileNotFoundError(f"Quality report not found at {QUALITY_REPORT_PATH}")
    
    print("LoggingContext test passed!")

if __name__ == "__main__":
    main()