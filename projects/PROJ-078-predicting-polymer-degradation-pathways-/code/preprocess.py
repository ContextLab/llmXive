import logging
import json
import hashlib
import os
import signal
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors

from utils import get_logger, get_project_paths
from data_models import PolymerRecord, MolecularGraph

# Constants for Imputation (FR-002 Compliance)
DEFAULT_PH = 7.0
DEFAULT_TEMP_C = 25.0
DEFAULT_UV_EXPOSURE = False

# Output paths
PATHS = get_project_paths()
IMPUTED_RECORDS_PATH = PATHS / "data" / "raw" / "imputed_records.csv"
FLAGGED_ENV_DATA_PATH = PATHS / "data" / "raw" / "flagged_env_data.csv"
PROCESSED_GRAPH_DATASET_PATH = PATHS / "data" / "processed" / "processed_graph_dataset.csv"

logger = get_logger(__name__)

def compute_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_augmentation_trigger() -> Dict[str, Any]:
    """Check if augmentation is triggered based on power analysis."""
    trigger_file = PATHS / "state" / "augmentation_trigger.json"
    if trigger_file.exists():
        with open(trigger_file, 'r') as f:
            return json.load(f)
    return {"n": 0, "action": "none"}

def smiles_to_graph(smiles: str) -> Optional[MolecularGraph]:
    """Convert SMILES string to a MolecularGraph object using RDKit."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    # Extract basic graph features
    num_atoms = mol.GetNumAtoms()
    num_bonds = mol.GetNumBonds()
    
    # Simple feature vector: [num_atoms, num_bonds, molecular_weight]
    mw = Descriptors.MolWt(mol)
    
    return MolecularGraph(
        smiles=smiles,
        num_atoms=num_atoms,
        num_bonds=num_bonds,
        molecular_weight=mw,
        # Placeholder for actual graph tensor data
        # In a real implementation, this would include node/edge features
        node_features=None, 
        edge_features=None
    )

def load_processed_polyester_dataset() -> pd.DataFrame:
    """Load the raw polymer records after initial filtering (T014/T016a)."""
    # This function assumes T016a has created raw_polymer_records.csv
    # We need to read from the raw file that has already been cleaned of missing labels
    raw_path = PATHS / "data" / "raw" / "raw_polymer_records.csv"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw polymer records not found at {raw_path}. Run T016a first.")
    
    df = pd.read_csv(raw_path)
    return df

def save_dataset(df: pd.DataFrame, output_path: Path, description: str = ""):
    """Save dataset to CSV and log checksum."""
    df.to_csv(output_path, index=False)
    checksum = compute_checksum(output_path)
    logger.info(f"{description} saved to {output_path} with checksum {checksum}")
    return checksum

def handle_missing_environmental_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    T015d: Implement Imputation Path for FR-002 Compliance.
    
    1. Identify records with missing environmental data (temp, pH, UV).
    2. Create an imputed version of these records with default values.
    3. Save the imputed records to data/raw/imputed_records.csv.
    4. Exclude these records from the returned 'valid' dataframe (to prevent confounding in training).
    5. Also save the IDs of flagged records for audit (T015b compatibility).
    
    Returns:
      Tuple[valid_df, imputed_df, flagged_df]
        - valid_df: Records with complete environmental data (for training).
        - imputed_df: Records with imputed values (artifact for FR-002, excluded from training).
        - flagged_df: IDs of records that had missing data (audit log).
    """
    logger.info("T015d: Handling missing environmental data with imputation path...")
    
    # Columns to check for missing data
    env_cols = ['temperature_c', 'ph', 'uv_exposure']
    
    # Identify rows with any missing environmental data
    missing_mask = df[env_cols].isnull().any(axis=1)
    
    # Split data
    valid_df = df[~missing_mask].copy()
    missing_df = df[missing_mask].copy()
    
    # Create flagged record IDs for audit (T015b)
    flagged_df = missing_df[['id']].copy() if 'id' in missing_df.columns else missing_df[['smiles']].copy()
    
    if len(missing_df) > 0:
        logger.warning(f"Found {len(missing_df)} records with missing environmental data. Imputing values.")
        
        # Impute values
        missing_df['temperature_c'] = DEFAULT_TEMP_C
        missing_df['ph'] = DEFAULT_PH
        missing_df['uv_exposure'] = DEFAULT_UV_EXPOSURE
        
        # Add a column to track that this data was imputed
        missing_df['is_imputed'] = True
        
        # Save imputed records to data/raw/imputed_records.csv
        save_dataset(missing_df, IMPUTED_RECORDS_PATH, "Imputed records (T015d)")
        
        # Save flagged IDs (T015b requirement)
        flagged_output_path = PATHS / "data" / "raw" / "flagged_env_data.csv"
        save_dataset(flagged_df, flagged_output_path, "Flagged environmental data IDs")
        
        logger.info(f"Imputed {len(missing_df)} records saved to {IMPUTED_RECORDS_PATH}")
        logger.info(f"Flagged {len(flagged_df)} record IDs saved to {flagged_output_path}")
    else:
        logger.info("No records with missing environmental data found.")
        # Ensure empty files exist if no data to impute, for consistency
        pd.DataFrame(columns=['id', 'temperature_c', 'ph', 'uv_exposure', 'is_imputed']).to_csv(IMPUTED_RECORDS_PATH, index=False)
        pd.DataFrame(columns=['id']).to_csv(FLAGGED_ENV_DATA_PATH, index=False)

    return valid_df, missing_df, flagged_df

def process_smiles_to_graphs(df: pd.DataFrame) -> List[MolecularGraph]:
    """Convert SMILES strings in dataframe to MolecularGraph objects."""
    graphs = []
    invalid_count = 0
    
    for _, row in df.iterrows():
        smiles = row['smiles']
        graph = smiles_to_graph(smiles)
        if graph:
            graphs.append(graph)
        else:
            invalid_count += 1
            logger.warning(f"Invalid SMILES: {smiles}")
    
    if invalid_count > 0:
        logger.warning(f"Skipped {invalid_count} invalid SMILES strings.")
    
    return graphs

def main():
    """
    Main entry point for T015 and T015d.
    1. Load raw records (T016a output).
    2. Handle missing environmental data (T015d - Imputation).
    3. Convert valid records to graphs (T015).
    4. Save processed dataset.
    """
    logger.info("Starting T015/T015d: Preprocessing and Imputation")
    
    try:
        # Load raw data
        raw_df = load_processed_polyester_dataset()
        logger.info(f"Loaded {len(raw_df)} raw records.")
        
        # T015d: Handle missing environmental data (Imputation path)
        valid_df, imputed_df, flagged_df = handle_missing_environmental_data(raw_df)
        
        # T015: Convert valid records to graphs
        logger.info(f"Converting {len(valid_df)} valid records to graphs...")
        graphs = process_smiles_to_graphs(valid_df)
        
        # Create a DataFrame from graphs for saving
        # Note: In a real implementation, we might convert MolecularGraph objects to a serializable format
        # For now, we'll keep the original valid_df and add graph properties
        processed_df = valid_df.copy()
        processed_df['num_atoms'] = [g.num_atoms for g in graphs]
        processed_df['num_bonds'] = [g.num_bonds for g in graphs]
        processed_df['molecular_weight'] = [g.molecular_weight for g in graphs]
        
        # T016b: Save processed graph dataset
        save_dataset(processed_df, PROCESSED_GRAPH_DATASET_PATH, "Processed graph dataset (T016b)")
        
        # T016c: Save pre-augmentation dataset (same as processed for now)
        pre_aug_path = PATHS / "data" / "processed" / "pre_augmented_graph_dataset.csv"
        save_dataset(processed_df, pre_aug_path, "Pre-augmentation dataset (T016c)")
        
        logger.info("T015/T015d completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during preprocessing: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()