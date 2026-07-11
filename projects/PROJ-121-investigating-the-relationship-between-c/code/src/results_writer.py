"""
Module to write the dipole timeseries results to CSV.
"""
import csv
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import get_config_summary

logger = logging.getLogger(__name__)

RESULTS_DIR = Path("data/results")
OUTPUT_FILE = RESULTS_DIR / "dipole_timeseries.csv"

def write_dipole_timeseries(
    rows: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> str:
    """
    Write the dipole timeseries data to a CSV file.

    Expected columns:
    - interval_start: ISO format datetime string or float (Julian Date)
    - dipole_amp: float
    - dipole_phase: float (radians or degrees)
    - quad_amp: float
    - partial_interval: boolean (0 or 1)

    Args:
        rows: List of dictionaries containing the results for each interval.
        output_path: Optional path to write the CSV. Defaults to data/results/dipole_timeseries.csv.

    Returns:
        The path to the written file.
    """
    if output_path is None:
        output_path = OUTPUT_FILE

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        logger.warning("No rows provided to write_dipole_timeseries. Creating empty CSV with headers.")
        fieldnames = ["interval_start", "dipole_amp", "dipole_phase", "quad_amp", "partial_interval"]
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return str(output_path)

    # Validate and normalize rows
    fieldnames = ["interval_start", "dipole_amp", "dipole_phase", "quad_amp", "partial_interval"]
    
    # Ensure all rows have the required keys
    for i, row in enumerate(rows):
        for key in fieldnames:
            if key not in row:
                # Provide defaults if missing (should not happen in valid pipeline)
                if key == "partial_interval":
                    row[key] = False
                else:
                    row[key] = 0.0
        
        # Normalize partial_interval to 0 or 1 for CSV
        if isinstance(row["partial_interval"], bool):
            row["partial_interval"] = 1 if row["partial_interval"] else 0
        elif isinstance(row["partial_interval"], (int, float)):
            row["partial_interval"] = int(row["partial_interval"] != 0)

    logger.info(f"Writing {len(rows)} rows to {output_path}")
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Successfully wrote dipole timeseries to {output_path}")
    return str(output_path)
