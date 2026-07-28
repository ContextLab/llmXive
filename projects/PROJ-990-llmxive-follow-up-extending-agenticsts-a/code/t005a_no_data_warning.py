"""
T005a: Generate No-Data Warning.

Logic:
1. Check if `data/processed/metrics_with_moves.csv` exists.
2. If it does NOT exist (indicating T006 was skipped or failed),
   generate `data/processed/edge_case_warnings.log` with the exact text:
   "Warning: No trajectory data available for entropy calculation; pipeline bootstrapped on synthetic data."
3. Ensure the log artifact exists even if no real data was processed.

This task ensures the pipeline has a valid warning log file even when no input data is available.
"""
import os
import logging
from pathlib import Path

def main():
    """Execute T005a logic."""
    # Define paths relative to project root
    # Assuming this script runs from the project root or code/ directory
    # We use absolute paths relative to the current working directory for safety
    processed_dir = Path("data/processed")
    metrics_file = processed_dir / "metrics_with_moves.csv"
    warning_log_file = processed_dir / "edge_case_warnings.log"

    # Ensure the processed directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Check if metrics file exists
    if not metrics_file.exists():
        # The file does not exist, so we generate the warning
        warning_message = "Warning: No trajectory data available for entropy calculation; pipeline bootstrapped on synthetic data."
        
        # Configure logger to write to the specific file
        # We create a new logger to avoid interfering with existing loggers
        logger = logging.getLogger("t005a_no_data_warning")
        logger.setLevel(logging.WARNING)
        
        # Remove any existing handlers to avoid duplicates
        if logger.hasHandlers():
            logger.handlers.clear()
        
        # Create file handler
        file_handler = logging.FileHandler(warning_log_file, mode='w')
        file_handler.setLevel(logging.WARNING)
        
        # Create formatter (we want just the message, no timestamp for this specific log format)
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        
        # Log the warning
        logger.warning(warning_message)
        
        # Also print to stdout for visibility
        print(warning_message)
        
        # Verify the file was created
        if warning_log_file.exists():
            print(f"Successfully created warning log: {warning_log_file}")
        else:
            print(f"Error: Failed to create warning log: {warning_log_file}")
            raise RuntimeError(f"Failed to create {warning_log_file}")
    else:
        # The file exists, so T006 ran successfully.
        # T005a is not needed in this case, but we ensure the log file exists
        # if it was created by T005 for other edge cases.
        if not warning_log_file.exists():
            # Create an empty log file or one indicating no warnings from T005a
            warning_log_file.touch()
            print(f"metrics_with_moves.csv exists. T005a skipped. Created empty log: {warning_log_file}")
        else:
            print(f"metrics_with_moves.csv exists. T005a skipped. Log file already exists: {warning_log_file}")

if __name__ == "__main__":
    main()