"""
Ingestion module for FDA drug data.
Implements T011: Data Source Fetch & Schema Verification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from datasets import load_dataset

# Import local utilities ensuring API compatibility
try:
    from logging_config import log_operation, get_logger, log_pipeline_failure
except ImportError:
    # Fallback if run directly without package init
    def log_operation(*args, **kwargs): return None
    def get_logger(*args, **kwargs): return None
    def log_pipeline_failure(*args, **kwargs): print(f"LOG FAIL: {args} {kwargs}")

# Constants
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
GATE_STATUS_PATH = DATA_DIR / "gate_status.json"
STAT_GATE_STATUS_PATH = DATA_DIR / "stat_gate_status.json"
OUTPUT_SCHEMA_PATH = DATA_DIR / "output_schema.yaml"

# Degradation column priority
DEGRADATION_COLUMNS = ["half_life", "k_degradation", "rate_constant", "t_half"]

# Source dataset info
FDA_DATASET_ID = "Synthyra/FDA-Approved-Drugs"
DEGRADATION_DATASET_ID = "Nab/Drug-Degradation"

logger = get_logger("ingest")

def get_data_path(filename: str) -> Path:
    """Return the full path for a data file."""
    return DATA_DIR / filename

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def save_checksums(file_path: Path, checksum: str) -> None:
    """Save checksums to a JSON file."""
    checksums_path = PROCESSED_DIR / "checksums.json"
    checksums = {}
    if checksums_path.exists():
        with open(checksums_path, "r") as f:
            checksums = json.load(f)
    checksums[file_path.name] = checksum
    with open(checksums_path, "w") as f:
        json.dump(checksums, f, indent=2)

def fetch_fda_drugs() -> pd.DataFrame:
    """
    Fetch FDA approved drugs from Synthyra/FDA-Approved-Drugs.
    Uses streaming=True to handle large datasets.
    Returns a pandas DataFrame.
    """
    logger.log("fetch_fda_drugs", status="started")
    try:
        # Use streaming to avoid loading full dataset into memory immediately
        dataset = load_dataset(FDA_DATASET_ID, split="train", streaming=True)
        
        # Convert to list of dicts first to inspect structure, then convert to DF
        # Since streaming yields batches, we need to handle it carefully
        # For now, let's try to load a sample to check schema, then fetch full if needed
        # However, task requires fetching structural data. We'll fetch the first batch to check schema
        # and then convert the streaming dataset to a parquet file.
        
        # We need to materialize the data to save as parquet. 
        # Given constraints, we'll fetch the first 1000 rows to check schema, 
        # then fetch the full dataset if schema is valid.
        # But for efficiency, we'll just fetch the full dataset into a DF if it fits,
        # otherwise we'll process in chunks.
        
        # For this implementation, we assume the dataset is small enough to load into memory
        # or we use a streaming approach to write directly to parquet.
        # Let's try loading the full dataset first.
        
        # Since streaming=True returns an IterableDataset, we need to convert it.
        # We'll use to_pandas() which might load everything.
        # To be safe with memory, we'll write to parquet in chunks if needed.
        # But for simplicity and correctness, let's try loading the first batch to verify schema.
        
        batch = next(iter(dataset))
        print(f"Dataset columns: {batch.keys()}")
        
        # If 'smiles' is not in the keys, we raise an error immediately
        if "smiles" not in batch.keys():
            raise SchemaError(f"Expected 'smiles' column not found in {FDA_DATASET_ID}. Found: {batch.keys()}")
        
        # Now fetch the full dataset. 
        # We'll use streaming to write to parquet to avoid memory issues.
        # However, datasets library doesn't directly support streaming to parquet easily.
        # We'll load the dataset and convert to pandas, assuming it fits in memory for now.
        # If it's too large, we'll need a more robust chunking strategy.
        
        # Let's try loading the full dataset
        full_dataset = load_dataset(FDA_DATASET_ID, split="train")
        df = full_dataset.to_pandas()
        
        # Verify smiles column exists in the full dataframe
        if "smiles" not in df.columns:
            raise SchemaError(f"Expected 'smiles' column not found in loaded data. Found: {df.columns.tolist()}")
        
        logger.log("fetch_fda_drugs", status="completed", rows=len(df))
        return df
        
    except Exception as e:
        log_pipeline_failure("fetch_fda_drugs", str(e))
        raise

def validate_smiles_series(smiles_series: pd.Series) -> pd.Series:
    """
    Validate SMILES strings. Returns a boolean series indicating validity.
    For now, we just check if the string is not empty.
    """
    # In a real implementation, we would use RDKit to validate SMILES
    # For now, we assume all non-empty strings are valid
    return smiles_series.astype(str).str.strip() != ""

def filter_valid_smiles(df: pd.DataFrame, smiles_col: str = "smiles") -> pd.DataFrame:
    """Filter dataframe to only include rows with valid SMILES."""
    valid_mask = validate_smiles_series(df[smiles_col])
    return df[valid_mask].copy()

def log_errors_to_file(errors: List[Dict[str, Any]], log_path: Path) -> None:
    """Log errors to a JSON file."""
    if log_path.exists():
        with open(log_path, "r") as f:
            try:
                existing_errors = json.load(f)
            except json.JSONDecodeError:
                existing_errors = []
    else:
        existing_errors = []
    
    existing_errors.extend(errors)
    
    with open(log_path, "w") as f:
        json.dump(existing_errors, f, indent=2)

def check_degradation_columns(df: pd.DataFrame, source_name: str = "main") -> Optional[str]:
    """
    Check for degradation columns in the dataframe.
    Returns the name of the first valid degradation column found, or None.
    """
    columns = [col.lower() for col in df.columns]
    for col in DEGRADATION_COLUMNS:
        if col in columns:
            # Find the actual column name (case-insensitive match)
            actual_col = df.columns[[c == col for c in columns]][0]
            # Check if the column has any non-null values
            if df[actual_col].notna().sum() > 0:
                return actual_col
    return None

def update_gate_status(status: str, reason: str = "", column_found: Optional[str] = None, n: Optional[int] = None) -> Dict[str, Any]:
    """Update the gate status file."""
    gate_data = {
        "status": status,
        "reason": reason,
        "column_found": column_found,
        "timestamp": datetime.utcnow().isoformat()
    }
    if n is not None:
        gate_data["N"] = n
    
    with open(GATE_STATUS_PATH, "w") as f:
        json.dump(gate_data, f, indent=2)
    
    return gate_data

def run_data_availability_gate(df: pd.DataFrame, source_name: str = "FDA") -> bool:
    """
    Run the data availability gate.
    Checks for 'smiles' column and degradation data.
    Returns True if gate passes, False otherwise.
    """
    logger.log("run_data_availability_gate", status="started", source=source_name)
    
    # Check for smiles column
    if "smiles" not in df.columns:
        update_gate_status("FAIL", "Missing 'smiles' column", None)
        raise SchemaError(f"Missing 'smiles' column in {source_name} dataset. Found: {df.columns.tolist()}")
    
    # Check for degradation column
    deg_col = check_degradation_columns(df, source_name)
    if deg_col is None:
        # Try to fetch degradation data from secondary source
        logger.log("run_data_availability_gate", status="degradation_missing", msg="Attempting secondary source")
        try:
            deg_dataset = load_dataset(DEGRADATION_DATASET_ID, split="train")
            deg_df = deg_dataset.to_pandas()
            
            # Check for smiles column in degradation dataset
            if "smiles" not in deg_df.columns and "canonical_smiles" not in deg_df.columns:
                update_gate_status("FAIL", "No degradation source with smiles found", None)
                raise SchemaError(f"Degradation dataset missing smiles column. Found: {deg_df.columns.tolist()}")
            
            # Use canonical_smiles if available, else smiles
            smiles_col = "canonical_smiles" if "canonical_smiles" in deg_df.columns else "smiles"
            
            # Merge on smiles
            merge_key = "canonical_smiles" if "canonical_smiles" in df.columns else "smiles"
            merged_df = pd.merge(df, deg_df, left_on=merge_key, right_on=smiles_col, how="left")
            
            # Check for degradation column in merged data
            deg_col = check_degradation_columns(merged_df, "merged")
            if deg_col is None:
                update_gate_status("FAIL", "No degradation column found in merged data", None)
                raise SchemaError("No degradation column found in merged data")
            
            # Update gate status
            update_gate_status("PASS", "Degradation data found in secondary source", deg_col, len(merged_df))
            logger.log("run_data_availability_gate", status="completed", msg="Secondary source used")
            return True
            
        except Exception as e:
            update_gate_status("FAIL", f"Secondary source failed: {str(e)}", None)
            raise DataFetchError(f"Failed to fetch degradation data from secondary source: {str(e)}")
    else:
        # Degradation column found in main dataset
        update_gate_status("PASS", "Degradation data found in main source", deg_col, len(df))
        logger.log("run_data_availability_gate", status="completed", msg="Main source used")
        return True

class SchemaError(Exception):
    """Raised when expected schema is not met."""
    pass

class DataFetchError(Exception):
    """Raised when data fetching fails."""
    pass

class DataIngestionError(Exception):
    """Raised during data ingestion."""
    pass

def merge_structural_degradation_data(structural_df: pd.DataFrame, degradation_df: pd.DataFrame) -> pd.DataFrame:
    """Merge structural and degradation data on SMILES."""
    # Determine merge key
    structural_key = "canonical_smiles" if "canonical_smiles" in structural_df.columns else "smiles"
    degradation_key = "canonical_smiles" if "canonical_smiles" in degradation_df.columns else "smiles"
    
    merged_df = pd.merge(structural_df, degradation_df, left_on=structural_key, right_on=degradation_key, how="inner")
    
    # Remove duplicate key column if exists
    if structural_key != degradation_key and structural_key in merged_df.columns:
        merged_df = merged_df.drop(columns=[structural_key])
    
    return merged_df

def save_merged_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Save merged dataset to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.log("save_merged_dataset", status="completed", path=str(output_path))

def generate_insufficiency_report(reason: str, n: Optional[int] = None) -> None:
    """Generate a data insufficiency report."""
    report_path = DATA_DIR / "data_insufficiency_report.md"
    with open(report_path, "w") as f:
        f.write("# Data Insufficiency Report\n\n")
        f.write(f"## Reason\n{reason}\n\n")
        if n is not None:
            f.write(f"## Record Count\n{ n }\n\n")
        f.write("## Recommendation\n")
        f.write("The data availability gate has failed. Please check the data sources and ensure the required columns are present.\n")
    logger.log("generate_insufficiency_report", status="completed", path=str(report_path))

def validate_smiles_column(df: pd.DataFrame) -> bool:
    """Validate that the smiles column exists and is not empty."""
    if "smiles" not in df.columns:
        return False
    return df["smiles"].notna().any()

def log_pipeline_start(task_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Log pipeline start."""
    logger.log("pipeline_start", operation=task_name, metadata=metadata or {})

def main():
    """Main entry point for ingestion."""
    parser = argparse.ArgumentParser(description="Ingest FDA drug data")
    parser.add_argument("--fetch", action="store_true", help="Fetch data from source")
    args = parser.parse_args()
    
    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    if args.fetch:
        log_pipeline_start("T011_Data_Source_Fetch", {"task": "T011"})
        
        try:
            # Fetch FDA drugs
            fda_df = fetch_fda_drugs()
            
            # Save to parquet
            parquet_path = RAW_DIR / "fda_structures.parquet"
            fda_df.to_parquet(parquet_path, index=False)
            logger.log("save_parquet", status="completed", path=str(parquet_path))
            
            # Calculate and save checksum
            checksum = calculate_checksum(parquet_path)
            save_checksums(parquet_path, checksum)
            
            # Run data availability gate
            run_data_availability_gate(fda_df)
            
            logger.log("T011_Data_Source_Fetch", status="completed")
            
        except SchemaError as e:
            log_pipeline_failure("T011_Data_Source_Fetch", str(e))
            # Update gate status to FAIL
            update_gate_status("FAIL", str(e), None)
            sys.exit(1)
        except DataFetchError as e:
            log_pipeline_failure("T011_Data_Source_Fetch", str(e))
            update_gate_status("FAIL", str(e), None)
            sys.exit(1)
        except Exception as e:
            log_pipeline_failure("T011_Data_Source_Fetch", str(e))
            update_gate_status("FAIL", f"Unexpected error: {str(e)}", None)
            sys.exit(1)
    else:
        print("Use --fetch to fetch data from source")

if __name__ == "__main__":
    main()
