import csv
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure logging is configured for this module if not already done
def setup_logging(log_file: str = "logs/pipeline.log"):
    """Configure logging to file and console."""
    Path("logs").mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SPOT_CHECK_DIR = DATA_DIR / "spot_check"
PROCESSED_DIR = DATA_DIR / "processed"

class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass

def load_processed_data(filepath: str) -> List[Dict[str, Any]]:
    """Load processed PR data from CSV."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def load_annotations(filepath: str) -> List[Dict[str, Any]]:
    """
    Load human annotations from CSV.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        DataValidationError: If the file is empty or schema is invalid.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Annotations file not found: {filepath}")
    
    if path.stat().st_size == 0:
        raise DataValidationError(f"Annotations file is empty: {filepath}")
    
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Validate header
        if 'pr_id' not in reader.fieldnames or 'is_ai_assisted' not in reader.fieldnames:
            raise DataValidationError(f"Invalid schema in annotations file. Expected 'pr_id' and 'is_ai_assisted'. Found: {reader.fieldnames}")
        
        for row in reader:
            data.append(row)
    
    if not data:
        raise DataValidationError(f"Annotations file contains no data rows: {filepath}")
        
    return data

def calculate_false_negative_rate(processed_data: List[Dict], annotations: List[Dict]) -> float:
    """
    Calculate the false-negative rate based on processed data and human annotations.
    
    False Negative in this context:
    The model (heuristic) classified a PR as NON-AI (0), but the human annotator
    confirmed it was AI-assisted (1).
    
    Returns:
        float: The calculated false-negative rate (0.0 to 1.0).
    """
    # Create a lookup map for annotations
    annotation_map = {ann['pr_id']: int(ann['is_ai_assisted']) for ann in annotations}
    
    false_negatives = 0
    total_checked = 0
    
    for pr in processed_data:
        pr_id = pr.get('pr_id')
        if pr_id in annotation_map:
            total_checked += 1
            model_label = int(pr.get('is_ai_assisted', 0))
            human_label = annotation_map[pr_id]
            
            # False Negative: Model said 0 (Non-AI), Human said 1 (AI)
            if model_label == 0 and human_label == 1:
                false_negatives += 1
    
    if total_checked == 0:
        logger.warning("No overlapping PRs found between processed data and annotations.")
        return 0.0
        
    return false_negatives / total_checked

def handle_missing_annotations():
    """
    Handle the case where annotations are missing or empty.
    Logs a CRITICAL warning and sets status to UNVALIDATED.
    """
    logger.critical("ANNOTATIONS MISSING OR EMPTY: Validation cannot be performed.")
    logger.critical("Proceeding with heuristic-only classification. Status: UNVALIDATED")
    
    # Create a minimal validation report indicating failure
    report = {
        "status": "UNVALIDATED",
        "reason": "Annotations file missing or empty",
        "false_negative_rate": None,
        "sample_size": 0,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    output_path = SPOT_CHECK_DIR / "validation_report.csv"
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["status", "reason", "false_negative_rate", "sample_size", "timestamp"])
        writer.writeheader()
        writer.writerow(report)
    
    logger.info(f"Validation report saved to {output_path}")
    return report

def save_validation_report(report_data: Dict[str, Any], output_path: str):
    """Save the validation report to a CSV file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["status", "false_negative_rate", "sample_size", "timestamp"])
        writer.writeheader()
        writer.writerow(report_data)
    logger.info(f"Validation report saved to {output_path}")

def main():
    """
    Main entry point for T019e: Ingest Real Annotations.
    
    Logic:
    1. Check if data/spot_check/annotations.csv exists.
    2. If missing/empty -> Log CRITICAL, save UNVALIDATED report, exit.
    3. If exists -> Load annotations, load processed data, calculate FNR, save report.
    """
    annotations_path = SPOT_CHECK_DIR / "annotations.csv"
    processed_data_path = PROCESSED_DIR / "pr_turnaround.csv"
    report_path = SPOT_CHECK_DIR / "validation_report.csv"
    
    logger.info(f"Starting validation ingestion. Looking for: {annotations_path}")
    
    # Step 1: Check for existence
    if not annotations_path.exists():
        logger.critical(f"File not found: {annotations_path}")
        handle_missing_annotations()
        return
    
    if annotations_path.stat().st_size == 0:
        logger.critical(f"File is empty: {annotations_path}")
        handle_missing_annotations()
        return
    
    # Step 2: Load Annotations
    try:
        annotations = load_annotations(str(annotations_path))
        logger.info(f"Successfully loaded {len(annotations)} annotations.")
    except DataValidationError as e:
        logger.critical(f"Data validation error: {e}")
        handle_missing_annotations()
        return
    
    # Step 3: Load Processed Data
    try:
        processed_data = load_processed_data(str(processed_data_path))
        logger.info(f"Successfully loaded {len(processed_data)} processed PR records.")
    except FileNotFoundError as e:
        logger.critical(f"Cannot proceed without processed data: {e}")
        raise e
    
    # Step 4: Calculate False Negative Rate
    fn_rate = calculate_false_negative_rate(processed_data, annotations)
    logger.info(f"Calculated False Negative Rate: {fn_rate:.4f}")
    
    # Step 5: Save Report
    report_data = {
        "status": "VALIDATED",
        "false_negative_rate": f"{fn_rate:.4f}",
        "sample_size": len(annotations),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    save_validation_report(report_data, str(report_path))
    
    # Log final status
    if fn_rate > 0.10:
        logger.warning(f"High False Negative Rate detected: {fn_rate:.4f} > 0.10. Limitation will be injected in report.")
    else:
        logger.info("False Negative Rate within acceptable limits.")

if __name__ == "__main__":
    main()