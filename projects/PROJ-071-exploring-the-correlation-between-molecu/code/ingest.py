import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd
import requests
from datasets import load_dataset
from rdkit import Chem

# Import from sibling modules as per API surface
from descriptors import calculate_descriptors_batch
from error_handlers import handle_molecule_error, PipelineStage
from logging_config import get_logger, log_error, log_pipeline_complete, log_pipeline_failure

logger = get_logger(__name__)

def fetch_fda_drugs() -> pd.DataFrame:
    """
    Fetches FDA-approved drug structures from the HuggingFace dataset 'Synthyra/FDA-Approved-Drugs'.
    Returns a DataFrame with SMILES and other available columns.
    """
    logger.info("Fetching FDA-approved drugs dataset from HuggingFace...")
    try:
        # Load the specific dataset
        dataset = load_dataset("Synthyra/FDA-Approved-Drugs", split="train")
        df = dataset.to_pandas()
        
        # Ensure SMILES column exists and is string type
        if 'SMILES' not in df.columns:
            # Fallback check for common variations
            if 'smiles' in df.columns:
                df['SMILES'] = df['smiles']
            else:
                raise ValueError("Dataset does not contain a 'SMILES' column.")
        
        df['SMILES'] = df['SMILES'].astype(str)
        logger.info(f"Dataset loaded successfully. Shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        raise

def check_degradation_columns(df: pd.DataFrame) -> bool:
    """
    Checks if the DataFrame contains degradation-related columns (e.g., half-life, rate constant).
    Returns True if at least one degradation column is found.
    """
    possible_cols = ['half_life', 't1/2', 'half_life_hours', 'degradation_rate', 'k', 'rate_constant']
    found_cols = [c for c in possible_cols if c in df.columns]
    
    if not found_cols:
        logger.warning("No degradation columns found in the dataset.")
        return False
    
    logger.info(f"Found degradation columns: {found_cols}")
    return True

def validate_smiles_series(smiles_series: pd.Series) -> pd.Series:
    """
    Validates a series of SMILES strings using RDKit.
    Returns a boolean series indicating validity.
    """
    valid_mask = []
    for smi in smiles_series:
        try:
            mol = Chem.MolFromSmiles(smi)
            valid_mask.append(mol is not None)
        except Exception:
            valid_mask.append(False)
    return pd.Series(valid_mask, index=smiles_series.index)

def generate_insufficiency_report(reason: str, output_path: Path) -> None:
    """
    Generates a report indicating data insufficiency and exits the pipeline.
    """
    report_content = f"""
    # Data Insufficiency Report

    **Reason**: {reason}
    **Status**: Pipeline halted.

    The data availability gate has been triggered. Insufficient data to proceed with analysis.
    """
    with open(output_path, 'w') as f:
        f.write(report_content.strip())
    logger.critical(report_content)

def run_data_availability_gate(df: pd.DataFrame, min_records: int = 30) -> bool:
    """
    Checks if the dataset has enough records with valid degradation data.
    Returns True if the gate passes, False otherwise.
    """
    valid_count = df.dropna(subset=['half_life_hours']).shape[0] if 'half_life_hours' in df.columns else 0
    
    if valid_count < min_records:
        generate_insufficiency_report(f"Only {valid_count} records with valid half-life data found (minimum: {min_records}).", 
                                    Path("data/data_insufficiency_report.md"))
        return False
    
    logger.info(f"Data Availability Gate passed: {valid_count} valid records found.")
    return True

def merge_structural_degradation_data(structural_df: pd.DataFrame, degradation_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merges structural and degradation dataframes on a common key (e.g., Drug Name or ID).
    For this task, we assume the fetch function returns a combined dataset or we join on index if aligned.
    Since the dataset 'Synthyra/FDA-Approved-Drugs' typically contains both structure and some properties,
    we assume the fetch returns a unified DF. If separate, this would perform a merge.
    Here we simulate the merge logic assuming the fetched DF has both.
    """
    # In a real scenario with separate sources, we would merge here.
    # For this implementation, we assume the fetched DF is the structural base
    # and degradation info is either present or we need to join.
    # Given the task context, we proceed with the fetched DF as the source of truth.
    return structural_df

def filter_valid_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters the DataFrame to keep only rows with valid SMILES and non-null degradation values.
    """
    if 'SMILES' not in df.columns or 'half_life_hours' not in df.columns:
        # Attempt to find degradation column if standard name missing
        deg_cols = [c for c in df.columns if 'half' in c.lower() or 't1/2' in c.lower()]
        if deg_cols:
            df['half_life_hours'] = df[deg_cols[0]]
        else:
            raise ValueError("Cannot find degradation column to filter.")

    # Validate SMILES
    valid_smiles = validate_smiles_series(df['SMILES'])
    df_filtered = df[valid_smiles].copy()
    
    # Filter non-null degradation
    df_filtered = df_filtered.dropna(subset=['half_life_hours'])
    
    logger.info(f"Filtered records: {len(df)} -> {len(df_filtered)}")
    return df_filtered

def calculate_checksums(file_path: Path, checksum_path: Path) -> None:
    """
    Calculates the SHA256 checksum of a file and writes it to a checksums file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    checksum = sha256_hash.hexdigest()
    checksum_entry = f"{checksum}  {file_path.name}\n"
    
    with open(checksum_path, 'a') as f:
        f.write(checksum_entry)
    
    logger.info(f"Checksum calculated for {file_path.name}: {checksum}")

def save_merged_dataset(df: pd.DataFrame, output_path: Path, checksum_path: Path) -> None:
    """
    Saves the merged and processed dataset to CSV and generates checksums.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate descriptors for all valid molecules
    logger.info("Calculating molecular descriptors...")
    descriptor_df = calculate_descriptors_batch(df['SMILES'].tolist())
    
    # Merge descriptors back to main dataframe
    df_merged = pd.concat([df.reset_index(drop=True), descriptor_df], axis=1)
    
    # Save to CSV
    df_merged.to_csv(output_path, index=False)
    logger.info(f"Merged dataset saved to {output_path}")
    
    # Clear checksum file if exists to start fresh for this run
    if checksum_path.exists():
        checksum_path.unlink()
    
    # Generate checksum
    calculate_checksums(output_path, checksum_path)
    logger.info(f"Checksums saved to {checksum_path}")

def main():
    """
    Main entry point for T017: Save merged dataset and generate checksums.
    """
    try:
        # 1. Fetch Data
        df_raw = fetch_fda_drugs()
        
        # 2. Check Degradation Columns
        if not check_degradation_columns(df_raw):
            generate_insufficiency_report("No degradation columns found in dataset.", Path("data/data_insufficiency_report.md"))
            return 1
        
        # 3. Prepare Data (Standardize column names if necessary)
        # Assuming the dataset has 'half_life_hours' or we map it
        if 'half_life_hours' not in df_raw.columns:
            # Map common variations to standard name
            for col in ['half_life', 't1/2']:
                if col in df_raw.columns:
                    df_raw['half_life_hours'] = df_raw[col]
                    break
        
        # 4. Filter Valid Records
        df_valid = filter_valid_records(df_raw)
        
        # 5. Run Data Availability Gate
        if not run_data_availability_gate(df_valid, min_records=30):
            return 1
        
        # 6. Save Merged Dataset and Checksums
        output_path = Path("data/processed/merged_drugs.csv")
        checksum_path = Path("data/checksums.txt")
        
        save_merged_dataset(df_valid, output_path, checksum_path)
        
        log_pipeline_complete("T017", "Merged dataset saved and checksums generated.")
        return 0
        
    except Exception as e:
        log_pipeline_failure("T017", str(e))
        raise

if __name__ == "__main__":
    sys.exit(main())
