import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors, rdDistGeom
from rdkit import RDLogger

# Project-relative imports based on provided API surface
from utils.logging import get_logger, log_errors, log_excluded_molecules
from utils.seed import set_seed, get_seed_from_env
from utils.config import get_project_root, get_data_dir

# Disable RDKit warnings to keep logs clean, we handle errors explicitly
RDLogger.DisableLog('rdApp.*')

logger = get_logger(__name__)

# Constants for failure reasons (Enum-like strings as per spec)
FAILURE_ETKDG = 'ETKDG_FAIL'
FAILURE_MINIMIZATION = 'MINIMIZATION_FAIL'
FAILURE_INVALID_VALENCE = 'INVALID_VALENCE'
FAILURE_CONFORMER_GEN = 'CONFORMER_GENERATION_FAIL'

# Default ETKDG parameters (will be overridden by config or env)
DEFAULT_ETKDG_PARAMS = {
    'numThreads': 0,
    'maxAttempts': 200,
    'energyMinimizationSteps': 100,
    'random_seed': 42
}

def generate_conformer_config(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generates the configuration for ETKDG conformer generation.
    Merges defaults with provided params.
    """
    config = DEFAULT_ETKDG_PARAMS.copy()
    if params:
        config.update(params)
    # Ensure random_seed is set explicitly for reproducibility
    if 'random_seed' not in config:
        config['random_seed'] = get_seed_from_env()
    return config

def map_rdkit_exception_to_reason(exception: Exception) -> str:
    """
    Maps RDKit exceptions to the specific failure reason codes required by the spec.
    """
    exc_type = type(exception).__name__
    exc_msg = str(exception).lower()

    # Check for valence issues first (ValueError often raised by RDKit on invalid valence)
    if exc_type == 'ValueError' or 'valence' in exc_msg:
        return FAILURE_INVALID_VALENCE

    # Check for generic RDKit exceptions
    if exc_type == 'RDKitException' or 'rdkit' in exc_msg:
        # Distinguish between ETKDG specific and generic if possible, else generic
        if 'etkdg' in exc_msg or 'distance geometry' in exc_msg:
            return FAILURE_ETKDG
        return FAILURE_CONFORMER_GEN

    # Check for RuntimeErrors (often minimization or ETKDG failures)
    if exc_type == 'RuntimeError':
        if 'minimization' in exc_msg or 'energy' in exc_msg:
            return FAILURE_MINIMIZATION
        if 'etkdg' in exc_msg or 'distance geometry' in exc_msg:
            return FAILURE_ETKDG
        return FAILURE_CONFORMER_GEN

    # Default fallback
    return FAILURE_CONFORMER_GEN

def generate_3d_conformer(mol: Chem.Mol, config: Dict[str, Any]) -> Tuple[Optional[Chem.Mol], str]:
    """
    Attempts to generate a 3D conformer for a molecule using ETKDG.
    Returns (modified_mol, error_reason). If successful, error_reason is None.
    """
    # Clone the molecule to avoid modifying the input if generation fails
    mol_copy = Chem.Mol(mol)

    # Check for valid valence before attempting generation (explicit check)
    try:
        Chem.SanitizeMol(mol_copy)
    except ValueError as e:
        return None, map_rdkit_exception_to_reason(e)

    # Prepare ETKDG parameters
    params = rdDistGeom.ETKDGv3()
    params.numThreads = config['numThreads']
    params.maxAttempts = config['maxAttempts']
    # Note: ETKDGv3 params don't directly expose 'energyMinimizationSteps' in the same way,
    # but we can set the max iterations for the minimizer if accessible or rely on defaults.
    # For v3, minimization is often handled internally or via a separate call.
    # We will attempt to set it if the attribute exists, otherwise ignore.
    if hasattr(params, 'maxIters'):
        params.maxIters = config['energyMinimizationSteps']
    
    # Set the random seed
    params.randomSeed = config['random_seed']

    try:
        # Generate conformer
        conformer_id = rdDistGeom.EmbedMolecule(mol_copy, params)
        
        if conformer_id == -1:
            return None, FAILURE_ETKDG

        # Perform energy minimization (MMFF94)
        # First, check if MMFF can be applied
        mmff_props = AllChem.MMFFGetMoleculeProperties(mol_copy)
        if mmff_props is None:
            # If MMFF fails, we might still have a valid conformer, but minimization failed
            # Depending on strictness, this could be a failure. Spec says MINIMIZATION_FAIL.
            # However, if we can't minimize, we can't guarantee energy min.
            # Let's try UFF if MMFF fails.
            uff_props = AllChem.UFFGetMoleculeForceField(mol_copy)
            if uff_props is None:
                return None, FAILURE_MINIMIZATION
            
            status = uff_props.Minimize(maxIts=config['energyMinimizationSteps'])
            if status != 0:
                return None, FAILURE_MINIMIZATION
        else:
            ff = AllChem.MMFFGetMoleculeForceField(mol_copy, mmff_props)
            if ff is None:
                return None, FAILURE_MINIMIZATION
            
            status = ff.Minimize(maxIts=config['energyMinimizationSteps'])
            if status != 0:
                return None, FAILURE_MINIMIZATION

        return mol_copy, None

    except Exception as e:
        reason = map_rdkit_exception_to_reason(e)
        return None, reason

def process_molecule_3d(row: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes a single molecule row to generate 3D conformer.
    Returns updated row or failure record.
    """
    smiles = row['smiles']
    mol = row['mol'] # Assuming mol object is passed or reconstructed
    
    if mol is None:
        return {'smiles': smiles, 'failure_reason': FAILURE_INVALID_VALENCE, 'atom_count': 0, 'conformer': None}

    atom_count = mol.GetNumAtoms()
    result_mol, error_reason = generate_3d_conformer(mol, config)

    if error_reason:
        return {
            'smiles': smiles,
            'failure_reason': error_reason,
            'atom_count': atom_count,
            'conformer': None
        }
    
    # Serialize conformer coordinates if successful
    # We store the conformer object or its coordinates. 
    # Parquet doesn't support RDKit objects directly, so we serialize to a string or store coordinates.
    # For this implementation, we will store the conformer object in a temporary list or 
    # convert to a serialized string representation (e.g., JSON of coords) for the parquet.
    # Given the task says "containing SMILES and the generated conformer objects (or serialized coordinates)",
    # we will serialize coordinates to a string "x,y,z;x,y,z..." for storage.
    conf = result_mol.GetConformer()
    coords = conf.GetPositions()
    coords_str = ";".join([",".join(map(str, pt)) for pt in coords])
    
    return {
        'smiles': smiles,
        'failure_reason': None,
        'atom_count': atom_count,
        'conformer_coords': coords_str
    }

def process_chunk_3d(df_chunk: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Processes a chunk of molecules for 3D conformer generation.
    Returns (successful_df, failure_records).
    """
    successful_records = []
    failure_records = []
    
    # Ensure we have a 'mol' column or reconstruct it
    # T014 should have passed a mol object or we need to parse SMILES again.
    # Assuming T014 output has 'mol' column as per data model.
    if 'mol' not in df_chunk.columns:
        # Fallback: reconstruct from SMILES if missing
        logger.warning("Column 'mol' not found in chunk. Reconstructing from SMILES.")
        df_chunk['mol'] = df_chunk['smiles'].apply(lambda s: Chem.MolFromSmiles(s))

    for idx, row in df_chunk.iterrows():
        res = process_molecule_3d(row, config)
        if res['failure_reason']:
            failure_records.append(res)
        else:
            successful_records.append(res)
    
    success_df = pd.DataFrame(successful_records)
    return success_df, failure_records

def save_conformer_params(config: Dict[str, Any], output_path: Path):
    """
    Saves the conformer generation parameters to a JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Saved conformer parameters to {output_path}")

def save_failure_report(failures: List[Dict], output_path: Path):
    """
    Saves the failure report to a CSV file.
    """
    if not failures:
        # Create empty file with headers if no failures
        df = pd.DataFrame(columns=['smiles', 'failure_reason', 'atom_count'])
        df.to_csv(output_path, index=False)
    else:
        df = pd.DataFrame(failures)
        df = df[['smiles', 'failure_reason', 'atom_count']] # Ensure column order
        df.to_csv(output_path, index=False)
    logger.info(f"Saved failure report to {output_path}")

def main():
    """
    Main entry point for T015a: 3D conformer generation.
    """
    project_root = get_project_root()
    data_dir = get_data_dir()
    processed_dir = data_dir / "processed"
    logs_dir = project_root / "logs"
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging for conformer failures
    conformer_log_path = logs_dir / "conformer_failures.log"
    fh = logging.FileHandler(conformer_log_path)
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)

    # Load input data from T014
    input_path = processed_dir / "graphs_with_features.parquet"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Please run T014 first.")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}")
    df = pd.read_parquet(input_path)
    
    # Validate input
    required_cols = ['smiles', 'mol'] # T014 should have 'mol'
    if not all(col in df.columns for col in required_cols):
        # If 'mol' is not present, try to parse from SMILES
        if 'mol' not in df.columns:
            logger.warning("'mol' column missing. Parsing SMILES...")
            df['mol'] = df['smiles'].apply(Chem.MolFromSmiles)
            if df['mol'].isna().any():
                logger.warning("Some SMILES failed to parse. Dropping them.")
                df = df.dropna(subset=['mol'])

    # Generate config
    config = generate_conformer_config()
    config_path = processed_dir / "conformer_params.json"
    save_conformer_params(config, config_path)

    logger.info(f"Starting 3D conformer generation with seed {config['random_seed']}")
    
    all_failures = []
    successful_dfs = []
    
    # Process in chunks to manage memory (though Parquet is loaded, we process row-wise)
    # For large datasets, we might want to iterate without loading all if memory is tight.
    # But for T015a, we assume T014 produced a manageable chunk or we process the whole thing.
    # To be safe with memory, we can iterate.
    
    total_count = len(df)
    chunk_size = 1000
    
    for i in range(0, total_count, chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        logger.info(f"Processing chunk {i//chunk_size + 1} ({len(chunk)} molecules)")
        
        success_df, failures = process_chunk_3d(chunk, config)
        successful_dfs.append(success_df)
        all_failures.extend(failures)
        
        # Check failure rate periodically
        current_total = i + len(chunk)
        current_fail_rate = len(all_failures) / current_total if current_total > 0 else 0
        
        if current_fail_rate > 0.10:
            logger.critical(f"Failure rate {current_fail_rate:.2%} exceeds 10% threshold. Halting.")
            # Save failure report before halting
            failure_report_path = processed_dir / "failure_report.csv"
            save_failure_report(all_failures, failure_report_path)
            raise RuntimeError(f"Critical: Conformer generation failure rate ({current_fail_rate:.2%}) exceeds 10% threshold.")

    # Final check
    total_processed = len(df)
    total_failures = len(all_failures)
    final_fail_rate = total_failures / total_processed if total_processed > 0 else 0

    if final_fail_rate > 0.10:
        logger.critical(f"Final failure rate {final_fail_rate:.2%} exceeds 10% threshold.")
        failure_report_path = processed_dir / "failure_report.csv"
        save_failure_report(all_failures, failure_report_path)
        raise RuntimeError(f"Critical: Conformer generation failure rate ({final_fail_rate:.2%}) exceeds 10% threshold.")

    # Combine successful records
    if successful_dfs:
        final_df = pd.concat(successful_dfs, ignore_index=True)
    else:
        final_df = pd.DataFrame(columns=['smiles', 'failure_reason', 'atom_count', 'conformer_coords'])

    # Save output
    output_path = processed_dir / "conformers.parquet"
    # Convert conformer_coords to a format suitable for parquet (it's already string)
    final_df.to_parquet(output_path, index=False)
    
    logger.info(f"Successfully generated {len(final_df)} conformers. Output saved to {output_path}")
    
    # Save failure report even if empty (for audit)
    failure_report_path = processed_dir / "failure_report.csv"
    save_failure_report(all_failures, failure_report_path)

    logger.info("T015a completed successfully.")

if __name__ == "__main__":
    main()
