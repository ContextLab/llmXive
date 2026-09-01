"""
T034: Refactored I/O Operations.

Consolidates file reading and writing operations to ensure
consistent error handling and encoding usage across the project.
"""

import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Iterator

logger = logging.getLogger("llmxive_io")

def read_csv_rows(
    file_path: Path,
    delimiter: str = ','
) -> Iterator[Dict[str, Any]]:
    """
    Reads a CSV file and yields rows as dictionaries.
    Handles encoding and missing files gracefully.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                yield row
    except Exception as e:
        logger.error(f"Error reading CSV {file_path}: {e}")

def write_csv_rows(
    file_path: Path,
    rows: List[Dict[str, Any]],
    fieldnames: Optional[List[str]] = None,
    delimiter: str = ','
) -> bool:
    """
    Writes a list of dictionaries to a CSV file.
    """
    if not rows:
        logger.warning(f"No data to write to {file_path}")
        return False

    try:
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if fieldnames is None:
            fieldnames = list(rows[0].keys())

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(rows)
        return True
    except Exception as e:
        logger.error(f"Error writing CSV {file_path}: {e}")
        return False

def read_json_file(file_path: Path) -> Optional[Any]:
    """
    Reads a JSON file.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading JSON {file_path}: {e}")
        return None

def write_json_file(file_path: Path, data: Any, indent: int = 2) -> bool:
    """
    Writes data to a JSON file.
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, default=str)
        return True
    except Exception as e:
        logger.error(f"Error writing JSON {file_path}: {e}")
        return False
