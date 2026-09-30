import logging
import os
import csv
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Ensure the results directory exists
RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
QUALITY_REPORT_PATH = RESULTS_DIR / "quality_report.csv"

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure the root logger.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file. If None, logs only to console.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers to avoid duplicates in interactive environments
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(console_format)
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (usually __name__).

    Returns:
        Configured Logger instance.
    """
    return logging.getLogger(name)

def initialize_quality_report() -> None:
    """
    Initialize the quality report CSV file with headers if it does not exist.
    Headers: [exclusion_type, count]
    """
    if not QUALITY_REPORT_PATH.exists():
        with open(QUALITY_REPORT_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['exclusion_type', 'count'])

def write_quality_entry(exclusion_type: str, count: int) -> None:
    """
    Append a single entry to the quality report CSV.

    Args:
        exclusion_type: String describing the type of exclusion (e.g., 'blink_loss', 'missing_data').
        count: Integer count of excluded items.
    """
    timestamp = datetime.now().isoformat()
    with open(QUALITY_REPORT_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([exclusion_type, count])

class LoggingContext:
    """
    Context manager for tracking exclusions and writing a final report.

    This class aggregates exclusion counts during a processing run and writes
    them to `results/quality_report.csv` upon completion.
    """

    def __init__(self):
        self.exclusions: Dict[str, int] = {}
        # Ensure the report file exists with headers before we start
        initialize_quality_report()

    def add_exclusion(self, exclusion_type: str, count: int) -> None:
        """
        Record an exclusion event.

        Args:
            exclusion_type: The category of exclusion (e.g., 'blink_loss', 'missing_fixations').
            count: The number of items excluded for this type.
        """
        if count < 0:
            raise ValueError(f"Count for exclusion '{exclusion_type}' cannot be negative.")

        if exclusion_type in self.exclusions:
            self.exclusions[exclusion_type] += count
        else:
            self.exclusions[exclusion_type] = count

        # Log the action for immediate visibility
        logger = get_logger(__name__)
        logger.debug(f"Exclusion recorded: {exclusion_type} (+{count})")

    def write_report(self, path: Optional[str] = None) -> None:
        """
        Write all accumulated exclusions to the CSV file.

        Args:
            path: Optional path to write to. If None, writes to default QUALITY_REPORT_PATH.
        """
        output_path = Path(path) if path else QUALITY_REPORT_PATH

        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # If the file is new, we need headers. If it exists, we append.
        # However, to ensure idempotency in testing or re-runs, we check if headers exist.
        file_exists = output_path.exists()
        file_empty = file_exists and os.getsize(output_path) == 0

        with open(output_path, 'a', newline='') as f:
            writer = csv.writer(f)

            # If file is new or empty, write headers
            if not file_exists or file_empty:
                writer.writerow(['exclusion_type', 'count'])

            timestamp = datetime.now().isoformat()
            for exc_type, count in self.exclusions.items():
                writer.writerow([exc_type, count])

        logger = get_logger(__name__)
        logger.info(f"Quality report written to {output_path} with {len(self.exclusions)} exclusion types.")

def main():
    """
    Test entry point to verify LoggingContext functionality.
    """
    # Remove existing file to test fresh initialization
    if QUALITY_REPORT_PATH.exists():
        os.remove(QUALITY_REPORT_PATH)

    # Initialize context
    ctx = LoggingContext()

    # Simulate some exclusions
    ctx.add_exclusion("blink_loss", 15)
    ctx.add_exclusion("missing_fixations", 5)
    ctx.add_exclusion("blink_loss", 3) # Test accumulation

    # Write the report
    ctx.write_report()

    # Verification assertions
    assert QUALITY_REPORT_PATH.exists(), "Report file not created."

    with open(QUALITY_REPORT_PATH, 'r') as f:
        lines = f.readlines()

    # Check headers
    assert lines[0].strip() == "exclusion_type,count", f"Headers mismatch: {lines[0]}"

    # Check content rows (3 rows: blink_loss 15, missing_fixations 5, blink_loss 3 -> accumulated)
    # Note: write_report writes the accumulated dict, so we expect 2 rows for 2 unique keys
    assert len(lines) == 3, f"Expected 3 lines (1 header + 2 data), got {len(lines)}"

    # Check accumulation logic (blink_loss should be 15+3=18)
    data_lines = [line.strip().split(',') for line in lines[1:]]
    blink_rows = [row for row in data_lines if row[0] == 'blink_loss']
    missing_rows = [row for row in data_lines if row[0] == 'missing_fixations']

    assert len(blink_rows) == 1, "blink_loss should appear once (accumulated)"
    assert int(blink_rows[0][1]) == 18, f"blink_loss count should be 18, got {blink_rows[0][1]}"

    assert len(missing_rows) == 1, "missing_fixations should appear once"
    assert int(missing_rows[0][1]) == 5, f"missing_fixations count should be 5, got {missing_rows[0][1]}"

    print("SUCCESS: LoggingContext works correctly. File created at:", QUALITY_REPORT_PATH)
    print("Content:")
    with open(QUALITY_REPORT_PATH, 'r') as f:
        print(f.read())

if __name__ == "__main__":
    main()
