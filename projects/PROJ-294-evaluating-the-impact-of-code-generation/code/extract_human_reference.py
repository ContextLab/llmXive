import os
import sys
import json
import logging
import pyarrow.parquet as pq
from typing import List, Dict, Any
from utils import setup_logging, get_logger, set_task_id, get_task_id

def extract_human_references():
    """
    FR-001: Extract human reference code from the parquet file and save as JSONL.
    The output conforms to specs/.../contracts/human_samples.schema.yaml:
    {
        "task_id": "...",
        "code": "...",          # canonical_solution
        "source": "human"
    }
    """
    logger = setup_logging(task_id="T001")
    logger.info("Extracting human reference solutions...")

    parquet_path = os.path.join("data", "raw", "humaneval.parquet")
    if not os.path.exists(parquet_path):
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

    table = pq.read_table(parquet_path)
    df = table.to_pandas()

    output_path = os.path.join("data", "generated", "human_samples.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        for _, row in df.iterrows():
            record = {
                "task_id": row["task_id"],
                "code": row["canonical_solution"],
                "source": "human"
            }
            f.write(json.dumps(record) + "\n")

    logger.info(f"Saved human references to {output_path}")
    return output_path

def main():
    extract_human_references()

if __name__ == "__main__":
    main()
