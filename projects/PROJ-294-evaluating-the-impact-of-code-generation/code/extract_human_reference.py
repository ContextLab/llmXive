import os
import sys
import json
import logging
import pyarrow.parquet as pq
from typing import List, Dict, Any
from utils import setup_logging, get_logger, set_task_id, get_task_id

def extract_human_references():
    """
    T011: Extract human reference code from parquet and save to JSONL.
    """
    logger = setup_logging(task_id="T011")
    logger.info("Extracting human reference code...")
    
    parquet_path = "data/raw/humaneval.parquet"
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    
    # Read parquet
    table = pq.read_table(parquet_path)
    df = table.to_pandas()
    
    output_path = "data/generated/human_samples.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w") as f:
        for _, row in df.iterrows():
            record = {
                "task_id": row["task_id"],
                "prompt": row["prompt"],
                "canonical_solution": row["canonical_solution"],
                "test": row["test"],
                "entry_point": row.get("entry_point", "")
            }
            f.write(json.dumps(record) + "\n")
    
    logger.info(f"Saved human references to {output_path}")
    return output_path

def main():
    extract_human_references()

if __name__ == "__main__":
    main()
