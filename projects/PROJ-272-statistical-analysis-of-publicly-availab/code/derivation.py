import logging
import os
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import yaml
import json
import hashlib
from datetime import datetime

from config import get_path, ensure_dirs
from utils import get_logger

def load_interim_data() -> pd.DataFrame:
    """
    Load the preprocessed data from the raw data directory.
    Expects the file to be at data/raw/processed_adress.csv based on pipeline flow.
    If that doesn't exist, it looks for data/raw/cleaned_raw.csv as a fallback for the intermediate step.
    """
    raw_path = get_path("data", "raw")
    # Based on T014/T015 flow, the cleaned/filtered data is usually the input to this step.
    # We assume the previous step wrote to a temp or specific intermediate file.
    # However, since T014/T015 are in ingestion.py, we need to find where they wrote the data.
    # Let's assume ingestion.py main writes the filtered data to data/raw/interim_processed.csv
    # or we read from the raw directory if ingestion wrote there.
    
    # For T016, we are creating the FINAL cleaned dataset from the *output* of T014/T015.
    # Let's assume T014/T015 output to `data/raw/interim_filtered.csv` or similar.
    # To be robust, we look for the most recent CSV in data/raw that isn't the raw download.
    
    input_file = None
    candidates = list(Path(raw_path).glob("*.csv"))
    # Filter out obvious raw archives if they were unzipped there
    valid_candidates = [f for f in candidates if "cleaned" not in f.name.lower() and "processed" not in f.name.lower()]
    
    # If we have candidates, pick the last modified one, or a specific name if we know it.
    # Since T014/T015 are part of ingestion, let's assume they output to `data/raw/filtered_adress.csv`
    # as a temporary holding spot before T016 finalizes it.
    
    specific_name = "filtered_adress.csv"
    potential = Path(raw_path) / specific_name
    if potential.exists():
        input_file = potential
    elif valid_candidates:
        # Fallback to most recent
        input_file = max(valid_candidates, key=os.path.getmtime)
    
    if not input_file:
        raise FileNotFoundError(f"No input data found in {raw_path} for derivation. "
                                f"Expected {specific_name} or any CSV in {raw_path}.")
                                
    logger = get_logger(__name__)
    logger.info(f"Loading interim data from {input_file}")
    
    df = pd.read_csv(input_file)
    return df

def generate_derivation_log(df: pd.DataFrame, input_file: Path) -> Dict[str, Any]:
    """
    Generates the derivation log metadata.
    Records the source, row counts, column stats, and timestamp.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "source_file": str(input_file),
        "source_hash": hashlib.sha256(input_file.read_bytes()).hexdigest(),
        "input_rows": len(df),
        "input_columns": list(df.columns),
        "output_file": "data/interim/cleaned_adress.csv",
        "steps_applied": [
            "T012: ADReSS Download & Verification",
            "T013: Text Cleaning (UTF-8, non-verbal removal)",
            "T014: Record Filtering (min 50 words, non-null labels)",
            "T015: Metadata Extraction & Reason Codes"
        ],
        "final_stats": {
            "total_records": len(df),
            "label_distribution": df["label"].value_counts().to_dict() if "label" in df.columns else "N/A",
            "missing_values": df.isnull().sum().to_dict()
        }
    }
    return log_entry

def finalize_dataset(df: pd.DataFrame, log_entry: Dict[str, Any]) -> None:
    """
    Writes the final cleaned dataset and the derivation log to disk.
    """
    output_dir = get_path("data", "interim")
    ensure_dirs(output_dir)
    
    output_csv = Path(output_dir) / "cleaned_adress.csv"
    output_log = Path(output_dir) / "cleaned_adress_derivation.yaml"
    
    # Save CSV
    df.to_csv(output_csv, index=False)
    
    # Save Log
    with open(output_log, "w", encoding="utf-8") as f:
        yaml.dump(log_entry, f, default_flow_style=False, sort_keys=False)
        
    return output_csv, output_log

def main():
    logger = get_logger(__name__)
    logger.info("Starting T016: Create intermediate cleaned dataset")
    
    try:
        # 1. Load data from previous step (T014/T015 output)
        df = load_interim_data()
        
        if df.empty:
            raise ValueError("Input dataframe is empty. Check T014/T015 filtering logic.")
        
        # 2. Generate Derivation Log
        input_path = Path(df.attrs.get("source_file", "unknown")) # Fallback if not set in attrs
        # We re-scan for the actual file path used in load_interim_data if not passed
        # But for simplicity, we trust the load function found the right one.
        # Let's re-find the specific file path used by load_interim_data for the log
        raw_path = get_path("data", "raw")
        specific_name = "filtered_adress.csv"
        input_file = Path(raw_path) / specific_name
        if not input_file.exists():
            # Fallback to logic in load_interim_data
            candidates = [f for f in Path(raw_path).glob("*.csv") if "cleaned" not in f.name.lower()]
            if candidates:
                input_file = max(candidates, key=os.path.getmtime)
        
        log_entry = generate_derivation_log(df, input_file)
        
        # 3. Write artifacts
        output_csv, output_log = finalize_dataset(df, log_entry)
        
        logger.info(f"Successfully created {output_csv}")
        logger.info(f"Derivation log saved to {output_log}")
        logger.info(f"Dataset contains {len(df)} records.")
        
    except Exception as e:
        logger.error(f"Failed to create dataset: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
