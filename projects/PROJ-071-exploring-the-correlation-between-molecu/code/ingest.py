"""Data ingestion and gate enforcement for molecular complexity study."""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from datasets import load_dataset

# Import from local modules
from logging_config import log_pipeline_failure, log_pipeline_start, log_pipeline_complete
from error_handlers import DataIngestionError, DataFetchError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_data_path() -> Path:
    """Get the project data directory."""
    return Path(__file__).parent.parent / "data"


def fetch_fda_drugs() -> pd.DataFrame:
    """Fetch FDA-approved drugs from Synthyra dataset.

    Returns:
        DataFrame with SMILES and molecule data.
    
    Raises:
        DataFetchError: If dataset cannot be fetched or lacks required columns.
    """
    try:
        logger.info("Fetching FDA-approved drugs from Synthyra dataset...")
        # Load the dataset with streaming to handle large sizes
        dataset = load_dataset(
            "Synthyra/FDA-Approved-Drugs",
            split="train",
            streaming=True
        )
        
        # Convert to DataFrame
        df_list = list(dataset)
        df = pd.DataFrame(df_list)
        
        # Verify required columns exist
        required_cols = ["canonical_smiles", "smiles"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            raise DataFetchError(f"Dataset missing required columns: {missing_cols}")
        
        logger.info(f"Fetched {len(df)} drugs from Synthyra dataset")
        return df
        
    except KeyError as e:
        logger.error(f"Failed to fetch dataset: {e}")
        raise DataFetchError(f"Dataset structure error: {e}")
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        raise DataFetchError(f"Failed to fetch FDA drugs: {e}")


def validate_smiles_series(smiles_series: pd.Series) -> Tuple[pd.Series, List[str]]:
    """Validate SMILES strings and return valid ones.
    
    Args:
        smiles_series: Series of SMILES strings.
        
    Returns:
        Tuple of (valid_smiles_series, list_of_invalid_smiles)
    """
    from rdkit import Chem
    
    valid_smiles = []
    invalid_smiles = []
    
    for smiles in smiles_series:
        if pd.isna(smiles) or not isinstance(smiles, str) or not smiles.strip():
            invalid_smiles.append(smiles if not pd.isna(smiles) else "NaN")
            continue
            
        mol = Chem.MolFromSmiles(smiles)
        if mol is not None:
            valid_smiles.append(smiles)
        else:
            invalid_smiles.append(smiles)
    
    return pd.Series(valid_smiles), invalid_smiles


def filter_valid_smiles(df: pd.DataFrame, smiles_col: str = "canonical_smiles") -> pd.DataFrame:
    """Filter DataFrame to keep only rows with valid SMILES.
    
    Args:
        df: Input DataFrame.
        smiles_col: Column name containing SMILES strings.
        
    Returns:
        Filtered DataFrame with valid SMILES only.
    """
    valid_series, invalid_list = validate_smiles_series(df[smiles_col])
    
    if invalid_list:
        logger.warning(f"Filtered out {len(invalid_list)} invalid SMILES strings")
        # Log excluded molecules
        log_errors_to_file(invalid_list, "invalid_smiles")
    
    return df[df[smiles_col].isin(valid_series)]


def log_errors_to_file(invalid_list: List[str], error_type: str) -> None:
    """Log invalid molecules to a file."""
    filepath = get_data_path() / "processed" / "excluded_molecules.csv"
    os.makedirs(filepath.parent, exist_ok=True)
    
    timestamp = datetime.utcnow().isoformat()
    
    with open(filepath, 'a', newline='') as f:
        writer = csv.writer(f)
        # Write header if file is empty
        if os.path.getsize(filepath) == 0:
            writer.writerow(['smiles', 'error_type', 'timestamp'])
        
        for smiles in invalid_list:
            writer.writerow([smiles, error_type, timestamp])


def check_degradation_columns(df: pd.DataFrame) -> List[str]:
    """Check for degradation-related columns in DataFrame.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        List of found degradation column names.
    """
    degradation_candidates = ['half_life', 'degradation_rate', 't12', 't_half', 'half_life_hours']
    found_cols = [col for col in df.columns if col in degradation_candidates]
    return found_cols


def update_gate_status(
    status: str,
    reason: str = "",
    n: int = 0,
    gate_file: Optional[Path] = None
) -> Dict:
    """Update the gate status JSON file.
    
    Args:
        status: "PASS" or "FAIL".
        reason: Reason for the status.
        n: Number of records.
        gate_file: Path to gate status file (defaults to data/gate_status.json).
        
    Returns:
        The updated status dictionary.
    """
    if gate_file is None:
        gate_file = get_data_path() / "gate_status.json"
    
    os.makedirs(gate_file.parent, exist_ok=True)
    
    gate_data = {
        "status": status,
        "reason": reason,
        "N": n,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    with open(gate_file, 'w') as f:
        json.dump(gate_data, f, indent=2)
    
    logger.info(f"Gate status updated: {status} (N={n})")
    return gate_data


def save_merged_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Save merged dataset to CSV.
    
    Args:
        df: DataFrame to save.
        output_path: Path to save the CSV file.
    """
    os.makedirs(output_path.parent, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved merged dataset to {output_path} ({len(df)} records)")


def calculate_checksum(filepath: Path) -> str:
    """Calculate SHA256 checksum of a file.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        SHA256 hash string.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def save_checksums(checksums: Dict[str, str], checksum_file: Path) -> None:
    """Save checksums to a text file.
    
    Args:
        checksums: Dictionary of filename -> checksum.
        checksum_file: Path to save the checksums.
    """
    os.makedirs(checksum_file.parent, exist_ok=True)
    with open(checksum_file, 'w') as f:
        for filename, checksum in checksums.items():
            f.write(f"{checksum}  {filename}\n")


def merge_structural_degradation_data(
    structural_df: pd.DataFrame,
    degradation_df: pd.DataFrame,
    key_col: str = "canonical_smiles"
) -> pd.DataFrame:
    """Merge structural and degradation data on SMILES.
    
    Args:
        structural_df: DataFrame with molecular structures.
        degradation_df: DataFrame with degradation data.
        key_col: Column name to join on.
        
    Returns:
        Merged DataFrame.
    """
    merged = pd.merge(
        structural_df,
        degradation_df,
        on=key_col,
        how='inner'
    )
    logger.info(f"Merged datasets: {len(merged)} records found")
    return merged


def run_data_availability_gate(
    structural_df: pd.DataFrame,
    degradation_df: Optional[pd.DataFrame] = None
) -> Tuple[Dict, Optional[pd.DataFrame]]:
    """Run the data availability gate.
    
    Args:
        structural_df: DataFrame with structural data.
        degradation_df: Optional DataFrame with degradation data.
        
    Returns:
        Tuple of (gate_status_dict, merged_df_or_None)
    """
    gate_file = get_data_path() / "gate_status.json"
    
    # If degradation data is provided, attempt merge
    if degradation_df is not None:
        merged_df = merge_structural_degradation_data(structural_df, degradation_df)
        degradation_cols = check_degradation_columns(merged_df)
        
        if not degradation_cols:
            logger.warning("No degradation columns found in merged data")
            gate_status = update_gate_status(
                "FAIL",
                "No verified degradation data source found",
                0,
                gate_file
            )
            return gate_status, None
        
        n = len(merged_df)
        if n < 30:
            logger.warning(f"Insufficient data: N={n} < 30")
            gate_status = update_gate_status(
                "FAIL",
                f"N < 30 (found {n})",
                n,
                gate_file
            )
            generate_insufficiency_report(n, "Data Availability Gate")
            return gate_status, None
        
        # Gate passed
        gate_status = update_gate_status("PASS", "Data available", n, gate_file)
        return gate_status, merged_df
    
    else:
        # No degradation data available - Gate fails
        logger.info("No degradation data provided - Gate FAIL")
        gate_status = update_gate_status(
            "FAIL",
            "No verified degradation data source found",
            0,
            gate_file
        )
        generate_insufficiency_report(0, "Data Availability Gate")
        return gate_status, None


def generate_insufficiency_report(n: int, gate_name: str) -> None:
    """Generate an insufficiency report when gate fails.
    
    Args:
        n: Number of records found.
        gate_name: Name of the gate that failed.
    """
    report_path = get_data_path().parent / "data_insufficiency_report.md"
    
    content = f"""# Data Insufficiency Report

## Gate: {gate_name}

## Status: FAIL

### Details
- **Records Found**: {n}
- **Required Minimum**: 30
- **Reason**: Insufficient data to proceed with analysis.

### Next Steps
The pipeline cannot proceed with statistical analysis due to insufficient data.
Please verify data sources or adjust the inclusion criteria.

### Timestamp
{datetime.utcnow().isoformat()}
"""
    
    with open(report_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Generated insufficiency report: {report_path}")


def main():
    """Main entry point for the ingestion script."""
    log_pipeline_start("T012_Ingest_And_Gate", {"task": "T012"})
    
    try:
        # Check gate status first
        gate_file = get_data_path() / "gate_status.json"
        
        if gate_file.exists():
            with open(gate_file, 'r') as f:
                existing_gate = json.load(f)
            
            if existing_gate.get("status") == "FAIL":
                logger.info("Gate already FAIL - reading structural subset and exiting")
                # Read structural subset if it exists
                structural_file = get_data_path() / "processed" / "structural_subset.csv"
                if structural_file.exists():
                    df = pd.read_csv(structural_file)
                    logger.info(f"Loaded structural subset: {len(df)} records")
                else:
                    logger.warning("Structural subset not found, fetching fresh data...")
                    # Fetch fresh data to create structural subset
                    raw_df = fetch_fda_drugs()
                    structural_df = filter_valid_smiles(raw_df)
                    structural_df.to_csv(structural_file, index=False)
                    logger.info(f"Created structural subset: {len(structural_df)} records")
                
                log_pipeline_complete("T012_Ingest_And_Gate", True, {"reason": "Gate was already FAIL"})
                return
        
        # Fetch FDA drugs
        raw_df = fetch_fda_drugs()
        
        # Validate and filter SMILES
        structural_df = filter_valid_smiles(raw_df)
        
        # Save structural subset (always produced)
        structural_file = get_data_path() / "processed" / "structural_subset.csv"
        structural_df.to_csv(structural_file, index=False)
        logger.info(f"Saved structural subset: {len(structural_df)} records")
        
        # Check for degradation data (T011b logic)
        # In this implementation, we assume no degradation data is found
        # as per the project's verified constraint
        logger.info("Searching for degradation data...")
        # T011b would have already determined no source exists
        # We proceed with Gate FAIL logic
        
        gate_status, merged_df = run_data_availability_gate(structural_df, degradation_df=None)
        
        if gate_status["status"] == "PASS":
            if merged_df is not None:
                # Save merged data
                merged_file = get_data_path() / "processed" / "merged_drugs.csv"
                save_merged_dataset(merged_df, merged_file)
                
                # Calculate and save checksums
                checksum = calculate_checksum(merged_file)
                checksums = {"merged_drugs.csv": checksum}
                save_checksums(checksums, get_data_path() / "checksums.txt")
        else:
            logger.info(f"Gate failed: {gate_status['reason']}")
            # structural_subset.csv is already saved above
        
        log_pipeline_complete("T012_Ingest_And_Gate", True, {"gate_status": gate_status["status"]})
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        log_pipeline_failure("T012_Ingest_And_Gate", str(e))
        raise DataIngestionError(f"Ingestion failed: {e}")


if __name__ == "__main__":
    main()