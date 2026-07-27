import json
import hashlib
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

from datasets import load_dataset
from config import get_config
from logging_config import get_logger, log_pipeline_failure

logger = get_logger(__name__)

class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass

class DataInsufficiencyError(Exception):
    """Raised when data availability gate fails."""
    pass

def get_data_path():
    config = get_config()
    return Path(config.get("data_dir", "data"))

def fetch_fda_drugs():
    """
    Fetch FDA-approved drugs from HuggingFace.
    Uses streaming to handle large datasets.
    """
    try:
        logger.info("Fetching FDA-approved drugs dataset...")
        # The dataset is 'Synthyra/FDA-Approved-Drugs'
        # It contains 'smiles' and potentially other columns, but NOT degradation data.
        dataset = load_dataset("Synthyra/FDA-Approved-Drugs", split="train", streaming=True)
        
        # Convert to list for initial inspection (streaming allows iteration)
        # Note: For a large dataset, we might want to sample or process in chunks,
        # but for the initial fetch and structural check, we need to ensure it exists.
        # We will iterate to build the dataframe.
        data = []
        for item in dataset:
            data.append(item)
        
        df = pd.DataFrame(data)
        logger.info(f"Fetched {len(df)} records.")
        return df
    except Exception as e:
        raise DataFetchError(f"Failed to fetch dataset: {str(e)}")

def check_degradation_columns(df: pd.DataFrame) -> bool:
    """
    Check if the dataframe contains degradation-related columns.
    Returns True if found, False otherwise.
    """
    degradation_keywords = ['half_life', 'degradation_rate', 't12', 't_half', 'k']
    columns = df.columns.str.lower().tolist()
    for keyword in degradation_keywords:
        if any(keyword in col for col in columns):
            return True
    return False

def validate_smiles_series(smiles_series: pd.Series) -> pd.Series:
    """
    Basic validation of SMILES strings.
    Returns a boolean series indicating validity (non-empty, non-null).
    """
    return smiles_series.notna() & (smiles_series.astype(str).str.strip() != "")

def filter_valid_smiles(df: pd.DataFrame, smiles_col: str = "smiles") -> pd.DataFrame:
    """
    Filter dataframe to keep only rows with valid SMILES.
    """
    if smiles_col not in df.columns:
        logger.warning(f"Column '{smiles_col}' not found. Returning original dataframe.")
        return df
    
    valid_mask = validate_smiles_series(df[smiles_col])
    return df[valid_mask]

def generate_insufficiency_report(reason: str, n: int):
    """
    Generate the data insufficiency report and gate status.
    """
    data_path = get_data_path()
    report_path = data_path / "data_insufficiency_report.md"
    gate_path = data_path / "gate_status.json"

    report_content = f"""# Data Insufficiency Report

## Status: FAIL

**Reason**: {reason}
**Records Available**: {n}
**Threshold**: 30

The pipeline cannot proceed with the correlation analysis due to insufficient data.
"""
    with open(report_path, 'w') as f:
        f.write(report_content)
    
    gate_data = {
        "status": "FAIL",
        "reason": reason,
        "N": n,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(gate_path, 'w') as f:
        json.dump(gate_data, f, indent=2)
    
    logger.info(f"Generated insufficiency report: {report_path}")
    logger.info(f"Updated gate status: {gate_path}")

def run_data_availability_gate(df: pd.DataFrame):
    """
    Run the data availability gate check.
    Raises DataInsufficiencyError if checks fail.
    """
    # Check 1: Degradation columns
    has_degradation = check_degradation_columns(df)
    if not has_degradation:
        reason = "No verified degradation source found in dataset"
        generate_insufficiency_report(reason, len(df))
        raise DataInsufficiencyError(reason)
    
    # Check 2: Minimum count (if degradation exists)
    # Note: T016a merges structural data first. If degradation is missing, we fail here.
    # If degradation exists, we check count.
    if len(df) < 30:
        reason = f"Insufficient records (N={len(df)} < 30)"
        generate_insufficiency_report(reason, len(df))
        raise DataInsufficiencyError(reason)
    
    # If we pass
    gate_path = get_data_path() / "gate_status.json"
    gate_data = {
        "status": "PASS",
        "reason": "Data availability confirmed",
        "N": len(df),
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(gate_path, 'w') as f:
        json.dump(gate_data, f, indent=2)
    logger.info(f"Data Availability Gate PASSED. N={len(df)}")

def merge_structural_degradation_data(structural_df: pd.DataFrame, degradation_df: pd.DataFrame = None):
    """
    Merge structural data with degradation data if available.
    If degradation_df is None, returns structural_df and logs.
    """
    if degradation_df is None:
        logger.info("No degradation data provided. Returning structural subset only.")
        return structural_df
    
    # Attempt merge on common key (e.g., 'smiles' or 'drug_name')
    # Assuming 'smiles' is the common key
    common_cols = list(set(structural_df.columns) & set(degradation_df.columns))
    if 'smiles' in common_cols:
        merged = structural_df.merge(degradation_df, on='smiles', how='inner')
        logger.info(f"Merged {len(merged)} records on 'smiles'.")
        return merged
    else:
        logger.warning("No common key found for merge. Returning structural subset.")
        return structural_df

def save_merged_dataset(df: pd.DataFrame, filename: str):
    """
    Save merged dataset and calculate checksum.
    """
    data_path = get_data_path()
    output_path = data_path / "processed" / filename
    
    df.to_csv(output_path, index=False)
    
    # Calculate checksum
    with open(output_path, 'rb') as f:
        content = f.read()
        checksum = hashlib.sha256(content).hexdigest()
    
    checksum_path = data_path / "checksums.txt"
    with open(checksum_path, 'a') as f:
        f.write(f"{filename}: {checksum}\n")
    
    logger.info(f"Saved merged dataset to {output_path} with checksum {checksum}")

def calculate_checksum(filepath: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def main():
    config = get_config()
    logger.info("Starting Ingestion Pipeline")
    
    try:
        # Fetch data
        df = fetch_fda_drugs()
        
        # Check for degradation columns
        has_degradation = check_degradation_columns(df)
        
        if not has_degradation:
            # T012a: Log and trigger gate
            log_pipeline_failure("ingest", "Missing degradation columns")
            generate_insufficiency_report("No verified degradation source found", len(df))
            raise DataInsufficiencyError("Missing degradation columns")
        
        # Filter valid SMILES (T016b)
        valid_df = filter_valid_smiles(df)
        
        # Check count (T016c)
        if len(valid_df) < 30:
            generate_insufficiency_report(f"Insufficient valid SMILES (N={len(valid_df)})", len(valid_df))
            raise DataInsufficiencyError(f"Insufficient valid SMILES: {len(valid_df)}")
        
        # Run Gate (T013)
        run_data_availability_gate(valid_df)
        
        # Save structural subset (T017)
        save_merged_dataset(valid_df, "structural_subset.csv")
        
        logger.info("Ingestion Pipeline Completed Successfully")
        
    except DataFetchError as e:
        log_pipeline_failure("ingest", str(e))
        raise
    except DataInsufficiencyError as e:
        log_pipeline_failure("ingest", str(e))
        raise
    except Exception as e:
        log_pipeline_failure("ingest", str(e))
        raise

if __name__ == "__main__":
    main()