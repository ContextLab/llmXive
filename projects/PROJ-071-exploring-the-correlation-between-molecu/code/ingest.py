from __future__ import annotations

import json
import hashlib
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import pandas as pd
from datasets import load_dataset

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(PROCESSED_DIR / "ingest.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("llmXive_pipeline.ingest")

# Error Handlers Import (using the defined API)
from error_handlers import DataIngestionError, DataFetchError

# Logging Config Import (using the defined API)
from logging_config import log_operation, log_pipeline_failure

DATASET_ID = "Synthyra/FDA-Approved-Drugs"
DEGRADATION_COLUMNS = ['half_life', 'degradation_rate', 't12']


def get_data_path() -> Path:
    return PROCESSED_DIR


def fetch_fda_drugs() -> Optional[pd.DataFrame]:
    """
    Fetch FDA-approved drugs from HuggingFace using streaming.
    Returns a DataFrame if successful, None if the dataset is inaccessible.
    """
    logger.info(f"Attempting to fetch dataset: {DATASET_ID}")
    try:
        # Use streaming to avoid loading full dataset into memory initially
        dataset = load_dataset(DATASET_ID, streaming=True)
        
        # Determine available splits
        splits = list(dataset.keys())
        if not splits:
            logger.error("Dataset contains no splits.")
            return None
        
        # Prefer 'train' if available, otherwise use the first split
        split_name = 'train' if 'train' in splits else splits[0]
        logger.info(f"Using split: {split_name}")
        
        # Convert to pandas
        # Note: Streaming datasets must be converted to a list or iterated
        # For a DataFrame, we iterate and build it.
        # To ensure we don't hit memory limits on the full fetch if it's huge,
        # we rely on the streaming iterator.
        chunks = []
        count = 0
        max_rows = 50000  # Safety cap for initial fetch to verify structure, 
                          # though the task implies merging. 
                          # If the dataset is purely structural and we need to merge 
                          # with degradation, we fetch what we can.
        
        logger.info("Iterating over dataset stream...")
        for row in dataset[split_name]:
            if count >= max_rows:
                logger.warning(f"Reached row limit ({max_rows}). Stopping fetch.")
                break
            chunks.append(row)
            count += 1
        
        if not chunks:
            logger.error("No data rows found in the stream.")
            return None
        
        df = pd.DataFrame(chunks)
        logger.info(f"Successfully fetched {len(df)} rows.")
        return df

    except Exception as e:
        logger.error(f"Failed to fetch dataset: {str(e)}")
        raise DataFetchError(f"Dataset fetch failed: {str(e)}")


def validate_smiles_series(smiles_series: pd.Series) -> pd.Series:
    """Basic validation of SMILES strings (non-null, non-empty)."""
    return smiles_series.dropna().replace('', pd.NA).dropna()


def filter_valid_smiles(df: pd.DataFrame, smiles_col: str = 'smiles') -> pd.DataFrame:
    """Filter dataframe to keep only rows with valid SMILES."""
    if smiles_col not in df.columns:
        # Try common alternatives
        candidates = ['SMILES', 'smile', 'structure']
        for cand in candidates:
            if cand in df.columns:
                smiles_col = cand
                break
        else:
            logger.warning("No SMILES column found. Returning original DF.")
            return df
    
    df[smiles_col] = df[smiles_col].astype(str)
    valid_mask = df[smiles_col].str.len() > 0
    return df[valid_mask].copy()


def check_degradation_columns(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Check if any degradation columns exist in the dataframe.
    Returns (found: bool, found_columns: List[str])
    """
    found_cols = [col for col in DEGRADATION_COLUMNS if col in df.columns]
    return len(found_cols) > 0, found_cols


def update_gate_status(status: str, reason: str, n: int) -> None:
    """
    Write the gate status to data/gate_status.json.
    """
    gate_file = DATA_DIR / "gate_status.json"
    status_data = {
        "status": status,
        "reason": reason,
        "N": n,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(gate_file, 'w') as f:
        json.dump(status_data, f, indent=2)
    logger.info(f"Gate status written: {status_data}")


def save_merged_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Save the merged dataframe to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Saved merged dataset to {output_path}")


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def merge_structural_degradation_data(df_struct: pd.DataFrame, df_deg: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Merge structural data with degradation data if available.
    Since the source dataset (Synthyra/FDA-Approved-Drugs) is primarily structural,
    we check for degradation columns in the same dataset.
    If found, we use them. If not, we return the structural data and note the lack.
    """
    # In this specific task context, we assume the fetched DF contains both if available.
    # If the dataset has degradation columns, we keep them.
    # If not, we return the structural data as is.
    return df_struct


def run_data_availability_gate(df: pd.DataFrame) -> Tuple[bool, int]:
    """
    Run the gate logic:
    1. Check for degradation columns.
    2. Count valid numeric non-null records.
    3. Enforce N >= 30.
    Returns (gate_passed, count)
    """
    found, cols = check_degradation_columns(df)
    logger.info(f"Degradation columns found: {cols}")

    if not found:
        logger.warning("No degradation columns found in the dataset.")
        return False, 0

    # Pick the first found degradation column to count valid records
    target_col = cols[0]
    
    # Ensure it's numeric
    df[target_col] = pd.to_numeric(df[target_col], errors='coerce')
    valid_count = df[target_col].notna().sum()
    
    logger.info(f"Valid records for {target_col}: {valid_count}")

    if valid_count < 30:
        logger.warning(f"Insufficient data: N={valid_count} < 30")
        return False, valid_count

    return True, valid_count


def generate_insufficiency_report(reason: str, n: int) -> None:
    """Generate the data insufficiency report markdown."""
    report_path = PROJECT_ROOT / "data_insufficiency_report.md"
    with open(report_path, 'w') as f:
        f.write("# Data Insufficiency Report\n\n")
        f.write(f"## Status: FAIL\n\n")
        f.write(f"**Reason**: {reason}\n\n")
        f.write(f"**Valid Record Count (N)**: {n}\n\n")
        f.write("## Conclusion\n\n")
        f.write("The data availability gate failed. The pipeline cannot proceed with correlation analysis due to insufficient degradation data.\n")
    logger.info(f"Generated insufficiency report at {report_path}")


def main():
    """Main entry point for the ingestion task."""
    log_operation("Ingest", stage="T012")
    
    try:
        # 1. Fetch Data
        df = fetch_fda_drugs()
        if df is None or df.empty:
            update_gate_status("FAIL", "No data fetched", 0)
            generate_insufficiency_report("No data fetched", 0)
            raise DataIngestionError("Failed to fetch or parse dataset.")

        # 2. Filter valid SMILES
        df = filter_valid_smiles(df)
        if df.empty:
            update_gate_status("FAIL", "No valid SMILES", 0)
            generate_insufficiency_report("No valid SMILES found", 0)
            raise DataIngestionError("No valid SMILES found in dataset.")

        # 3. Run Gate
        passed, count = run_data_availability_gate(df)

        if not passed:
            # Gate Failed
            reason = "N < 30 or No Degradation Data"
            update_gate_status("FAIL", reason, count)
            generate_insufficiency_report(reason, count)
            raise DataIngestionError(f"Data Availability Gate Failed: {reason}")

        # 4. Gate Passed
        # Save merged data
        output_csv = PROCESSED_DIR / "merged_drugs.csv"
        save_merged_dataset(df, output_csv)

        # Save checksums
        checksum = calculate_checksum(output_csv)
        checksum_file = DATA_DIR / "checksums.txt"
        with open(checksum_file, 'w') as f:
            f.write(f"{checksum}  merged_drugs.csv\n")
        
        update_gate_status("PASS", "Data Availability Gate Passed", count)
        logger.info(f"Gate Passed. N={count}. Saved to {output_csv}")

    except DataIngestionError as e:
        # Re-raise to be caught by the pipeline runner or main block
        raise e
    except Exception as e:
        # Log pipeline failure using the tolerant logging function
        log_pipeline_failure("Ingest", str(e))
        raise e


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Ensure we exit with non-zero on failure
        sys.exit(1)
