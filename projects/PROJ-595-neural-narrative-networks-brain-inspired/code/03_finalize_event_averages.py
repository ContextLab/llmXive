"""
T021b: Finalize data/processed/event_averages.csv with columns:
subject_id, event_id, roi, mean_signal. Validate against schema.
Requires T021a completion (data/processed/event_averages_tmp.csv).
"""
import os
import sys
import json
import csv
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, info, error, warning, log_error
from utils.schema_validation import validate_neural_data
from config import get_config

logger = get_logger(__name__)

INPUT_FILE = project_root / "data" / "processed" / "event_averages_tmp.csv"
OUTPUT_FILE = project_root / "data" / "processed" / "event_averages.csv"
SCHEMA_PATH = project_root / "specs" / "001-neural-narrative-networks-brain-inspired" / "contracts" / "neural-data.schema.yaml"

def load_tmp_event_averages(input_path: Path) -> List[Dict[str, Any]]:
    """Load the temporary event averages from T021a."""
    if not input_path.exists():
        log_error("E001", f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    rows = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    if not rows:
        log_error("E002", f"Input file is empty: {input_path}")
        raise ValueError(f"Input file is empty: {input_path}")
    
    return rows

def finalize_event_averages(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ensure the rows have the exact required columns:
    subject_id, event_id, roi, mean_signal.
    Type coerce mean_signal to float.
    """
    required_cols = ['subject_id', 'event_id', 'roi', 'mean_signal']
    finalized = []
    
    for row in rows:
        # Check for missing keys
        missing = [col for col in required_cols if col not in row or row[col] is None]
        if missing:
            warning(f"Row missing columns {missing}, skipping: {row}")
            continue
        
        # Validate and coerce
        try:
            mean_signal = float(row['mean_signal'])
        except (ValueError, TypeError):
            warning(f"Invalid mean_signal value '{row['mean_signal']}', skipping row: {row}")
            continue
        
        finalized.append({
            'subject_id': str(row['subject_id']),
            'event_id': str(row['event_id']),
            'roi': str(row['roi']),
            'mean_signal': mean_signal
        })
    
    if not finalized:
        log_error("E002", "No valid rows found after finalization.")
        raise ValueError("No valid rows found after finalization.")
    
    return finalized

def save_finalized_csv(rows: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the finalized rows to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ['subject_id', 'event_id', 'roi', 'mean_signal']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    info(f"Saved {len(rows)} rows to {output_path}")

def validate_output(output_path: Path) -> bool:
    """Validate the output CSV against the neural-data schema."""
    if not output_path.exists():
        error(f"Output file does not exist for validation: {output_path}")
        return False
    
    # Use the schema validation utility
    is_valid = validate_neural_data(str(output_path))
    if is_valid:
        info(f"Validation passed for {output_path}")
    else:
        error(f"Validation failed for {output_path}")
    
    return is_valid

def main():
    config = get_config()
    logger.info(f"Starting T021b: Finalize event averages (seed={config['random_seed']})")
    
    try:
        # 1. Load temporary data from T021a
        logger.info(f"Loading temporary data from {INPUT_FILE}")
        tmp_rows = load_tmp_event_averages(INPUT_FILE)
        logger.info(f"Loaded {len(tmp_rows)} rows from temporary file")
        
        # 2. Finalize format
        logger.info("Finalizing event averages format...")
        final_rows = finalize_event_averages(tmp_rows)
        logger.info(f"Finalized {len(final_rows)} valid rows")
        
        # 3. Save to final destination
        logger.info(f"Saving to {OUTPUT_FILE}")
        save_finalized_csv(final_rows, OUTPUT_FILE)
        
        # 4. Validate against schema
        logger.info("Validating output against schema...")
        if not validate_output(OUTPUT_FILE):
            log_error("E001", "Schema validation failed for event_averages.csv")
            sys.exit(1)
        
        logger.info("T021b completed successfully.")
        
    except FileNotFoundError as e:
        log_error("E001", str(e))
        sys.exit(1)
    except ValueError as e:
        log_error("E002", str(e))
        sys.exit(1)
    except Exception as e:
        log_error("E001", f"Unexpected error during T021b: {str(e)}")
        raise

if __name__ == "__main__":
    main()