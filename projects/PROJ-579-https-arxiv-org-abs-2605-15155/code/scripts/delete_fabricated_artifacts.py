"""
Task T037: Delete Fabricated Artifacts

This script checks for the existence of potentially fabricated data artifacts
(data/sdar_results.csv and the figures/ directory) and removes them if found.
It logs the actions taken to outputs/gaps/fabrication_cleanup.log.

Dependencies:
- None (standard library only)
"""
import os
import shutil
from pathlib import Path

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRAUD_CSV_PATH = PROJECT_ROOT / "data" / "sdar_results.csv"
FIGURES_DIR_PATH = PROJECT_ROOT / "figures"
LOG_PATH = PROJECT_ROOT / "outputs" / "gaps" / "fabrication_cleanup.log"

def ensure_log_directory():
    """Ensure the directory for the cleanup log exists."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def log_message(message: str):
    """Append a message to the cleanup log."""
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def delete_file(path: Path):
    """Safely delete a file if it exists."""
    if path.exists():
        path.unlink()
        return True
    return False

def delete_directory(path: Path):
    """Safely delete a directory and its contents if it exists."""
    if path.exists() and path.is_dir():
        shutil.rmtree(path)
        return True
    return False

def main():
    """
    Main entry point for T037.
    Deletes fabricated artifacts and logs the action.
    """
    ensure_log_directory()
    
    log_message(f"Starting fabrication artifact cleanup at {Path.cwd()}")
    
    deleted_csv = False
    deleted_figures = False

    # Check and delete CSV
    if delete_file(FRAUD_CSV_PATH):
        log_message(f"DELETED: Fabricated CSV found at {FRAUD_CSV_PATH}")
        deleted_csv = True
    else:
        log_message(f"SKIPPED: No fabricated CSV found at {FRAUD_CSV_PATH}")

    # Check and delete figures directory
    if delete_directory(FIGURES_DIR_PATH):
        log_message(f"DELETED: Fabricated figures directory found at {FIGURES_DIR_PATH}")
        deleted_figures = True
    else:
        log_message(f"SKIPPED: No fabricated figures directory found at {FIGURES_DIR_PATH}")

    if not deleted_csv and not deleted_figures:
        log_message("No fabricated artifacts found.")
    else:
        log_message("Cleanup completed successfully.")
    
    print(f"Cleanup finished. Log written to: {LOG_PATH}")

if __name__ == "__main__":
    main()