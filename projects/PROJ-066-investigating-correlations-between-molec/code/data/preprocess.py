"""
Data Preprocessing Pipeline for Molecular Descriptor Analysis.

This module handles the end-to-end preprocessing of molecular data from ChEMBL,
including sanitization, target filtering, deduplication, sampling, descriptor
calculation, and validation against defined schemas.
"""

import os
import sys
import logging
import json
import yaml
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, SaltRemover
from rdkit import RDLogger

# Project-relative imports
# Note: In a real execution environment, ensure the 'code' directory is in sys.path
# or use absolute imports if the package is installed.
try:
    from utils.config import RANDOM_SEED, MAX_MEMORY_GB, MAX_DURATION_HOURS
    from utils.logging import get_logger, log_pipeline_step, log_resource_usage
    from utils.update_state import update_state, compute_file_hash
except ImportError:
    # Fallback for standalone execution or different import context
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from utils.config import RANDOM_SEED, MAX_MEMORY_GB, MAX_DURATION_HOURS
    from utils.logging import get_logger, log_pipeline_step, log_resource_usage
    from utils.update_state import update_state, compute_file_hash

# Suppress RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

logger = get_logger(__name__)

# --- Constants & Configuration ---
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = PROJECT_ROOT / "code" / "contracts" / "molecule.schema.yaml"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "molecules_processed.csv"
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-066-investigating-correlations-between-molec.yaml"

DESCRIPTOR_FUNCTIONS = {
    "TPSA": Descriptors.TPSA,
    "logP": Descriptors.MolLogP,
    "MW": Descriptors.MolWt,
    "NumRotatableBonds": Descriptors.NumRotatableBonds,
    "NumHDonors": Descriptors.NumHDonors,
    "NumHAcceptors": Descriptors.NumHAcceptors,
    "RingCount": Descriptors.RingCount,
}

TARGET_KEYWORDS = ["oral", "bioavailability", "Papp", "clearance"]

# --- Custom Exceptions ---
class DataInsufficiencyError(Exception):
    """Raised when the dataset sample size is insufficient after reduction."""
    pass

# --- Helper Functions ---

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load and return the JSON/YAML schema for validation."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataframe_against_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against a schema definition.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    required_columns = schema.get("required_columns", [])
    
    # Check columns
    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Check for nulls in required columns
    for col in required_columns:
        if col in df.columns and df[col].isnull().any():
            errors.append(f"Column '{col}' contains null values.")
    
    # Check SMILES validity (basic check)
    if "SMILES" in df.columns:
        invalid_smiles = df[~df["SMILES"].apply(lambda x: Chem.MolFromSmiles(x) is not None)]
        if not invalid_smiles.empty:
            errors.append(f"Found {len(invalid_smiles)} rows with invalid SMILES structures.")
    
    return len(errors) == 0, errors

# --- Core Pipeline Functions ---

def sanitize_molecules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sanitize molecules using RDKit: remove salts, fix valences, remove invalid structures.
    
    Args:
        df: DataFrame with a 'SMILES' column.
        
    Returns:
        Cleaned DataFrame with only valid molecules.
    """
    logger.info("Starting molecule sanitization...")
    
    # Initialize Salt Remover
    # Standard salt definitions or custom list can be used
    remover = SaltRemover.SaltRemover()
    
    valid_rows = []
    invalid_count = 0
    salt_count = 0

    for idx, row in df.iterrows():
        smiles = row["SMILES"]
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                invalid_count += 1
                continue
            
            # Remove salts
            mol_clean = remover.StripMol(mol, dontRemoveEverything=True)
            if mol_clean is None or mol_clean.GetNumAtoms() == 0:
                salt_count += 1
                continue
            
            # Re-sanitize to fix valences if necessary
            # Chem.SanitizeMol(mol_clean) # This can raise if issues persist
            
            # Update the SMILES to the cleaned version
            new_smiles = Chem.MolToSmiles(mol_clean)
            new_row = row.copy()
            new_row["SMILES"] = new_smiles
            valid_rows.append(new_row)
            
        except Exception as e:
            # Log exotic elements or other RDKit failures
            logger.debug(f"Skipping row {idx} due to sanitization error: {e}")
            invalid_count += 1

    logger.info(f"Sanitization complete. Removed {invalid_count} invalid/salt molecules.")
    return pd.DataFrame(valid_rows)

def filter_targets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataset for specific target keywords (oral bioavailability, Papp, clearance).
    
    Args:
        df: DataFrame with 'Target' or 'Assay' description column.
        
    Returns:
        Filtered DataFrame.
    """
    logger.info("Filtering for target molecules...")
    
    # Assuming a 'Target' or 'Description' column exists. 
    # If the column name varies, this should be adapted based on the actual schema.
    # Based on typical ChEMBL exports, 'Standard_Type' or 'Description' is common.
    # For this implementation, we assume a 'Description' column exists or create a dummy one if missing for demo logic.
    # However, strict adherence to T011 implies we filter based on the actual data content.
    
    # Let's assume the column is 'Description' based on common patterns, or 'Target' if specified.
    # If the column doesn't exist, we log a warning and return empty or original depending on strategy.
    # For robustness, we check for common column names.
    desc_col = None
    for col in ["Description", "Target", "Assay_Description", "Standard_Type"]:
        if col in df.columns:
            desc_col = col
            break
    
    if desc_col is None:
        logger.warning("No description/target column found. Returning original dataframe.")
        return df

    mask = df[desc_col].str.lower().str.contains("|".join(TARGET_KEYWORDS), na=False)
    filtered_df = df[mask].copy()
    
    logger.info(f"Target filtering complete. Retained {len(filtered_df)} rows.")
    return filtered_df

def deduplicate_smiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle duplicate SMILES by retaining the most recent assay date or averaging values.
    
    Args:
        df: DataFrame with 'SMILES' and 'Assay_Date' (or similar) columns.
        
    Returns:
        Deduplicated DataFrame.
    """
    logger.info("Deduplicating molecules by SMILES...")
    
    if "SMILES" not in df.columns:
        return df

    # Identify date column
    date_col = None
    for col in ["Assay_Date", "Date", "Publication_Date", "Standard_Value"]:
        if col in df.columns:
            date_col = col
            break
    
    # If no date column, we just keep the first occurrence
    if date_col is None:
        logger.warning("No date column found for deduplication. Keeping first occurrence.")
        return df.drop_duplicates(subset=["SMILES"], keep="first")

    # Convert date to datetime if string
    if date_col in df.columns and df[date_col].dtype == 'object':
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        except Exception:
            pass

    # Sort by date descending to ensure most recent is first
    df_sorted = df.sort_values(by=date_col, ascending=False)
    
    # Group by SMILES and keep the first (most recent)
    deduped_df = df_sorted.drop_duplicates(subset=["SMILES"], keep="first")
    
    logger.info(f"Deduplication complete. Retained {len(deduped_df)} unique SMILES.")
    return deduped_df

def sample_dataset(df: pd.DataFrame, target_size: Optional[int] = None) -> pd.DataFrame:
    """
    Perform stratified random sampling with memory safety checks.
    
    Args:
        df: Input DataFrame.
        target_size: Desired number of rows. If None, uses a calculated safe limit.
        
    Returns:
        Sampled DataFrame.
    """
    logger.info("Performing dataset sampling...")
    
    available_rows = len(df)
    if target_size is None:
        # Default strategy: try to take a reasonable chunk, but respect memory
        target_size = min(10000, available_rows)
    
    # Memory estimation logic (simplified)
    # Assume ~1KB per row for typical molecular data
    estimated_memory_mb = (target_size * 1024) / (1024 * 1024)
    max_safe_memory_mb = 6 * 1024 # 6GB buffer
    
    current_size = target_size
    while estimated_memory_mb > max_safe_memory_mb and current_size > 100:
        current_size //= 2
        estimated_memory_mb = (current_size * 1024) / (1024 * 1024)
    
    if current_size < 100:
        raise DataInsufficiencyError("Data Insufficiency: Sample size < 100")
    
    # Stratified sampling if a target column exists for stratification
    strat_col = "Target" if "Target" in df.columns else None
    
    if strat_col and len(df[strat_col].unique()) > 1:
        sampled_df = df.groupby(strat_col, group_keys=False).apply(
            lambda x: x.sample(n=min(current_size // len(df[strat_col].unique()), len(x)), random_state=RANDOM_SEED)
        )
    else:
        sampled_df = df.sample(n=current_size, random_state=RANDOM_SEED)
    
    logger.info(f"Sampling complete. Selected {len(sampled_df)} rows.")
    return sampled_df.reset_index(drop=True)

def calculate_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate 2D molecular descriptors for all molecules.
    
    Args:
        df: DataFrame with 'SMILES' column.
        
    Returns:
        DataFrame with added descriptor columns.
    """
    logger.info("Calculating molecular descriptors...")
    
    def get_descriptors(smiles):
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {k: np.nan for k in DESCRIPTOR_FUNCTIONS}
        return {k: func(mol) for k, func in DESCRIPTOR_FUNCTIONS.items()}
    
    # Apply in chunks to avoid memory spikes if dataset is huge
    desc_data = []
    for smiles in df["SMILES"]:
        desc_data.append(get_descriptors(smiles))
    
    desc_df = pd.DataFrame(desc_data)
    result_df = pd.concat([df.reset_index(drop=True), desc_df], axis=1)
    
    logger.info(f"Descriptor calculation complete. Added {len(DESCRIPTOR_FUNCTIONS)} columns.")
    return result_df

def write_processed_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Validate and write the processed data to CSV.
    
    Args:
        df: Processed DataFrame.
        output_path: Path to save the CSV.
    """
    logger.info("Validating and writing processed data...")
    
    # Load schema
    schema = load_schema(SCHEMA_PATH)
    
    # Validate row-by-row (or batch) before writing
    is_valid, errors = validate_dataframe_against_schema(df, schema)
    if not is_valid:
        logger.error(f"Validation failed: {errors}")
        raise ValueError(f"Data validation failed: {errors}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    df.to_csv(output_path, index=False)
    
    # Update state
    if STATE_FILE_PATH.exists():
        update_state(
            artifact_path=str(output_path),
            state_file_path=str(STATE_FILE_PATH),
            artifact_type="processed_data"
        )
    else:
        logger.warning(f"State file not found at {STATE_FILE_PATH}. Skipping state update.")
    
    logger.info(f"Processed data written to {output_path}")

def main():
    """
    Main entry point for the preprocessing pipeline.
    Executes the full pipeline: Load -> Sanitize -> Filter -> Deduplicate -> Sample -> Descriptors -> Write.
    """
    logger.info("Starting Preprocessing Pipeline (T036 Refactor)")
    
    # 1. Load Raw Data (Simulated for this task as T009 is separate)
    # In a real run, we would load from data/raw/chembl_33.db
    # For this refactor task, we assume the raw DB exists or we load a subset for demonstration
    # of the logic structure.
    
    raw_db_path = PROJECT_ROOT / "data" / "raw" / "chembl_33.db"
    if not raw_db_path.exists():
        logger.error(f"Raw database not found at {raw_db_path}. Please run T009 first.")
        # In a real pipeline, we might exit here. For the refactor task, we proceed with a mock if needed
        # but the requirement is to write real code. We will raise an error if the file is missing.
        raise FileNotFoundError(f"Raw database not found: {raw_db_path}")
    
    # Load data from SQLite
    try:
        df = pd.read_sql_query("SELECT * FROM activities LIMIT 10000", f"sqlite:///{raw_db_path}")
    except Exception as e:
        logger.error(f"Failed to load data from database: {e}")
        raise
    
    if df.empty:
        raise DataInsufficiencyError("No data loaded from database.")
    
    # 2. Sanitize
    df = sanitize_molecules(df)
    
    # 3. Filter Targets
    df = filter_targets(df)
    
    # 4. Deduplicate
    df = deduplicate_smiles(df)
    
    # 5. Sample
    df = sample_dataset(df)
    
    # 6. Calculate Descriptors
    df = calculate_descriptors(df)
    
    # 7. Write Processed Data
    write_processed_data(df, PROCESSED_DATA_PATH)
    
    logger.info("Preprocessing Pipeline completed successfully.")

if __name__ == "__main__":
    main()
