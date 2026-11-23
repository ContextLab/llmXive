import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/aggregate.log')
    ]
)
logger = logging.getLogger(__name__)

def find_batch_files(processing_dir: Path) -> List[Path]:
    """
    Find all generation batch JSON files in the processing directory.
    Returns a sorted list of paths to ensure deterministic processing order.
    """
    if not processing_dir.exists():
        logger.warning(f"Processing directory does not exist: {processing_dir}")
        return []
    
    batch_files = sorted(processing_dir.glob("generation_batch_*.json"))
    logger.info(f"Found {len(batch_files)} batch files in {processing_dir}")
    return batch_files

def load_batch_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load a single batch JSON file.
    Returns the list of records or an empty list if the file is empty/invalid.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                logger.error(f"File {file_path} does not contain a JSON list. Got {type(data)}")
                return []
            logger.info(f"Loaded {len(data)} records from {file_path.name}")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON in {file_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading {file_path}: {e}")
        return []

def consolidate_batches(batch_files: List[Path]) -> List[Dict[str, Any]]:
    """
    Iterate over batch files, load them, and consolidate into a single list.
    Preserves 'ast_params' and other fields from the source records.
    """
    consolidated = []
    total_loaded = 0
    total_skipped = 0

    for file_path in batch_files:
        records = load_batch_file(file_path)
        if not records:
            total_skipped += 1
            continue
        
        # Verify structure integrity for a sample record
        if records:
            sample = records[0]
            if 'ast_params' in sample:
                logger.debug(f"Verified 'ast_params' preservation in {file_path.name}")
            else:
                logger.warning(f"'ast_params' missing in sample record from {file_path.name}")

        consolidated.extend(records)
        total_loaded += len(records)
    
    logger.info(f"Consolidation complete: Loaded {total_loaded} records, Skipped {total_skipped} files")
    return consolidated

def verify_structure(records: List[Dict[str, Any]]) -> bool:
    """
    Verify the final consolidated structure.
    Checks that all records are dictionaries and contain expected keys.
    """
    if not records:
        logger.warning("No records to verify.")
        return False

    valid_count = 0
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            logger.error(f"Record {i} is not a dictionary: {type(record)}")
            return False
        
        # Basic validation: ensure essential keys exist (even if null)
        required_keys = ['method_name', 'repo_name', 'human_docstring', 'generated_docstring']
        for key in required_keys:
            if key not in record:
                logger.warning(f"Record {i} missing key: {key}")
        
        if 'ast_params' in record:
            if not isinstance(record['ast_params'], list):
                logger.error(f"Record {i} 'ast_params' is not a list: {type(record['ast_params'])}")
                return False
        
        valid_count += 1

    logger.info(f"Structure verification passed for {valid_count} records.")
    return True

def save_results(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the consolidated records to the final results JSON file.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved {len(records)} records to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save results to {output_path}: {e}")
        raise

def main():
    """
    Main entry point for the aggregation task.
    Iterates over batch files, consolidates them, verifies, and saves.
    """
    # Define paths based on project structure
    base_dir = Path(__file__).resolve().parent.parent
    processing_dir = base_dir / "data" / "processed"
    output_file = base_dir / "data" / "processed" / "results.json"

    logger.info(f"Starting aggregation. Processing dir: {processing_dir}, Output: {output_file}")

    # Step 1: Find batch files
    batch_files = find_batch_files(processing_dir)
    if not batch_files:
        logger.error("No batch files found. Aborting.")
        sys.exit(1)

    # Step 2: Consolidate
    consolidated_data = consolidate_batches(batch_files)
    if not consolidated_data:
        logger.error("Consolidation resulted in no data. Aborting.")
        sys.exit(1)

    # Step 3: Verify row count constraint (20 repos * 1000 methods = 20,000 max)
    max_rows = 20000
    total_rows = len(consolidated_data)
    if total_rows > max_rows:
        logger.error(f"Row count {total_rows} exceeds maximum allowed {max_rows}. Aborting.")
        sys.exit(1)
    logger.info(f"Row count verification passed: {total_rows} <= {max_rows}")

    # Step 4: Verify structure
    if not verify_structure(consolidated_data):
        logger.error("Structure verification failed. Aborting.")
        sys.exit(1)

    # Step 5: Save results
    save_results(consolidated_data, output_file)

    logger.info("Aggregation task completed successfully.")

if __name__ == "__main__":
    main()
