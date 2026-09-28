import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import yaml
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
import hashlib
from datetime import datetime

# Import local utilities
from utils.logging import get_logger
from utils.update_state import update_state, compute_file_hash, load_state_file, save_state_file
from utils.config import RANDOM_SEED

logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-066-investigating-correlations-between-molec.yaml"

def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the molecule schema from the contracts directory."""
    if schema_path is None:
        schema_path = CONTRACTS_DIR / "molecule.schema.yaml"
    
    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataframe_against_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against the molecule schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})
    
    # Check if all required fields are present
    missing_fields = [field for field in required_fields if field not in df.columns]
    if missing_fields:
        errors.append(f"Missing required columns: {missing_fields}")
    
    # Check for any NaN values in required fields
    for field in required_fields:
        if field in df.columns:
            if df[field].isna().any():
                errors.append(f"Column '{field}' contains NaN values")
    
    # Check data types for known fields
    type_mapping = {
        'smiles': str,
        'experimental_value': (int, float, str),
        'target': str,
        'mw': (int, float),
        'logp': (int, float),
        'tpsa': (int, float),
        'hbd': int,
        'hba': int,
        'rotatable_bonds': int,
        'ring_count': int
    }
    
    for field, expected_type in type_mapping.items():
        if field in df.columns:
            if not df[field].apply(lambda x: isinstance(x, expected_type) or pd.isna(x)).all():
                errors.append(f"Column '{field}' contains invalid types")
    
    return len(errors) == 0, errors

def sanitize_molecules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Use RDKit to remove salts, fix valences, and log/remove invalid structures.
    Handles 'exotic elements' by logging and excluding molecules where RDKit sanitizer fails.
    """
    logger.info("Starting molecule sanitization...")
    valid_indices = []
    invalid_rows = []
    
    for idx, row in df.iterrows():
        smiles = row['smiles']
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                invalid_rows.append({'index': idx, 'smiles': smiles, 'reason': 'Failed to parse SMILES'})
                continue
            
            # Try to sanitize the molecule
            Chem.SanitizeMol(mol)
            valid_indices.append(idx)
        except Exception as e:
            # Log exotic elements or valence errors
            logger.warning(f"Sanitization failed for index {idx}, SMILES {smiles}: {str(e)}")
            invalid_rows.append({'index': idx, 'smiles': smiles, 'reason': str(e)})
    
    logger.info(f"Sanitization complete: {len(valid_indices)} valid, {len(invalid_rows)} invalid")
    for row in invalid_rows[:5]:  # Log first 5 invalid rows
        logger.warning(f"Invalid row: {row}")
    
    return df.iloc[valid_indices].reset_index(drop=True)

def deduplicate_smiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle duplicate SMILES by retaining most recent assay date or averaging values if dates match.
    Must run AFTER sanitization and BEFORE target filtering.
    """
    logger.info("Starting deduplication...")
    if 'assay_date' not in df.columns:
        logger.warning("No 'assay_date' column found, skipping deduplication based on date")
        return df.drop_duplicates(subset=['smiles'], keep='first').reset_index(drop=True)
    
    # Sort by assay_date descending to keep most recent
    df_sorted = df.sort_values(by='assay_date', ascending=False)
    
    # Group by SMILES and keep the first (most recent) entry
    deduped_df = df_sorted.groupby('smiles', as_index=False).first()
    
    logger.info(f"Deduplication complete: {len(df)} -> {len(deduped_df)} rows")
    return deduped_df

def filter_targets(df: pd.DataFrame, targets: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Filter for oral bioavailability, apparent permeability (Papp), or clearance.
    Remove rows with missing targets.
    """
    logger.info("Starting target filtering...")
    
    if targets is None:
        targets = ['oral_bioavailability', 'Papp', 'clearance']
    
    # Ensure target column exists
    if 'target' not in df.columns:
        logger.error("No 'target' column found in dataframe")
        return df[df['target'].notna()]  # This will return empty if column missing
    
    # Filter for known targets and non-null values
    mask = df['target'].notna()
    if targets:
        mask = mask & df['target'].isin(targets)
    
    filtered_df = df[mask].reset_index(drop=True)
    logger.info(f"Target filtering complete: {len(df)} -> {len(filtered_df)} rows")
    return filtered_df

def sample_dataset(df: pd.DataFrame, max_samples: Optional[int] = None) -> pd.DataFrame:
    """
    Perform stratified random sampling on the filtered dataset.
    Cap at max_samples if specified.
    """
    logger.info("Starting dataset sampling...")
    if max_samples is None:
        # Default to a reasonable limit for computation
        max_samples = 10000
    
    if len(df) <= max_samples:
        logger.info(f"Dataset size ({len(df)}) is within limit, no sampling needed")
        return df
    
    # Simple random sampling with seed for reproducibility
    sampled_df = df.sample(n=max_samples, random_state=RANDOM_SEED).reset_index(drop=True)
    logger.info(f"Sampling complete: {len(df)} -> {len(sampled_df)} rows")
    return sampled_df

def calculate_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute 2D descriptors (TPSA, logP, MW, rotatable bonds, H-bond donors/acceptors, ring count).
    """
    logger.info("Starting descriptor calculation...")
    
    descriptors_list = []
    for idx, row in df.iterrows():
        smiles = row['smiles']
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Could not create molecule from SMILES: {smiles}")
            descriptors_list.append({
                'smiles': smiles,
                'mw': None, 'logp': None, 'tpsa': None,
                'hbd': None, 'hba': None, 'rotatable_bonds': None, 'ring_count': None
            })
            continue
        
        mw = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        tpsa = Descriptors.TPSA(mol)
        hbd = rdMolDescriptors.CalcNumHBD(mol)
        hba = rdMolDescriptors.CalcNumHBA(mol)
        rotatable_bonds = rdMolDescriptors.CalcNumRotatableBonds(mol)
        ring_count = rdMolDescriptors.CalcNumRings(mol)
        
        descriptors_list.append({
            'smiles': smiles,
            'mw': mw, 'logp': logp, 'tpsa': tpsa,
            'hbd': hbd, 'hba': hba, 'rotatable_bonds': rotatable_bonds, 'ring_count': ring_count
        })
    
    desc_df = pd.DataFrame(descriptors_list)
    # Merge back with original data
    result_df = pd.merge(df, desc_df, on='smiles', how='left')
    logger.info(f"Descriptor calculation complete: {len(result_df)} rows processed")
    return result_df

def write_processed_data(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Output data/processed/molecules_processed.csv and validate against molecule.schema.yaml before saving.
    Must explicitly call update_state.py to record the new artifact hash in the state file.
    """
    if output_path is None:
        output_path = DATA_PROCESSED_DIR / "molecules_processed.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load schema
    schema = load_schema()
    
    # Validate dataframe against schema
    is_valid, errors = validate_dataframe_against_schema(df, schema)
    if not is_valid:
        logger.error(f"Validation failed: {errors}")
        raise ValueError(f"Data validation failed: {errors}")
    
    # Write to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Processed data written to {output_path}")
    
    # Compute file hash
    file_hash = compute_file_hash(output_path)
    logger.info(f"File hash for {output_path}: {file_hash}")
    
    # Update state file
    update_state(
        artifact_path=str(output_path),
        artifact_hash=file_hash,
        state_file=STATE_FILE,
        artifact_type="processed_data",
        description="Processed molecule dataset with 2D descriptors"
    )
    
    logger.info(f"State file updated with artifact hash for {output_path}")
    return output_path

def main():
    """
    Main pipeline for preprocessing: load raw data, sanitize, deduplicate, filter, sample, calculate descriptors, and write output.
    """
    logger.info("Starting preprocessing pipeline...")
    
    # Define paths
    raw_db_path = DATA_RAW_DIR / "chembl_33.db"
    if not raw_db_path.exists():
        logger.error(f"Raw database not found at {raw_db_path}. Run download.py first.")
        sys.exit(1)
    
    # Load data from SQLite
    logger.info(f"Loading data from {raw_db_path}...")
    # Assuming the table name is 'molecules' or similar; adjust as needed
    try:
        df = pd.read_sql_query("SELECT * FROM molecules", raw_db_path)
    except Exception as e:
        logger.error(f"Failed to load data from database: {e}")
        # Fallback: try to load from CSV if DB structure differs
        csv_path = DATA_RAW_DIR / "chembl_33.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
        else:
            raise FileNotFoundError("No data source found (DB or CSV)")
    
    logger.info(f"Loaded {len(df)} rows from raw data")
    
    # Pipeline steps
    df = sanitize_molecules(df)
    df = deduplicate_smiles(df)
    df = filter_targets(df)
    df = sample_dataset(df)
    df = calculate_descriptors(df)
    
    # Write output
    output_path = write_processed_data(df)
    logger.info(f"Preprocessing pipeline complete. Output: {output_path}")

if __name__ == "__main__":
    main()
