import csv
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from .config import get_config_summary

logger = logging.getLogger(__name__)

def write_dipole_timeseries(
    results: List[Dict[str, Any]],
    output_path: str,
    detectors: Optional[List[str]] = None
) -> None:
    """
    Write dipole timeseries data to a CSV file.

    Expected columns:
    - interval_start: ISO format datetime string
    - detector: Detector name (IceCube or Auger)
    - dipole_amp: Dipole amplitude
    - dipole_phase: Dipole phase (degrees)
    - quad_amp: Quadrupole amplitude (optional, can be 0 or None)
    - partial_interval: Boolean flag indicating if the interval is partial

    Args:
        results: List of dictionaries containing dipole analysis results per interval.
        output_path: Path to the output CSV file.
        detectors: Optional list of detector names to include. If None, all results are included.
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define the required columns
    fieldnames = [
        'interval_start',
        'detector',
        'dipole_amp',
        'dipole_phase',
        'quad_amp',
        'partial_interval'
    ]

    # Filter results if specific detectors are requested
    if detectors:
        filtered_results = [r for r in results if r.get('detector') in detectors]
    else:
        filtered_results = results

    if not filtered_results:
        logger.warning(f"No results to write to {output_path}")
        # Still create an empty file with headers
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        return

    try:
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in filtered_results:
                row = {
                    'interval_start': result.get('interval_start', ''),
                    'detector': result.get('detector', ''),
                    'dipole_amp': result.get('dipole_amp', 0.0),
                    'dipole_phase': result.get('dipole_phase', 0.0),
                    'quad_amp': result.get('quad_amp', 0.0),
                    'partial_interval': str(result.get('partial_interval', False)).lower()
                }
                writer.writerow(row)

        logger.info(f"Wrote {len(filtered_results)} rows to {output_path}")

    except Exception as e:
        logger.error(f"Failed to write dipole timeseries to {output_path}: {e}")
        raise
