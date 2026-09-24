import csv
import json
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import DatasetRecord
from .synthetic_gen import SyntheticDataGenerator
from .utils import set_seed
from .logging_config import setup_logging

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["pre_test_score", "post_test_score", "instruction_type"]
SKIPPED_LOG_PATH = Path("data/derivation_logs/skipped_records.log")

def log_skipped_record(record: Dict[str, Any], reason: str) -> None:
    """Log a skipped record to the derivation log in JSONL format."""
    SKIPPED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_entry = {
        "timestamp": record.get("timestamp", ""),
        "error_code": "DATA_SKIP",
        "reason": reason,
        "record_preview": record
    }
    with open(SKIPPED_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    logger.warning(f"Skipped record: {reason}")

def handle_synthetic_fallback_failure(dataset_source: str) -> None:
    """Handle the case where synthetic generation fails. Exits with code 1."""
    error_msg = "Primary research question cannot be answered: missing instruction_type and synthetic generation failed"
    logger.error(error_msg)
    
    # Log to derivation log
    SKIPPED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_entry = {
        "timestamp": "",
        "error_code": "FALLBACK_FAILED",
        "reason": "synthetic_gen_failed",
        "dataset_source": dataset_source
    }
    with open(SKIPPED_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    sys.exit(1)

def load_public_dataset(file_path: str) -> List[DatasetRecord]:
    """
    Load a public dataset from a CSV or JSON file.
    
    Args:
        file_path: Path to the CSV or JSON file.
        
    Returns:
        List of DatasetRecord objects.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    data: List[Dict[str, Any]] = []
    
    if path.suffix.lower() == ".csv":
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            data = list(reader)
    elif path.suffix.lower() in [".json", ".jsonl"]:
        with open(path, "r", encoding="utf-8") as f:
            if path.suffix == ".json":
                data = json.load(f)
            else:
                data = [json.loads(line) for line in f if line.strip()]
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    # Validate required columns
    if data:
        first_record = data[0]
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in first_record]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
    
    return [
        DatasetRecord(
            pre_test_score=float(r.get("pre_test_score", 0)),
            post_test_score=float(r.get("post_test_score", 0)),
            instruction_type=str(r.get("instruction_type", "unknown")),
            covariates={k: v for k, v in r.items() if k not in REQUIRED_COLUMNS}
        )
        for r in data
    ]

def generate_synthetic_fallback(n: int, seed: int, mean_diff_embodied: float, mean_diff_static: float) -> List[DatasetRecord]:
    """
    Generate synthetic data as a fallback when public data lacks instruction_type.
    
    Args:
        n: Number of records to generate.
        seed: Random seed for reproducibility.
        mean_diff_embodied: Mean difference for embodied group.
        mean_diff_static: Mean difference for static group.
        
    Returns:
        List of DatasetRecord objects.
    """
    set_seed(seed)
    generator = SyntheticDataGenerator()
    return generator.generate(n=n, seed=seed, mean_diff_embodied=mean_diff_embodied, mean_diff_static=mean_diff_static)

def calculate_gain_scores(records: List[DatasetRecord]) -> List[DatasetRecord]:
    """
    Calculate gain scores (post - pre) for each record.
    Logs records with missing values to the derivation log.
    
    Args:
        records: List of DatasetRecord objects.
        
    Returns:
        List of DatasetRecord objects with gain scores calculated.
    """
    processed_records = []
    for i, record in enumerate(records):
        pre = record.pre_test_score
        post = record.post_test_score
        
        if pre is None or post is None or (isinstance(pre, float) and (pre != pre)) or (isinstance(post, float) and (post != post)):
            log_skipped_record({"index": i, "pre": pre, "post": post}, "missing_or_nan_scores")
            continue
        
        gain = post - pre
        processed_records.append(DatasetRecord(
            pre_test_score=pre,
            post_test_score=post,
            instruction_type=record.instruction_type,
            covariates=record.covariates,
            gain_score=gain
        ))
    
    return processed_records

def write_processed_data(records: List[DatasetRecord], output_path: str) -> None:
    """
    Write processed records to a CSV file.
    
    Args:
        records: List of DatasetRecord objects.
        output_path: Path to the output CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["pre_test_score", "post_test_score", "instruction_type", "gain_score"])
        for record in records:
            writer.writerow([
                record.pre_test_score,
                record.post_test_score,
                record.instruction_type,
                getattr(record, "gain_score", None)
            ])
    logger.info(f"Wrote {len(records)} records to {output_path}")

def load_public_dataset_with_fallback(
    file_path: Optional[str] = None,
    n: int = 100,
    seed: int = 42,
    mean_diff_embodied: float = 5.0,
    mean_diff_static: float = 2.0,
    mode: str = "secondary_analysis"
) -> List[DatasetRecord]:
    """
    Load public dataset with fallback to synthetic generation.
    
    Args:
        file_path: Path to public dataset. If None or missing instruction_type, uses synthetic.
        n: Number of synthetic records if fallback is used.
        seed: Random seed for synthetic generation.
        mean_diff_embodied: Mean difference for embodied group in synthetic.
        mean_diff_static: Mean difference for static group in synthetic.
        mode: Operation mode ('secondary_analysis' or 'synthetic').
        
    Returns:
        List of DatasetRecord objects.
    """
    # If file_path is provided, try to load it
    if file_path and Path(file_path).exists():
        try:
            records = load_public_dataset(file_path)
            if records and all(r.instruction_type for r in records):
                return records
            # If loaded but missing instruction_type, fall through to synthetic
            logger.warning("Public data loaded but missing instruction_type. Falling back to synthetic.")
        except Exception as e:
            logger.warning(f"Failed to load public dataset: {e}. Falling back to synthetic.")
    
    # Fallback to synthetic
    if mode == "secondary_analysis":
        handle_synthetic_fallback_failure(file_path or "unknown")
    
    return generate_synthetic_fallback(n, seed, mean_diff_embodied, mean_diff_static)

def main() -> None:
    """Main entry point for data loading module."""
    import sys
    from .cli import parse_args
    
    args = parse_args(sys.argv[1:])
    setup_logging()
    
    records = load_public_dataset_with_fallback(
        file_path=args.input,
        n=args.n,
        seed=args.seed,
        mode=args.mode
    )
    
    gain_records = calculate_gain_scores(records)
    output_path = f"data/processed/validated_fallback.csv"
    write_processed_data(gain_records, output_path)
    
    logger.info(f"Data processing complete. Output: {output_path}")

import sys