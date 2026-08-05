from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from datasets import load_dataset

from logging_config import get_logger, log_operation, log_pipeline_failure, log_pipeline_start
from config import get_config

logger = get_logger("ingest")

def get_data_path() -> Path:
    return Path(__file__).parent.parent / "data"

def load_config() -> Dict[str, Any]:
    config_path = get_data_path() / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    import yaml
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def save_gate_status(status: Dict[str, Any]) -> None:
    output_path = get_data_path() / "gate_status.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(status, f, indent=2)
    logger.log("GateStatusSaved", {"path": str(output_path)})

def calculate_file_hash(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main() -> int:
    """
    Implements T011 & T012: Data Ingestion and Gate Logic.
    1. Read config for dataset ID/Version.
    2. Fetch data (streaming).
    3. Verify 'smiles' column.
    4. Check for degradation columns.
    5. Gate Logic: If no degradation, FAIL. If N < 30, FAIL.
    6. Save merged data if PASS.
    """
    # Note: log_pipeline_start signature issue fixed by tolerant logging_config
    logger.log("IngestStart", {"task": "T011"})

    try:
        config = load_config()
        dataset_id = config.get("dataset_id")
        dataset_version = config.get("dataset_version")

        if not dataset_id:
            raise ValueError("dataset_id not found in config.yaml")

        logger.log("FetchingDataset", {"id": dataset_id, "version": dataset_version})

        # Fetch data
        # Using streaming=True to handle large datasets, but for gate check we might need to materialize
        # or count on the fly. T011 says "streaming=True".
        try:
            dataset = load_dataset(dataset_id, split="train", streaming=True)
        except Exception as e:
            logger.log("DatasetFetchFailed", {"error": str(e)})
            # T070: Hard Fail on Data Fetch - do not fallback
            save_gate_status({
                "status": "FAIL",
                "reason": "Dataset fetch failed",
                "error": str(e)
            })
            return 1

        # Convert to list to inspect columns (or iterate to count)
        # For schema check, we can peek
        sample = next(iter(dataset))
        columns = list(sample.keys())

        # T011: Verify 'smiles' column
        if "smiles" not in columns:
            logger.log("SchemaError", {"reason": "No 'smiles' column found"})
            save_gate_status({
                "status": "FAIL",
                "reason": "No smiles column found",
                "column_found": None
            })
            return 1

        # T011: Check degradation columns
        degradation_cols = [c for c in columns if c.lower() in ["half_life", "t1/2", "rate_constant", "degradation_rate"]]
        
        if not degradation_cols:
            logger.log("DegradationDataMissing", {"reason": "No degradation column found"})
            save_gate_status({
                "status": "FAIL",
                "reason": "No degradation column found",
                "column_found": None
            })
            return 1

        logger.log("DegradationColumnsFound", {"columns": degradation_cols})

        # T012: Merge and Count
        # Since we are streaming, we need to materialize or count carefully.
        # For this implementation, we will materialize the dataset for merging.
        # If the dataset is too large, this might fail memory, but T012 requires merging.
        df = dataset.to_pandas()
        
        # Merge logic: Assuming single table from dataset, or merge with another source?
        # T012 says "merge structural data ... with degradation data on canonical_smiles".
        # If the dataset already has both, we just rename/prepare.
        # If we have separate sources, we'd merge. Assuming single source here for simplicity
        # or that the dataset is the merged source.
        
        # Ensure canonical_smiles exists or use smiles
        if "canonical_smiles" not in df.columns and "smiles" in df.columns:
            df["canonical_smiles"] = df["smiles"]

        # Count valid records (non-null in degradation column)
        deg_col = degradation_cols[0]
        valid_count = df[deg_col].notna().sum()

        logger.log("ValidRecordsCounted", {"N": valid_count})

        if valid_count < 30:
            logger.log("GateFailed", {"reason": "N < 30", "N": valid_count})
            save_gate_status({
                "status": "FAIL",
                "reason": "N < 30",
                "N": valid_count
            })
            return 1

        # Save merged data
        merged_path = get_data_path() / "processed" / "merged_drugs.csv"
        merged_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(merged_path, index=False)
        
        file_hash = calculate_file_hash(merged_path)
        
        save_gate_status({
            "status": "PASS",
            "N": valid_count,
            "degradation_column": deg_col,
            "file_hash": file_hash,
            "path": str(merged_path)
        })
        
        logger.log("IngestComplete", {"status": "PASS", "N": valid_count})
        return 0

    except Exception as e:
        logger.log("IngestError", {"error": str(e)})
        log_pipeline_failure("Ingest", str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())