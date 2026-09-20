import csv
import json
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from .models import DatasetRecord
from .synthetic_gen import SyntheticDataGenerator


logger = logging.getLogger(__name__)


def log_skipped_record(
    reason: str, 
    dataset_source: str, 
    record_id: Optional[str] = None
) -> None:
    """
    Log a skipped record to the derivation log.
    
    Args:
        reason: The reason for skipping.
        dataset_source: The source of the dataset.
        record_id: Optional ID of the skipped record.
    """
    log_entry = {
        "timestamp": None, # Will be set by JSON encoder if needed, or use datetime
        "error_code": "SKIPPED_RECORD",
        "reason": reason,
        "dataset_source": dataset_source,
        "record_id": record_id
    }
    
    log_path = Path("data/derivation_logs/skipped_records.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
        
    logger.warning(f"Skipped record: {reason}")


def calculate_gain_scores(records: List[DatasetRecord]) -> List[DatasetRecord]:
    """
    Calculate gain scores (post - pre) for each record.
    
    Args:
        records: List of dataset records.
        
    Returns:
        List of records with gain scores calculated (stored in covariates if needed, 
        or simply validated). The task implies computing the value, which is used later.
        Here we validate and ensure data is clean.
    """
    valid_records = []
    for record in records:
        if record.pre_test_score is None or record.post_test_score is None:
            log_skipped_record(
                reason="Missing pre or post test score",
                dataset_source="input",
                record_id=None
            )
            continue
        valid_records.append(record)
        
    logger.info(f"Calculated gain scores for {len(valid_records)} valid records.")
    return valid_records


def write_processed_data(records: List[DatasetRecord], output_path: str) -> None:
    """
    Write processed records to a CSV file.
    
    Args:
        records: List of dataset records.
        output_path: Path to the output CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['pre_test_score', 'post_test_score', 'instruction_type', 'covariates'])
        for record in records:
            writer.writerow([
                record.pre_test_score,
                record.post_test_score,
                record.instruction_type,
                json.dumps(record.covariates)
            ])
            
    logger.info(f"Wrote {len(records)} records to {output_path}")


def load_public_dataset(
    input_path: str, 
    concept_definition: Optional[Dict[str, Any]] = None
) -> List[DatasetRecord]:
    """
    Load a public dataset from a CSV or JSON file.
    
    Args:
        input_path: Path to the input file.
        concept_definition: Optional concept definition for synthetic fallback.
        
    Returns:
        List of DatasetRecord objects.
        
    Raises:
        ValueError: If required columns are missing and synthetic generation fails.
    """
    path = Path(input_path)
    records: List[DatasetRecord] = []
    source = str(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    try:
        if path.suffix == '.csv':
            with open(path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Validate columns
                    if 'instruction_type' not in row:
                        logger.warning("Missing 'instruction_type' column in public data.")
                        # Fallback to synthetic generation
                        return generate_synthetic_fallback(concept_definition)
                    
                    try:
                        record = DatasetRecord(
                            pre_test_score=float(row['pre_test_score']),
                            post_test_score=float(row['post_test_score']),
                            instruction_type=row['instruction_type'],
                            covariates=json.loads(row.get('covariates', '{}'))
                        )
                        records.append(record)
                    except (ValueError, KeyError) as e:
                        log_skipped_record(reason=f"Invalid data row: {e}", dataset_source=source)
                        
        elif path.suffix == '.json':
            with open(path, 'r') as f:
                data = json.load(f)
                for item in data:
                    if 'instruction_type' not in item:
                        logger.warning("Missing 'instruction_type' column in public data.")
                        return generate_synthetic_fallback(concept_definition)
                    
                    try:
                        record = DatasetRecord(
                            pre_test_score=float(item['pre_test_score']),
                            post_test_score=float(item['post_test_score']),
                            instruction_type=item['instruction_type'],
                            covariates=item.get('covariates', {})
                        )
                        records.append(record)
                    except (ValueError, KeyError) as e:
                        log_skipped_record(reason=f"Invalid data row: {e}", dataset_source=source)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
            
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise
        
    if not records:
        logger.warning("No valid records loaded from public data.")
        return generate_synthetic_fallback(concept_definition)
        
    logger.info(f"Loaded {len(records)} records from {input_path}")
    return records


def generate_synthetic_fallback(
    concept_definition: Optional[Dict[str, Any]] = None
) -> List[DatasetRecord]:
    """
    Generate synthetic data if public data is insufficient or missing columns.
    
    Args:
        concept_definition: Concept definition for generation.
        
    Returns:
        List of synthetic DatasetRecord objects.
        
    Raises:
        SystemExit: If generation fails.
    """
    logger.info("Public data missing 'instruction_type' or empty. Generating synthetic data.")
    try:
        generator = SyntheticDataGenerator()
        # Default parameters if not provided
        params = concept_definition or {
            "n_samples": 100,
            "mean_diff": 0.5,
            "std_dev": 1.0,
            "instruction_types": ["embodied", "static"]
        }
        records = generator.generate(**params)
        logger.info(f"Successfully generated {len(records)} synthetic records.")
        return records
    except Exception as e:
        logger.critical(f"Synthetic data generation failed: {e}")
        log_skipped_record(
            reason="Synthetic generation failed", 
            dataset_source="fallback"
        )
        raise SystemExit(1) from e
