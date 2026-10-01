import os
import sys
import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for file paths
RAW_LABELS_PATH = Path("data/processed/raw_labels.csv")
NULL_LABELS_PATH = Path("data/processed/null_labels.csv")
FINAL_LABELS_PATH = Path("data/processed/labels.csv")
EXCLUDED_LOG_PATH = Path("data/processed/excluded_samples.log")
CONFIDENCE_THRESHOLD = 0.9

def load_raw_labels(filepath: Path) -> List[Dict[str, Any]]:
    """
    Load raw labels from CSV.
    
    Args:
        filepath: Path to raw_labels.csv
        
    Returns:
        List of dictionaries containing clip_id, label, confidence_score, and reason (if applicable)
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Raw labels file not found at {filepath}")
    
    records = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure numeric conversion for confidence
            try:
                row['confidence_score'] = float(row.get('confidence_score', 0.0))
            except (ValueError, TypeError):
                row['confidence_score'] = 0.0
            
            # Normalize reason field if missing
            if 'reason' not in row or row['reason'] is None:
                row['reason'] = ""
                
            records.append(row)
    
    logger.info(f"Loaded {len(records)} records from {filepath}")
    return records

def process_labels_and_exclusions(
    records: List[Dict[str, Any]], 
    threshold: float = CONFIDENCE_THRESHOLD
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Separate records into valid labels and null/excluded samples.
    
    Args:
        records: List of raw label records
        threshold: Minimum confidence score to be considered valid
        
    Returns:
        Tuple of (valid_labels, null_samples)
    """
    valid_labels = []
    null_samples = []
    
    for record in records:
        confidence = record.get('confidence_score', 0.0)
        reason = record.get('reason', "").strip()
        simulation_failed = record.get('simulation_failed', False)
        
        is_null = False
        exclusion_reason = ""
        
        # Check confidence threshold
        if confidence < threshold:
            is_null = True
            exclusion_reason = f"Low confidence ({confidence:.4f} < {threshold})"
        
        # Check for simulation failure
        if simulation_failed:
            is_null = True
            exclusion_reason = "Simulation failure"
        
        # Check for explicit reason provided in raw data
        if reason:
            is_null = True
            exclusion_reason = reason
        
        if is_null:
            null_samples.append({
                'clip_id': record['clip_id'],
                'reason': exclusion_reason,
                'confidence_score': confidence
            })
        else:
            # Keep only necessary fields for final labels
            valid_labels.append({
                'clip_id': record['clip_id'],
                'label': record['label'],
                'confidence_score': confidence
            })
    
    logger.info(f"Processed {len(records)} records: {len(valid_labels)} valid, {len(null_samples)} null")
    return valid_labels, null_samples

def save_null_labels(records: List[Dict[str, Any]], filepath: Path) -> None:
    """
    Save null/excluded samples to CSV.
    
    Args:
        records: List of null sample records
        filepath: Output path for null_labels.csv
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['clip_id', 'reason', 'confidence_score'])
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Saved {len(records)} null samples to {filepath}")

def save_final_labels(records: List[Dict[str, Any]], filepath: Path) -> None:
    """
    Save valid labels to final CSV.
    
    Args:
        records: List of valid label records
        filepath: Output path for labels.csv
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['clip_id', 'label', 'confidence_score'])
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Saved {len(records)} valid labels to {filepath}")

def save_excluded_log(null_samples: List[Dict[str, Any]], filepath: Path) -> None:
    """
    Create an exclusion log file. If no samples are excluded, creates an empty file
    to ensure consistent hashing as per requirements.
    
    Args:
        null_samples: List of null samples
        filepath: Output path for excluded_samples.log
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        if not null_samples:
            # Create empty file if no exclusions
            pass
        else:
            for sample in null_samples:
                f.write(f"{sample['clip_id']}|{sample['reason']}|{sample['confidence_score']}\n")
    
    logger.info(f"Created exclusion log at {filepath} with {len(null_samples)} entries")

def main():
    """
    Main entry point for separating null samples from raw labels.
    """
    logger.info("Starting null sample separation process...")
    
    try:
        # Load raw labels
        raw_records = load_raw_labels(RAW_LABELS_PATH)
        
        if not raw_records:
            logger.warning("Raw labels file is empty. Creating empty output files.")
            save_null_labels([], NULL_LABELS_PATH)
            save_final_labels([], FINAL_LABELS_PATH)
            save_excluded_log([], EXCLUDED_LOG_PATH)
            return

        # Process and separate
        valid_labels, null_samples = process_labels_and_exclusions(raw_records)
        
        # Save artifacts
        save_null_labels(null_samples, NULL_LABELS_PATH)
        save_final_labels(valid_labels, FINAL_LABELS_PATH)
        save_excluded_log(null_samples, EXCLUDED_LOG_PATH)
        
        logger.info("Null sample separation completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during processing: {e}")
        raise

if __name__ == "__main__":
    main()
