"""
Module for logging data quality metrics for the solar flare and geomagnetic storm correlation project.

This module calculates counts of missing values for key predictors (CME speeds, flares, etc.)
and alignment success rates, writing the metrics to a log file.
"""
import os
import sys
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
LOG_DIR = Path("results")
LOG_FILE = LOG_DIR / "data_quality.log"

def ensure_log_directory():
    """Ensure the log directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging():
    """Configure logging to write to both file and console."""
    ensure_log_directory()
    
    # Clear existing handlers to avoid duplicates in repeated runs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_aligned_events(file_path: str = "data/processed/aligned_events.csv") -> List[Dict[str, Any]]:
    """
    Load the aligned events dataset from the specified CSV file.
    
    Args:
        file_path: Path to the aligned events CSV file.
        
    Returns:
        List of dictionaries representing the rows in the CSV.
        
    Raises:
        FileNotFoundError: If the specified file does not exist.
        Exception: If there is an error reading the file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Aligned events file not found: {file_path}")
    
    data = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except Exception as e:
        logging.error(f"Error reading aligned events file: {e}")
        raise
    
    return data

def calculate_missing_counts(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Calculate the count of missing values for key predictor columns.
    
    Args:
        data: List of dictionaries representing the rows in the aligned events dataset.
        
    Returns:
        Dictionary mapping column names to their missing value counts.
    """
    # Define key predictor columns to check for missing values
    key_columns = [
        'cme_speed', 
        'cme_width', 
        'flare_flux', 
        'flare_class',
        'dst_min',
        'kp_max'
    ]
    
    missing_counts = {col: 0 for col in key_columns}
    total_rows = len(data)
    
    for row in data:
        for col in key_columns:
            value = row.get(col, '')
            # Check for various representations of missing data
            if value is None or value == '' or value == 'nan' or value == 'NaN' or value == 'null':
                missing_counts[col] += 1
    
    missing_counts['total_rows'] = total_rows
    return missing_counts

def calculate_alignment_success_rate(data: List[Dict[str, Any]], match_column: str = 'solar_event_id') -> Dict[str, Any]:
    """
    Calculate the success rate of aligning solar events with geomagnetic storms.
    
    Args:
        data: List of dictionaries representing the rows in the aligned events dataset.
        match_column: The column name that indicates a successful match (e.g., 'solar_event_id').
        
    Returns:
        Dictionary containing the alignment success rate and counts.
    """
    if not data:
        return {
            'total_events': 0,
            'matched_events': 0,
            'unmatched_events': 0,
            'success_rate': 0.0
        }
    
    total_events = len(data)
    matched_events = sum(1 for row in data if row.get(match_column) and row.get(match_column) not in ['', 'nan', 'NaN', 'null'])
    unmatched_events = total_events - matched_events
    success_rate = (matched_events / total_events) * 100 if total_events > 0 else 0.0
    
    return {
        'total_events': total_events,
        'matched_events': matched_events,
        'unmatched_events': unmatched_events,
        'success_rate': success_rate
    }

def log_data_quality_metrics(data: List[Dict[str, Any]], output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate and log comprehensive data quality metrics.
    
    Args:
        data: List of dictionaries representing the rows in the aligned events dataset.
        output_file: Optional path to write the metrics to a JSON file.
        
    Returns:
        Dictionary containing all calculated metrics.
    """
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("DATA QUALITY METRICS REPORT")
    logger.info("=" * 60)
    
    # Calculate missing counts
    missing_counts = calculate_missing_counts(data)
    logger.info("\nMISSING VALUE COUNTS:")
    logger.info(f"Total rows: {missing_counts['total_rows']}")
    for col, count in missing_counts.items():
        if col != 'total_rows':
            percentage = (count / missing_counts['total_rows'] * 100) if missing_counts['total_rows'] > 0 else 0
            logger.info(f"  {col}: {count} ({percentage:.2f}%)")
    
    # Calculate alignment success rate
    alignment_stats = calculate_alignment_success_rate(data)
    logger.info("\nALIGNMENT SUCCESS RATE:")
    logger.info(f"  Total events: {alignment_stats['total_events']}")
    logger.info(f"  Matched events: {alignment_stats['matched_events']}")
    logger.info(f"  Unmatched events: {alignment_stats['unmatched_events']}")
    logger.info(f"  Success rate: {alignment_stats['success_rate']:.2f}%")
    
    # Calculate recurrent activity flag statistics
    recurrent_count = sum(1 for row in data if row.get('is_recurrent', 'False') in ['True', 'true', '1', 1])
    total_rows = len(data)
    recurrent_percentage = (recurrent_count / total_rows * 100) if total_rows > 0 else 0
    logger.info("\nRECURRENT ACTIVITY STATISTICS:")
    logger.info(f"  Recurrent events: {recurrent_count}")
    logger.info(f"  Non-recurrent events: {total_rows - recurrent_count}")
    logger.info(f"  Recurrent percentage: {recurrent_percentage:.2f}%")
    
    # Prepare metrics dictionary
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'missing_counts': missing_counts,
        'alignment_stats': alignment_stats,
        'recurrent_stats': {
            'recurrent_count': recurrent_count,
            'non_recurrent_count': total_rows - recurrent_count,
            'recurrent_percentage': recurrent_percentage
        }
    }
    
    # Write to JSON file if output_file is specified
    if output_file:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"\nMetrics written to: {output_file}")
    
    logger.info("=" * 60)
    
    return metrics

def main():
    """Main entry point for the data quality logging script."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load aligned events data
        logger.info("Loading aligned events data...")
        aligned_events_path = "data/processed/aligned_events.csv"
        data = load_aligned_events(aligned_events_path)
        logger.info(f"Loaded {len(data)} events from {aligned_events_path}")
        
        # Log data quality metrics
        metrics_output_path = "results/data_quality_metrics.json"
        log_data_quality_metrics(data, output_file=metrics_output_path)
        
        logger.info("Data quality logging completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()