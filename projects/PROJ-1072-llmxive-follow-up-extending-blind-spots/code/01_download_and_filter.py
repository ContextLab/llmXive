import argparse
import json
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
import logging

# Import local utilities
from utils.logging_config import get_logger
from utils.hashing_utils import compute_file_hash
from utils.dataset_integrity import validate_record_fields, generate_integrity_report
from utils.filtering_utils import filter_by_categories

# Configure logging
logger = get_logger(__name__)

def setup_logging(log_level: str = "INFO") -> None:
    """Configure root logger."""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def download_dataset(dataset_path: str) -> List[Dict[str, Any]]:
    """
    Download the Blind-Spots-Bench dataset.
    
    Args:
        dataset_path: Path to the dataset (local or identifier for datasets library).
        
    Returns:
        List of task records.
    """
    logger.info(f"Loading dataset from: {dataset_path}")
    try:
        # Attempt to load from HuggingFace datasets if it's a repo ID
        # If it's a local path, load_jsonl
        p = Path(dataset_path)
        if p.exists():
            if p.is_dir():
                # Assume jsonl inside dir or specific file
                target = p / "tasks.jsonl"
                if not target.exists():
                    # Fallback to first jsonl
                    target = next(p.glob("*.jsonl"), None)
                    if not target:
                        raise FileNotFoundError(f"No .jsonl found in {p}")
            else:
                target = p
            
            records = []
            with open(target, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            logger.info(f"Loaded {len(records)} records from local file.")
            return records
        
        # If not local, try datasets library
        from datasets import load_dataset
        # Assuming the canonical source is a specific HF repo ID
        # If the user provided a repo ID, use it. Otherwise default.
        ds_id = dataset_path if not dataset_path.startswith('/') else "blind-spots-bench" 
        # Fallback default if path was invalid
        if not dataset_path or dataset_path.startswith('/'):
            ds_id = "blind-spots-bench" # Replace with actual repo ID if known, otherwise this fails loudly
            
        ds = load_dataset(ds_id, split="train")
        records = ds.to_list()
        logger.info(f"Loaded {len(records)} records from HuggingFace.")
        return records

    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def filter_records(records: List[Dict[str, Any]], categories: Set[str]) -> List[Dict[str, Any]]:
    """
    Filter records by target categories.
    
    Args:
        records: List of all records.
        categories: Set of allowed categories (e.g., {"Abstract Reasoning", "Object-Centric"}).
        
    Returns:
        Filtered list of records.
    """
    logger.info(f"Filtering for categories: {categories}")
    filtered = filter_by_categories(records, categories)
    logger.info(f"Filtered: {len(filtered)} records retained.")
    return filtered

def validate_integrity(records: List[Dict[str, Any]], output_dir: Path) -> bool:
    """
    Validate that all records have the required 'constraint' field.
    Generates an error report and exits if failures found.
    
    Args:
        records: List of filtered records.
        output_dir: Directory to write validation reports.
        
    Returns:
        True if validation passes.
    """
    required_fields = ["constraint"]
    errors = validate_record_fields(records, required_fields)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "integrity_error_report.json"
    
    report = generate_integrity_report(errors, report_path)
    
    if report["total_errors"] > 0:
        logger.error(f"Integrity check failed: {report['total_errors']} records missing required fields.")
        logger.error(f"Report written to: {report_path}")
        raise SystemExit(1)
    
    logger.info("Integrity check passed.")
    return True

def write_filtered_data(records: List[Dict[str, Any]], output_path: Path) -> str:
    """
    Write filtered records to JSONL and compute checksum.
    
    Args:
        records: List of records to write.
        output_path: Destination path.
        
    Returns:
        Hex digest of the file hash.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for rec in records:
            f.write(json.dumps(rec) + '\n')
    
    file_hash = compute_file_hash(output_path)
    logger.info(f"Wrote {len(records)} records to {output_path}")
    logger.info(f"Checksum: {file_hash}")
    return file_hash

def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Download and filter Blind-Spots-Bench dataset."
    )
    parser.add_argument(
        "--dataset-path",
        type=str,
        default="blind-spots-bench",
        help="Path to the dataset (local file/dir or HuggingFace repo ID). Default: blind-spots-bench"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/filtered",
        help="Directory to write filtered data and reports. Default: data/filtered"
    )
    parser.add_argument(
        "--categories",
        type=str,
        nargs="+",
        default=["Abstract Reasoning", "Object-Centric"],
        help="Categories to retain. Default: Abstract Reasoning Object-Centric"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level. Default: INFO"
    )
    
    args = parser.parse_args()
    setup_logging(args.log_level)
    
    output_dir = Path(args.output_dir)
    filtered_file = output_dir / "filtered_tasks.jsonl"
    validation_dir = output_dir.parent / "validation"
    
    try:
        # 1. Download/Load
        records = download_dataset(args.dataset_path)
        
        # 2. Filter
        target_cats = set(args.categories)
        filtered = filter_records(records, target_cats)
        
        if not filtered:
            logger.warning("No records found matching the specified categories.")
            # Still write empty file or exit? Per spec, usually fail if empty but let's proceed to integrity check
        
        # 3. Validate Integrity
        validate_integrity(filtered, validation_dir)
        
        # 4. Write Output
        checksum = write_filtered_data(filtered, filtered_file)
        
        # 5. Write Checksum file
        checksum_file = output_dir / "filtered_tasks.jsonl.sha256"
        with open(checksum_file, 'w') as f:
            f.write(checksum)
        
        logger.info("Pipeline completed successfully.")
        
    except SystemExit as e:
        raise
    except Exception as e:
        logger.exception(f"Pipeline failed with unhandled error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()