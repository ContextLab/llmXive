"""
Automated Data Backup Module.

This module implements an immutable audit trail by copying the submissions
CSV file to a timestamped backup location after every successful write.
This reinforces Constitution Principle III (Data Integrity & Auditability).
"""

import os
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Configure logging for backup operations
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ensure logs directory exists
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# File handler for backup errors
file_handler = logging.FileHandler(logs_dir / "backup_errors.log")
file_handler.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def get_submissions_csv_path() -> Path:
    """Return the path to the raw submissions CSV."""
    return get_project_root() / "data" / "raw" / "submissions.csv"


def get_backup_dir() -> Path:
    """Return the path to the backups directory."""
    return get_project_root() / "data" / "backups"


def create_backup(source_path: Optional[Path] = None) -> Optional[Path]:
    """
    Create a timestamped backup of the submissions CSV.

    Args:
        source_path: Optional path to the source file. If None, uses the default
                     submissions.csv path.

    Returns:
        Path to the created backup file, or None if backup failed.

    Raises:
        FileNotFoundError: If the source file does not exist.
        OSError: If the backup operation fails (permissions, disk full, etc.).
    """
    if source_path is None:
        source_path = get_submissions_csv_path()

    if not source_path.exists():
        logger.error(f"Source file not found: {source_path}")
        raise FileNotFoundError(f"Source file not found: {source_path}")

    backup_dir = get_backup_dir()
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"submissions_{timestamp}.csv"
    backup_path = backup_dir / backup_filename

    try:
        # Perform the copy
        shutil.copy2(str(source_path), str(backup_path))
        logger.info(f"Backup created: {backup_path}")

        # Log the backup event to a manifest for auditability
        manifest_path = backup_dir / "backup_manifest.json"
        manifest_entry = {
            "timestamp": datetime.now().isoformat(),
            "source_file": str(source_path),
            "backup_file": str(backup_path),
            "backup_filename": backup_filename
        }

        manifest_data = []
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                try:
                    manifest_data = json.load(f)
                except json.JSONDecodeError:
                    manifest_data = []

        manifest_data.append(manifest_entry)

        with open(manifest_path, 'w') as f:
            json.dump(manifest_data, f, indent=2)

        return backup_path

    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise OSError(f"Backup operation failed: {e}")


def backup_on_write(source_path: Optional[Path] = None) -> bool:
    """
    Wrapper to trigger backup after a write operation.

    This function is intended to be called immediately after a successful
    write to the submissions CSV to ensure a backup exists.

    Args:
        source_path: Optional path to the source file.

    Returns:
        True if backup was successful, False otherwise (with error logged).
    """
    try:
        create_backup(source_path)
        return True
    except Exception as e:
        logger.error(f"Backup failed after write: {e}")
        # Re-raise to ensure the caller knows the audit trail was not created
        raise


def main():
    """
    Command-line entry point for manual backup triggering.
    Usage: python -m code.utils.backup
    """
    print("Triggering manual data backup...")
    try:
        backup_path = create_backup()
        if backup_path:
            print(f"Success! Backup created at: {backup_path}")
        else:
            print("Backup failed.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
