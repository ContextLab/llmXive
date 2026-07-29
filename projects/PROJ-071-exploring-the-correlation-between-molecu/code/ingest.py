"""
Ingestion module for fetching FDA-approved drug structures and preparing data.
Handles data fetching, validation, merging, and gate status updates.
"""
from __future__ import annotations

import json
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
from datasets import load_dataset
from rdkit import Chem
from rdkit.Chem import AllChem

# Import error handlers
from error_handlers import DataFetchError, DataInefficiencyError

# Import logging utilities
from logging_config import get_logger, log_operation, log_pipeline_failure

# Configure module logger
logger = logging.getLogger(__name__)
reproducibility_logger = get_logger("ingest")


def get_data_path(filename: str) -> Path:
    """Get absolute path for a data file."""
    return Path(__file__).parent.parent / "data" / filename


def fetch_fda_drugs() -> pd.DataFrame:
    """
    Fetch FDA-approved drug structures from HuggingFace.
    Returns a DataFrame with SMILES and metadata.
    """
    dataset_name = "Synthyra/FDA-Approved-Drugs"
    logger.info(f"Fetching dataset: {dataset_name}")

    try:
        # Load dataset with streaming to handle large sizes
        dataset = load_dataset(dataset_name, streaming=True)

        # Check available splits
        available_splits = list(dataset.keys())
        logger.info(f"Available splits: {available_splits}")

        # The dataset might not have a 'train' split explicitly named
        # We need to find the correct split name
        split_name = None
        for split in available_splits:
            if 'train' in split.lower() or 'default' in split.lower():
                split_name = split
                break

        if split_name is None:
            # Fallback: try to use the first available split
            split_name = available_splits[0] if available_splits else None

        if split_name is None:
            raise DataFetchError(f"No valid split found in dataset {dataset_name}. Available: {available_splits}")

        logger.info(f"Using split: {split_name}")

        # Load the split into a DataFrame
        # Since we're streaming, we need to convert to list first
        data_list = []
        for item in dataset[split_name]:
            data_list.append(item)

        df = pd.DataFrame(data_list)

        # Verify required columns exist
        required_cols = ['smiles', 'name', 'synonyms']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise DataFetchError(f"Missing required columns: {missing_cols}")

        logger.info(f"Successfully fetched {len(df)} records with columns: {list(df.columns)}")
        return df

    except Exception as e:
        error_msg = f"Failed to fetch dataset: {str(e)}"
        logger.error(error_msg)
        # Log to reproducibility logger as well
        log_operation("fetch_fda_drugs", status="failed", error=str(e))
        raise DataFetchError(error_msg) from e


def validate_smiles_series(smiles_series: pd.Series) -> Tuple[pd.Series, pd.DataFrame]:
    """
    Validate a series of SMILES strings.
    Returns (valid_smiles_series, excluded_molecules_df).
    """
    valid_indices = []
    excluded_data = []

    for idx, smiles in smiles_series.items():
        if not isinstance(smiles, str) or not smiles.strip():
            excluded_data.append({
                'smiles': str(smiles) if smiles is not None else "None",
                'error_type': 'empty_or_invalid_type',
                'timestamp': pd.Timestamp.now().isoformat()
            })
            continue

        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is not None:
                # Check for basic valence issues
                Chem.SanitizeMol(mol)
                valid_indices.append(idx)
            else:
                excluded_data.append({
                    'smiles': smiles,
                    'error_type': 'rdkit_parse_failed',
                    'timestamp': pd.Timestamp.now().isoformat()
                })
        except Exception as e:
            excluded_data.append({
                'smiles': smiles,
                'error_type': f'validation_error_{type(e).__name__}',
                'timestamp': pd.Timestamp.now().isoformat()
            })

    valid_smiles = smiles_series.iloc[valid_indices] if valid_indices else pd.Series(dtype=str)
    excluded_df = pd.DataFrame(excluded_data) if excluded_data else pd.DataFrame(columns=['smiles', 'error_type', 'timestamp'])

    return valid_smiles, excluded_df


def filter_valid_smiles(df: pd.DataFrame, smiles_col: str = 'smiles') -> pd.DataFrame:
    """
    Filter DataFrame to keep only rows with valid SMILES.
    Logs excluded molecules to data/processed/excluded_molecules.csv.
    """
    if smiles_col not in df.columns:
        raise ValueError(f"Column '{smiles_col}' not found in DataFrame")

    logger.info(f"Validating {len(df)} SMILES strings in column '{smiles_col}'")

    valid_smiles, excluded_df = validate_smiles_series(df[smiles_col])

    # Log excluded molecules
    excluded_path = get_data_path("processed/excluded_molecules.csv")
    excluded_path.parent.mkdir(parents=True, exist_ok=True)

    if not excluded_df.empty:
        # Append to existing file if it exists
        if excluded_path.exists():
            existing_df = pd.read_csv(excluded_path)
            combined_df = pd.concat([existing_df, excluded_df], ignore_index=True)
            combined_df.to_csv(excluded_path, index=False)
        else:
            excluded_df.to_csv(excluded_path, index=False)

        logger.info(f"Excluded {len(excluded_df)} invalid molecules. Saved to {excluded_path}")
    else:
        logger.info("No molecules excluded during validation")

    # Return filtered DataFrame
    filtered_df = df.loc[valid_smiles.index].reset_index(drop=True)
    logger.info(f"Filtered dataset: {len(filtered_df)} valid molecules remaining")

    return filtered_df


def check_degradation_columns(df: pd.DataFrame) -> List[str]:
    """
    Check for degradation-related columns in the DataFrame.
    Returns list of found degradation columns.
    """
    potential_cols = ['half_life', 'degradation_rate', 't12', 't_half', 'k', 'rate_constant']
    found_cols = [col for col in potential_cols if col in df.columns]
    return found_cols


def update_gate_status(status: str, reason: str = "", n: int = 0) -> Dict[str, Any]:
    """
    Update gate_status.json with current status.
    """
    gate_path = get_data_path("gate_status.json")
    gate_path.parent.mkdir(parents=True, exist_ok=True)

    gate_data = {
        "status": status,
        "reason": reason,
        "n": n,
        "timestamp": pd.Timestamp.now().isoformat()
    }

    with open(gate_path, 'w') as f:
        json.dump(gate_data, f, indent=2)

    logger.info(f"Gate status updated: {status} (N={n})")
    return gate_data


def save_merged_dataset(df: pd.DataFrame, output_path: str) -> None:
    """Save merged dataset to CSV."""
    path = get_data_path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    logger.info(f"Saved merged dataset to {path} ({len(df)} rows)")


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def merge_structural_degradation_data(structural_df: pd.DataFrame, degradation_cols: List[str]) -> pd.DataFrame:
    """
    Merge structural data with degradation data if available.
    Since the FDA dataset only has structures, we just return the structural data
    and note the absence of degradation columns.
    """
    if degradation_cols:
        logger.warning(f"Found degradation columns: {degradation_cols}")
        # In a real scenario, we would merge here
        return structural_df
    else:
        logger.info("No degradation columns found in structural dataset")
        return structural_df


def run_data_availability_gate(df: pd.DataFrame) -> bool:
    """
    Run the data availability gate.
    Returns True if gate passes, False otherwise.
    """
    # Check for degradation columns
    degradation_cols = check_degradation_columns(df)
    n = len(df)

    if not degradation_cols:
        logger.warning("No degradation data found in dataset")
        update_gate_status("FAIL", "No verified degradation source found", n)
        return False

    if n < 30:
        logger.warning(f"Insufficient data: N={n} < 30")
        update_gate_status("FAIL", f"Insufficient sample size (N={n})", n)
        return False

    update_gate_status("PASS", "Data sufficient for analysis", n)
    return True


def generate_insufficiency_report(reason: str, n: int) -> Path:
    """Generate data insufficiency report."""
    report_path = get_data_path("data_insufficiency_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    content = f"""# Data Insufficiency Report

## Summary
The data availability gate has failed due to insufficient data.

## Details
- **Reason**: {reason}
- **Sample Size (N)**: {n}
- **Threshold**: 30 records
- **Timestamp**: {pd.Timestamp.now().isoformat()}

## Action
The pipeline has halted analysis as per the Data Availability Gate requirements.
Further correlation analysis cannot proceed without verified degradation data.

## Next Steps
1. Identify alternative data sources with degradation rates
2. Re-run the pipeline once data is available
"""

    with open(report_path, 'w') as f:
        f.write(content)

    logger.info(f"Generated insufficiency report: {report_path}")
    return report_path


def main():
    """Main entry point for ingestion pipeline."""
    logger.info("Starting FDA drug data ingestion pipeline")

    try:
        # Step 1: Fetch FDA drugs
        logger.info("Step 1: Fetching FDA-approved drug structures")
        df = fetch_fda_drugs()

        # Step 2: Filter valid SMILES
        logger.info("Step 2: Filtering valid SMILES")
        df_valid = filter_valid_smiles(df, 'smiles')

        # Step 3: Check degradation columns
        logger.info("Step 3: Checking for degradation data")
        degradation_cols = check_degradation_columns(df_valid)

        # Step 4: Merge data (structural only if no degradation)
        logger.info("Step 4: Merging structural data")
        df_merged = merge_structural_degradation_data(df_valid, degradation_cols)

        # Step 5: Save merged dataset
        output_path = "processed/structural_subset.csv"
        save_merged_dataset(df_merged, output_path)

        # Step 6: Run data availability gate
        logger.info("Step 6: Running data availability gate")
        gate_passed = run_data_availability_gate(df_merged)

        if not gate_passed:
            # Generate report and raise error
            gate_data = json.loads(get_data_path("gate_status.json").read_text())
            generate_insufficiency_report(gate_data.get("reason", "Unknown"), gate_data.get("n", 0))
            raise DataInefficiencyError("Data availability gate failed")

        # Step 7: Calculate checksums
        output_file = get_data_path(output_path)
        checksum = calculate_checksum(output_file)
        checksum_path = get_data_path("checksums.txt")
        with open(checksum_path, 'w') as f:
            f.write(f"{checksum}  {output_path}\n")
        logger.info(f"Checksum saved: {checksum}")

        logger.info("Ingestion pipeline completed successfully")
        return df_merged

    except DataFetchError as e:
        logger.error(f"Data fetch failed: {str(e)}")
        log_pipeline_failure(logger, "T012_Data_Fetch", str(e))
        raise
    except DataInefficiencyError as e:
        logger.error(f"Data insufficiency: {str(e)}")
        # This is a graceful exit for the insufficiency path
        return None
    except Exception as e:
        logger.exception(f"Unexpected error in ingestion pipeline: {str(e)}")
        log_pipeline_failure(logger, "T016b_Filter_Valid_SMILES", str(e))
        raise


if __name__ == "__main__":
    main()