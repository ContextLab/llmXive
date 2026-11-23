import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

SCHEMA = {
    "granularity": str,
    "expressiveness": str,
    "success_rate": float,
    "latency_ms": float,
    "memory_mb": float,
    "trace_count": int
}

def get_schema() -> Dict[str, type]:
    return SCHEMA

def validate_row(row: Dict[str, Any], schema: Dict[str, type]) -> bool:
    """Validate that a row matches the expected schema."""
    for key, expected_type in schema.items():
        if key not in row:
            return False
        if not isinstance(row[key], expected_type):
            return False
    return True

def ensure_output_directory(file_path: Path):
    """Ensure the directory for the output file exists."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

def write_header_only(file_path: Path):
    """Write the CSV header to the file."""
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA.keys())
        writer.writeheader()

def append_row(file_path: Path, row: Dict[str, Any]):
    """Append a row to the CSV file."""
    with open(file_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=SCHEMA.keys())
        writer.writerow(row)

def clear_results(file_path: Path):
    """Clear the file content."""
    if file_path.exists():
        file_path.unlink()
