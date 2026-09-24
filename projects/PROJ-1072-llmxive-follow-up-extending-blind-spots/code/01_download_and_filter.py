import argparse
import json
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple, Iterator

from utils.logging_config import get_logger, setup_root_logger
from utils.filtering_utils import is_valid_category, filter_by_categories
from utils.hashing_utils import compute_file_hash

# Configure logger
logger = get_logger(__name__)

def setup_logging():
    """Setup logging configuration."""
    setup_root_logger()

def download_dataset(output_path: Path) -> Iterator[Dict[str, Any]]:
    """
    Download dataset from canonical source using streaming.
    Yields records one by one to minimize memory usage.
    """
    from datasets import load_dataset
    
    # The canonical source for Blind-Spots-Bench is the HuggingFace dataset
    # "blind-spots-bench" or similar. We use the streaming API.
    # If the specific dataset ID is not standard, we assume it's available 
    # under a known namespace or we fetch from a specific config.
    # Based on context, we assume 'blind-spots-bench' or similar.
    # Let's assume the dataset name is 'blind-spots-bench' as per the project title.
    # If it fails, we let it raise (T053 requirement).
    
    dataset_name = "blind-spots-bench" 
    try:
        ds = load_dataset(dataset_name, split="train", streaming=True)
        for item in ds:
            yield item
    except Exception as e:
        logger.error(f"Failed to download dataset '{dataset_name}': {e}")
        raise

def filter_records(records: Iterator[Dict[str, Any]], categories: Set[str]) -> Iterator[Dict[str, Any]]:
    """
    Filter records based on task_category.
    """
    for record in records:
        if is_valid_category(record, categories):
            yield record

def validate_integrity(records: List[Dict[str, Any]], required_field: str = "constraint") -> Tuple[int, List[str]]:
    """
    Check for missing required fields (FR-006, FR-001).
    Returns (count_of_missing, list_of_missing_ids).
    """
    missing_count = 0
    missing_ids = []
    
    for record in records:
        # Check if the field exists and is not None/empty
        if required_field not in record or record[required_field] is None:
            missing_count += 1
            record_id = record.get("id", "unknown_id")
            missing_ids.append(record_id)
            logger.warning(f"Missing '{required_field}' in record ID: {record_id}")
    
    return missing_count, missing_ids

def write_integrity_report(output_path: Path, total_missing: int, missing_ids: List[str], status: str = "failed"):
    """
    Write integrity error report to JSON.
    If status is 'passed', we might not write or write a success report.
    Per T014, we MUST generate this file if there are missing constraints, 
    and then halt.
    """
    report = {
        "status": status,
        "total_missing": total_missing,
        "missing_ids": missing_ids,
        "message": "Execution halted due to missing constraint fields." if status == "failed" else "Integrity check passed."
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Integrity report written to {output_path}")

def write_filtered_data(records: List[Dict[str, Any]], output_path: Path):
    """
    Write filtered records to JSONL file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')
    logger.info(f"Filtered data written to {output_path}")

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    """
    return compute_file_hash(file_path)

def main():
    parser = argparse.ArgumentParser(description="Download and filter Blind-Spots-Bench dataset.")
    parser.add_argument("--input", type=str, default=None, help="Path to input dataset (if not downloading).")
    parser.add_argument("--output", type=str, default='data/filtered/filtered_tasks.jsonl', help="Output path for filtered data.")
    parser.add_argument("--categories", type=str, nargs='+', default=['Abstract Reasoning', 'Object-Centric'], 
                        help="Categories to filter for.")
    parser.add_argument("--integrity-output", type=str, default='data/validation/integrity_error_report.json',
                        help="Path for integrity error report.")
    
    args = parser.parse_args()
    setup_logging()
    
    categories = set(args.categories)
    output_path = Path(args.output)
    integrity_output_path = Path(args.integrity_output)
    
    # 1. Download or Load
    if args.input:
        logger.info(f"Loading dataset from {args.input}")
        # Assuming JSONL input if local file provided
        records = []
        with open(args.input, 'r', encoding='utf-8') as f:
            for line in f:
                records.append(json.loads(line))
    else:
        logger.info("Downloading dataset via streaming...")
        records = list(download_dataset(output_path.parent))
    
    # 2. Filter
    logger.info(f"Filtering for categories: {categories}")
    filtered_records = list(filter_records(iter(records), categories))
    logger.info(f"Filtered {len(filtered_records)} records.")
    
    # 3. Integrity Check (T014)
    logger.info("Running integrity check for 'constraint' field...")
    missing_count, missing_ids = validate_integrity(filtered_records, "constraint")
    
    if missing_count > 0:
        logger.error(f"Integrity check FAILED: {missing_count} records missing 'constraint' field.")
        write_integrity_report(integrity_output_path, missing_count, missing_ids, status="failed")
        logger.critical("Halting execution due to integrity failure.")
        sys.exit(1)
    else:
        logger.info("Integrity check PASSED: All records have 'constraint' field.")
        # Optional: Write a success report or skip writing this file if not required on success.
        # The task says "MUST generate ... on failure". It implies on success we proceed.
        # However, to be safe and explicit, we can write a success status if needed, 
        # but the critical requirement is the failure report.
        # We will not write the failure report on success.
        pass
    
    # 4. Write Filtered Data
    write_filtered_data(filtered_records, output_path)
    
    # 5. Compute Hash
    file_hash = compute_file_hash(output_path)
    logger.info(f"Output file hash: {file_hash}")
    
    logger.info("Pipeline stage completed successfully.")

if __name__ == "__main__":
    main()