import csv
import json
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import DatasetRecord
from .synthetic_gen import SyntheticDataGenerator, generate_mapping_log

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ['pre_test_score', 'post_test_score', 'instruction_type']

def log_skipped_record(record_id: Optional[str], reason: str, source: str = "unknown"):
    """
    Logs a skipped record to the derivation logs.
    
    Args:
        record_id: The ID of the skipped record.
        reason: The reason for skipping.
        source: The source dataset or file.
    """
    log_entry = {
        "timestamp": logging.Formatter('%Y-%m-%d %H:%M:%S').format(logging.LogRecord('', logging.INFO, '', 0, '', (), None)),
        "record_id": record_id,
        "reason": reason,
        "source": source
    }
    log_file_path = Path("data/derivation_logs/skipped_records.log")
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file_path, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    logger.warning(f"Skipped record {record_id} from {source}: {reason}")

def calculate_gain_scores(records: List[DatasetRecord]) -> List[DatasetRecord]:
    """
    Calculates gain scores (post - pre) for each record.
    Skips records with missing values and logs them.
    
    Args:
        records: List of DatasetRecord objects.
        
    Returns:
        List of DatasetRecord objects with gain scores calculated.
    """
    processed_records = []
    for i, record in enumerate(records):
        pre = record.pre_test_score
        post = record.post_test_score
        
        if pre is None or post is None:
            log_skipped_record(record_id=str(i), reason="Missing pre or post test score", source="input_data")
            continue
        
        # Create a new record with gain score
        # Note: DatasetRecord might need a gain_score field if not present. 
        # Assuming we store it in covariates or a new field if we modify the dataclass.
        # For now, we assume the record is updated or we create a new structure.
        # Let's assume we add gain_score to the record if possible, or just process it.
        # Since we can't easily modify the dataclass instance fields without redefinition,
        # we will log the gain or assume the downstream consumer handles it.
        # However, the task implies we compute it. Let's add it to covariates if needed, 
        # or assume the record object is mutable and we add a property.
        # Given the constraints, let's assume we just return the list and log the gain.
        # But to be useful, let's assume we are updating the record's internal state 
        # or we are just filtering. The prompt says "compute... excluding rows".
        
        gain = post - pre
        # We will store the gain in the record's covariates for now if it's not there,
        # or assume the record object has a gain_score attribute added dynamically.
        # A safer approach for the dataclass is to assume we are just validating 
        # and returning the list, but the task says "compute".
        # Let's add a dynamic attribute for gain_score.
        record.gain_score = gain
        processed_records.append(record)
        
        logger.info(f"Calculated gain score for record {i}: {gain}")
    
    return processed_records

def write_processed_data(records: List[DatasetRecord], output_path: str):
    """
    Writes processed records to a CSV file.
    
    Args:
        records: List of DatasetRecord objects.
        output_path: Path to the output CSV file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not records:
        logger.warning("No records to write.")
        return

    fieldnames = ['pre_test_score', 'post_test_score', 'instruction_type', 'gain_score']
    # Add covariates keys if present
    if records and records[0].covariates:
        fieldnames.extend(records[0].covariates.keys())

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for record in records:
            row = {
                'pre_test_score': record.pre_test_score,
                'post_test_score': record.post_test_score,
                'instruction_type': record.instruction_type,
                'gain_score': getattr(record, 'gain_score', None)
            }
            if record.covariates:
                row.update(record.covariates)
            writer.writerow(row)
    
    logger.info(f"Wrote {len(records)} processed records to {output_path}")

def load_public_dataset(input_path: str) -> List[DatasetRecord]:
    """
    Loads a public dataset from CSV or JSON.
    Validates required columns.
    If 'instruction_type' is missing, invokes SyntheticDataGenerator.
    
    Args:
        input_path: Path to the input file.
        
    Returns:
        List of DatasetRecord objects.
        
    Raises:
        ValueError: If required columns are missing and fallback fails.
    """
    logger.info(f"Attempting to load public dataset from {input_path}")
    path = Path(input_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    records = []
    data = []

    if path.suffix == '.csv':
        with open(path, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
    elif path.suffix == '.json':
        with open(path, 'r') as f:
            data = json.load(f)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

    if not data:
        logger.warning("Dataset is empty.")
        return []

    # Check for required columns
    first_row = data[0]
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in first_row]

    if missing_cols:
        logger.warning(f"Missing required columns: {missing_cols}")
        if 'instruction_type' in missing_cols:
            logger.info("Missing 'instruction_type'. Invoking SyntheticDataGenerator fallback.")
            return generate_synthetic_fallback()
        else:
            # If other columns are missing, we cannot proceed
            handle_synthetic_fallback_failure("Missing critical columns other than instruction_type")

    for i, row in enumerate(data):
        try:
            record = DatasetRecord(
                pre_test_score=float(row['pre_test_score']),
                post_test_score=float(row['post_test_score']),
                instruction_type=row['instruction_type'],
                covariates={k: v for k, v in row.items() if k not in REQUIRED_COLUMNS}
            )
            records.append(record)
        except (ValueError, KeyError) as e:
            log_skipped_record(str(i), str(e), source=input_path)

    logger.info(f"Successfully loaded {len(records)} records from {input_path}")
    return records

def generate_synthetic_fallback() -> List[DatasetRecord]:
    """
    Generates synthetic data when public data lacks 'instruction_type'.
    """
    logger.info("Generating synthetic fallback data.")
    generator = SyntheticDataGenerator(seed=42)
    # Generate a reasonable sample size for validation
    records = generator.generate(n_samples=1000)
    
    # Generate mapping log as required by Constitution Principle VI
    # This is skipped if --mode=secondary_analysis, but here we are in fallback mode
    # which implies we are not in secondary analysis (since we have data but missing type)
    # So we generate the log.
    try:
        generate_mapping_log("data/synthetic/mapping_log.json")
        logger.info("Generated mapping_log.json for synthetic data.")
    except Exception as e:
        logger.error(f"Failed to generate mapping_log.json: {e}")
        # Continue anyway, but log the error

    return records

def handle_synthetic_fallback_failure(reason: str):
    """
    Handles failure of synthetic data generation or missing critical columns.
    Logs error and exits.
    
    Args:
        reason: The reason for failure.
    """
    error_msg = f"CRITICAL ERROR: {reason}. Primary research question cannot be answered."
    logger.error(error_msg)
    
    # Log to derivation log
    log_entry = {
        "timestamp": logging.Formatter('%Y-%m-%d %H:%M:%S').format(logging.LogRecord('', logging.ERROR, '', 0, '', (), None)),
        "error_code": "FALLBACK_FAILURE",
        "reason": reason,
        "dataset_source": "unknown"
    }
    log_file_path = Path("data/derivation_logs/skipped_records.log")
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file_path, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    sys.exit(1)

def main():
    # Placeholder for direct execution if needed
    pass
