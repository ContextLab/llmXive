import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure required output directories exist."""
    data_processed = Path("data/processed")
    data_processed.mkdir(parents=True, exist_ok=True)
    return data_processed

def get_subject_list_from_download_log() -> List[Dict[str, Any]]:
    """
    Read the list of subjects from the download log.
    Expects data/processed/download_log.json to exist with a 'subjects' key.
    """
    log_path = Path("data/processed/download_log.json")
    if not log_path.exists():
        logger.error(f"Download log not found at {log_path}. Run download.py first.")
        return []
    
    try:
        with open(log_path, 'r') as f:
            data = json.load(f)
        return data.get("subjects", [])
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse download log: {e}")
        return []

def load_graph_metrics() -> List[Dict[str, Any]]:
    """
    Load the aggregated graph metrics from data/processed/graph_metrics.csv.
    Returns a list of dictionaries.
    """
    metrics_path = Path("data/processed/graph_metrics.csv")
    if not metrics_path.exists():
        logger.error(f"Graph metrics file not found at {metrics_path}. Run graph_metrics.py first.")
        return []
    
    metrics = []
    try:
        with open(metrics_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                row_copy = dict(row)
                if 'value' in row_copy:
                    row_copy['value'] = float(row_copy['value'])
                if 'fluid_intelligence_score' in row_copy:
                    try:
                        row_copy['fluid_intelligence_score'] = float(row_copy['fluid_intelligence_score'])
                    except (ValueError, TypeError):
                        row_copy['fluid_intelligence_score'] = None
                metrics.append(row_copy)
    except Exception as e:
        logger.error(f"Failed to load graph metrics: {e}")
        return []
    
    return metrics

def validate_and_aggregate() -> bool:
    """
    Validate that subjects have valid Fluid Intelligence scores.
    
    Logic:
    1. Get list of subjects from download_log.json.
    2. Load graph_metrics.csv.
    3. Check if 'fluid_intelligence_score' column exists and is not null for at least one subject.
    
    If NO valid scores are found, raise a critical error (halt).
    If at least one valid score exists, log success and return True.
    """
    subjects = get_subject_list_from_download_log()
    if not subjects:
        logger.error("No subjects found in download log. Cannot validate.")
        return False

    metrics = load_graph_metrics()
    if not metrics:
        logger.error("No graph metrics found. Cannot validate.")
        return False

    # Check for the presence of the column in the CSV headers first
    if not metrics:
        # If file is empty but exists, we treat it as 0 valid scores
        logger.error("Graph metrics file is empty or has no data rows.")
        raise ValueError("No valid Fluid Intelligence scores found for correlation analysis")

    # Check if the column exists
    sample_row = metrics[0]
    if 'fluid_intelligence_score' not in sample_row:
        logger.error("Column 'fluid_intelligence_score' is missing from graph_metrics.csv")
        raise ValueError("No valid Fluid Intelligence scores found for correlation analysis (column missing)")

    # Count valid scores
    valid_count = 0
    invalid_count = 0
    valid_subject_ids = []

    for row in metrics:
        score = row.get('fluid_intelligence_score')
        sub_id = row.get('subject_id', 'Unknown')
        
        # Check if score is None, 'None', or empty string
        if score is None or score == '' or str(score).lower() == 'nan':
            invalid_count += 1
        else:
            try:
                val = float(score)
                if not (val != val): # Check for NaN explicitly
                    valid_count += 1
                    valid_subject_ids.append(sub_id)
                else:
                    invalid_count += 1
            except (ValueError, TypeError):
                invalid_count += 1

    logger.info(f"Validation Results: {valid_count} valid scores, {invalid_count} invalid/missing.")
    
    if valid_count == 0:
        error_msg = "No valid Fluid Intelligence scores found for correlation analysis. Halting execution."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Success: Found {valid_count} subjects with valid Fluid Intelligence scores.")
    return True

def main():
    """Entry point for the validation script."""
    try:
        ensure_directories()
        if validate_and_aggregate():
            logger.info("Validation passed. Proceeding to analysis.")
            sys.exit(0)
    except ValueError as e:
        logger.critical(str(e))
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
