"""
Data Quality Logging Module for Solar Flare - Geomagnetic Storm Correlation Project.

This module calculates and logs data quality metrics, specifically counts of missing
values for key predictors (CME speeds, flare fluxes) and alignment success rates.
It operates on the aligned events dataset produced by the US1 pipeline.
"""

import os
import sys
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/data_quality.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
ALIGNED_EVENTS_PATH = PROCESSED_DIR / "aligned_events.csv"
QUALITY_REPORT_PATH = PROCESSED_DIR / "data_quality_metrics.json"


def load_aligned_events(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load the aligned events CSV file.

    Args:
        filepath: Path to the aligned_events.csv file.

    Returns:
        List of dictionaries representing rows.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Aligned events file not found: {filepath}")

    events = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV file is empty or has no header.")
        
        for row in reader:
            events.append(row)

    if not events:
        logger.warning("Aligned events file contains no data rows.")
    
    return events


def calculate_missing_counts(events: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate counts of missing values for key predictor columns.

    Missing values are identified as empty strings, 'NaN', 'null', or None.

    Args:
        events: List of event dictionaries.

    Returns:
        Dictionary mapping column names to missing counts.
    """
    target_columns = [
        'cme_speed_kms', 
        'cme_width_deg', 
        'flare_flux_w_m2', 
        'flare_class',
        'dst_min'
    ]
    
    missing_counts = {col: 0 for col in target_columns}
    total_rows = len(events)

    for event in events:
        for col in target_columns:
            val = event.get(col, '')
            if val is None or str(val).strip() == '' or str(val).lower() in ('nan', 'null', 'none'):
                missing_counts[col] += 1

    return missing_counts, total_rows


def calculate_alignment_success_rate(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate the rate of successful solar event matching.

    Args:
        events: List of event dictionaries.

    Returns:
        Dictionary with total storms, matched storms, and success rate.
    """
    total_storms = len(events)
    if total_storms == 0:
        return {
            'total_storms': 0,
            'matched_storms': 0,
            'match_rate': 0.0,
            'unmatched_storms': 0
        }

    # A storm is considered "matched" if it has a non-null solar event identifier
    # Assuming 'flare_id' or 'cme_id' serves as the match indicator
    matched_count = 0
    for event in events:
        flare_id = event.get('flare_id', '')
        cme_id = event.get('cme_id', '')
        if flare_id and str(flare_id).strip() != '' or cme_id and str(cme_id).strip() != '':
            matched_count += 1

    match_rate = matched_count / total_storms if total_storms > 0 else 0.0

    return {
        'total_storms': total_storms,
        'matched_storms': matched_count,
        'unmatched_storms': total_storms - matched_count,
        'match_rate': round(match_rate, 4)
    }


def log_data_quality_metrics(events: List[Dict[str, Any]], output_path: Path) -> Dict[str, Any]:
    """
    Calculate all data quality metrics, log them, and save to a JSON report.

    Args:
        events: List of event dictionaries.
        output_path: Path to save the JSON report.

    Returns:
        The metrics dictionary.
    """
    logger.info("Starting data quality metrics calculation...")
    
    # Calculate missing counts
    missing_counts, total_rows = calculate_missing_counts(events)
    
    # Calculate alignment success
    alignment_stats = calculate_alignment_success_rate(events)

    # Compile metrics
    metrics = {
        'timestamp': datetime.utcnow().isoformat(),
        'dataset_source': str(ALIGNED_EVENTS_PATH),
        'total_records': total_rows,
        'missing_value_counts': missing_counts,
        'alignment_statistics': alignment_stats,
        'summary': {
            'highest_missing_rate_column': None,
            'highest_missing_rate_value': 0.0
        }
    }

    # Determine highest missing rate
    if total_rows > 0:
        max_col = None
        max_rate = 0.0
        for col, count in missing_counts.items():
            rate = count / total_rows
            if rate > max_rate:
                max_rate = rate
                max_col = col
        metrics['summary']['highest_missing_rate_column'] = max_col
        metrics['summary']['highest_missing_rate_value'] = round(max_rate, 4)

    # Log results
    logger.info(f"Total records processed: {total_rows}")
    logger.info(f"Missing value counts: {missing_counts}")
    logger.info(f"Alignment match rate: {alignment_stats['match_rate']:.2%}")
    
    if max_col and max_rate > 0.5:
        logger.warning(f"High missing rate ({max_rate:.2%}) detected in column: {max_col}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Data quality metrics report saved to: {output_path}")

    return metrics


def main():
    """
    Entry point for the data quality logging script.
    """
    logger.info(f"Data Quality Logger started.")
    
    if not ALIGNED_EVENTS_PATH.exists():
        logger.error(f"Required input file not found: {ALIGNED_EVENTS_PATH}")
        logger.error("Please ensure T017 (write_aligned_output) has completed successfully.")
        sys.exit(1)

    try:
        events = load_aligned_events(ALIGNED_EVENTS_PATH)
        metrics = log_data_quality_metrics(events, QUALITY_REPORT_PATH)
        logger.info("Data quality logging completed successfully.")
    except Exception as e:
        logger.error(f"Error during data quality logging: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
