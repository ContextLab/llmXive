"""
T011: Extract human reference code from raw HumanEval data.

Reads data/raw/humaneval.parquet, extracts human reference code (canonical_solution),
preserves task_id and prompt, and writes to data/generated/human_samples.json (JSONL).

Constraint: Must NOT fall back to synthetic data.
"""
import os
import sys
import json
import logging
import pyarrow.parquet as pq
from typing import List, Dict, Any

# Import shared utilities from the existing API surface
from utils import setup_logging, get_logger, set_task_id, get_task_id
from utils import ensure_directory

TASK_ID = "T011"

def extract_human_references(input_path: str, output_path: str) -> int:
    """
    Extract human reference code from parquet file and save as JSONL.
    
    Args:
        input_path: Path to data/raw/humaneval.parquet
        output_path: Path to data/generated/human_samples.json
        
    Returns:
        Number of records extracted
        
    Raises:
        RuntimeError: If input file not found or extraction fails
    """
    logger = get_logger()
    logger.info(f"Starting extraction from {input_path}")
    
    # Verify input exists
    if not os.path.exists(input_path):
        raise RuntimeError(f"Input file not found: {input_path}. Run T010 first.")
    
    # Read parquet file
    table = pq.read_table(input_path)
    df = table.to_pandas()
    
    logger.info(f"Loaded {len(df)} records from parquet")
    
    # Extract required fields
    extracted_records = []
    for idx, row in df.iterrows():
        record = {
            "task_id": row["task_id"],
            "prompt": row["prompt"],
            "canonical_solution": row["canonical_solution"]
        }
        extracted_records.append(record)
    
    # Ensure output directory exists
    ensure_directory(output_path)
    
    # Write JSONL output
    with open(output_path, "w", encoding="utf-8") as f:
        for record in extracted_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    logger.info(f"Extracted {len(extracted_records)} human references to {output_path}")
    return len(extracted_records)

def main():
    """Main entry point for T011."""
    # Setup logging
    logger = setup_logging(task_id=TASK_ID)
    set_task_id(TASK_ID)
    
    # Define paths
    input_path = "data/raw/humaneval.parquet"
    output_path = "data/generated/human_samples.json"
    
    try:
        count = extract_human_references(input_path, output_path)
        logger.info(f"T011 completed successfully: {count} records extracted")
        return 0
    except Exception as e:
        logger.error(f"T011 failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())