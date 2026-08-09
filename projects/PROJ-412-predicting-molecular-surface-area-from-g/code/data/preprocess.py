import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors, Descriptors
from rdkit import RDLogger

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

# Import project utilities
from code.utils.logging import get_logger, log_excluded_molecules, log_errors
from code.utils.config import get_project_root, get_data_dir
from code.utils.validators import count_atoms

# Constants
CRITICAL_FAILURE_RATE = 0.10  # 10% failure rate threshold
CONFORMER_PARAMS_KEYS = ['numThreads', 'maxAttempts', 'energyMinimizationSteps']

logger = get_logger(__name__)

def generate_conformer_params() -> Dict[str, Any]:
    """Generate and return the RDKit conformer generation parameters."""
    return {
        "numThreads": 0,  # 0 = use all available threads
        "maxAttempts": 500,
        "energyMinimizationSteps": 1000,
        "useRandomCoords": False,
        "enforceChirality": True,
        "useExpTorsionAnglePrefs": True,
        "useBasicKnowledge": True
    }

def calculate_sasa(mol: Chem.Mol) -> float:
    """
    Calculate the Solvent Accessible Surface Area (SASA) for a molecule.
    Returns the area in Angstroms squared.
    """
    # RDKit's SASA calculation requires 3D coordinates
    if mol.GetNumConformers() == 0:
        raise RuntimeError("No conformers available for SASA calculation")
    
    # Use the first conformer
    conf = mol.GetConformer(0)
    
    # Calculate SASA
    # The default probe radius is 1.4 Angstroms (water)
    sasa = rdMolDescriptors.CalcSASA(mol, probeRadius=1.4)
    return float(sasa)

def map_rdkit_exception_to_reason(exception: Exception, smiles: str) -> str:
    """
    Map RDKit exceptions to the specific failure reason codes defined in the spec.
    """
    error_str = str(exception).lower()
    
    # Check for valence issues first (ValueError)
    if isinstance(exception, ValueError):
        if "valence" in error_str or "atom" in error_str:
            return 'INVALID_VALENCE'
        return 'CONFORMER_GENERATION_FAIL'
    
    # Check for RuntimeError (ETKDG or Minimization)
    if isinstance(exception, RuntimeError):
        if "etkdg" in error_str or "embed" in error_str:
            return 'ETKDG_FAIL'
        if "minimize" in error_str or "energy" in error_str:
            return 'MINIMIZATION_FAIL'
        return 'CONFORMER_GENERATION_FAIL'
    
    # Generic RDKitException
    if isinstance(exception, Exception): # RDKitException is often a subclass of RuntimeError in Python bindings
        if "valence" in error_str:
            return 'INVALID_VALENCE'
        if "etkdg" in error_str:
            return 'ETKDG_FAIL'
        if "minimize" in error_str:
            return 'MINIMIZATION_FAIL'
    
    return 'CONFORMER_GENERATION_FAIL'

def process_molecule_3d(smiles: str, row_index: int) -> Tuple[Optional[float], Optional[str], int, Optional[str]]:
    """
    Process a single molecule: generate 3D conformer and calculate SASA.
    
    Returns:
        Tuple of (sasa_value, failure_reason, atom_count, error_message)
        If successful: (sasa_float, None, count, None)
        If failed: (None, reason_code, count, error_msg)
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None, 'INVALID_VALENCE', 0, "Failed to parse SMILES"
    
    # Add hydrogens for accurate 3D generation
    mol_h = Chem.AddHs(mol)
    atom_count = mol_h.GetNumAtoms()
    
    # Generate conformer using ETKDG
    params = generate_conformer_params()
    try:
        # ETKDGv3 is the current standard
        etkdg_params = AllChem.ETKDGv3()
        etkdg_params.numThreads = params['numThreads']
        etkdg_params.maxAttempts = params['maxAttempts']
        etkdg_params.useExpTorsionAnglePrefs = params['useExpTorsionAnglePrefs']
        etkdg_params.useBasicKnowledge = params['useBasicKnowledge']
        etkdg_params.enforceChirality = params['enforceChirality']
        
        success = AllChem.EmbedMolecule(mol_h, etkdg_params)
        if success == -1:
            return None, 'ETKDG_FAIL', atom_count, "ETKDG embedding failed"
    except Exception as e:
        reason = map_rdkit_exception_to_reason(e, smiles)
        return None, reason, atom_count, str(e)
    
    # Minimize energy
    try:
        # MMFF94 force field
        ff = AllChem.MMFFGetMoleculeForceField(mol_h, AllChem.MMFFGetMoleculeProperties(mol_h))
        if ff is None:
            # Fallback to UFF if MMFF fails
            ff = AllChem.UFFGetMoleculeForceField(mol_h)
            if ff is None:
                return None, 'MINIMIZATION_FAIL', atom_count, "Could not create force field"
        
        ff.Minimize(maxIts=params['energyMinimizationSteps'])
    except Exception as e:
        reason = map_rdkit_exception_to_reason(e, smiles)
        return None, reason, atom_count, str(e)
    
    # Calculate SASA
    try:
        sasa = calculate_sasa(mol_h)
        return sasa, None, atom_count, None
    except Exception as e:
        reason = map_rdkit_exception_to_reason(e, smiles)
        return None, reason, atom_count, str(e)

def process_chunk_3d(df_chunk: pd.DataFrame, params: Dict[str, Any]) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Process a chunk of molecules for 3D conformer generation and SASA.
    
    Args:
        df_chunk: DataFrame with SMILES and existing features
        params: Conformer generation parameters
    
    Returns:
        Tuple of (processed_chunk_df, failure_records_list)
    """
    sasa_values = []
    failure_records = []
    successful_count = 0
    total_count = len(df_chunk)
    
    logger.info(f"Processing {total_count} molecules for 3D conformer generation...")
    
    for idx, row in df_chunk.iterrows():
        smiles = row['smiles']
        sasa, failure_reason, atom_count, error_msg = process_molecule_3d(smiles, idx)
        
        if sasa is not None:
            sasa_values.append(sasa)
            successful_count += 1
        else:
            sasa_values.append(np.nan)
            failure_records.append({
                'smiles': smiles,
                'failure_reason': failure_reason,
                'atom_count': atom_count
            })
            logger.warning(f"Conformer generation failed for {smiles}: {failure_reason} ({error_msg})")
    
    # Create the new column
    df_chunk = df_chunk.copy()
    df_chunk['surface_area'] = sasa_values
    
    # Log progress
    success_rate = successful_count / total_count if total_count > 0 else 0
    logger.info(f"Chunk processed: {successful_count}/{total_count} successful ({success_rate:.2%})")
    
    return df_chunk, failure_records

def save_conformer_params(params: Dict[str, Any], output_path: Path) -> str:
    """
    Save conformer parameters to JSON and return the SHA-256 hash of the content.
    """
    # Ensure deterministic JSON output for hashing
    json_content = json.dumps(params, sort_keys=True, indent=2)
    
    with open(output_path, 'w') as f:
        f.write(json_content)
    
    # Calculate hash
    hash_object = hashlib.sha256(json_content.encode('utf-8'))
    return hash_object.hexdigest()

def save_failure_report(failures: List[Dict], output_path: Path):
    """
    Save failure report to CSV atomically.
    """
    if not failures:
        # Create empty file with headers if no failures
        df_fail = pd.DataFrame(columns=['smiles', 'failure_reason', 'atom_count'])
    else:
        df_fail = pd.DataFrame(failures)
        # Ensure column order
        df_fail = df_fail[['smiles', 'failure_reason', 'atom_count']]
    
    df_fail.to_csv(output_path, index=False)
    logger.info(f"Saved failure report to {output_path} with {len(failures)} entries")

def main():
    """
    Main entry point for T015: 3D conformer generation and SASA calculation.
    """
    project_root = get_project_root()
    data_dir = get_data_dir()
    
    # Input/Output paths
    input_path = data_dir / "processed" / "graphs_with_features.parquet"
    output_path = data_dir / "processed" / "paired_dataset.parquet"
    params_path = data_dir / "processed" / "conformer_params.json"
    failure_report_path = data_dir / "processed" / "failure_report.csv"
    log_path = project_root / "logs" / "conformer_failures.log"
    
    # Ensure output directories exist
    (data_dir / "processed").mkdir(parents=True, exist_ok=True)
    (project_root / "logs").mkdir(parents=True, exist_ok=True)
    
    # Setup file handler for failure logs
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    # Check input file
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading input data from {input_path}")
    df = pd.read_parquet(input_path)
    
    # Validate required columns
    required_cols = ['smiles', 'molecular_weight']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Generate and save conformer parameters
    params = generate_conformer_params()
    config_hash = save_conformer_params(params, params_path)
    logger.info(f"Saved conformer parameters to {params_path} with hash {config_hash}")
    
    # Verify parameters
    for key in CONFORMER_PARAMS_KEYS:
        if key not in params:
            logger.error(f"Missing required parameter: {key}")
            raise ValueError(f"Missing required parameter: {key}")
    
    # Process in chunks to manage memory
    chunk_size = 100  # Process 100 molecules at a time
    all_failures = []
    processed_chunks = []
    
    total_rows = len(df)
    logger.info(f"Processing {total_rows} molecules in chunks of {chunk_size}")
    
    for i in range(0, total_rows, chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        processed_chunk, failures = process_chunk_3d(chunk, params)
        processed_chunks.append(processed_chunk)
        all_failures.extend(failures)
        
        # Log progress
        if (i + chunk_size) % 500 == 0 or (i + chunk_size) >= total_rows:
            logger.info(f"Progress: {min(i+chunk_size, total_rows)}/{total_rows} processed")
    
    # Concatenate all chunks
    df_final = pd.concat(processed_chunks, ignore_index=True)
    
    # Add conformer config hash as a column
    df_final['conformer_config_hash'] = config_hash
    
    # Check failure rate
    total_processed = len(df_final)
    failure_count = len(all_failures)
    failure_rate = failure_count / total_processed if total_processed > 0 else 0
    
    logger.info(f"Total processing complete: {total_processed} molecules, {failure_count} failures ({failure_rate:.2%})")
    
    # Save failure report BEFORE any potential halt
    save_failure_report(all_failures, failure_report_path)
    
    # Halt if failure rate is too high
    if failure_rate > CRITICAL_FAILURE_RATE:
        logger.critical(f"Critical failure rate detected: {failure_rate:.2%} > {CRITICAL_FAILURE_RATE:.2%}")
        logger.critical(f"Failure report saved to {failure_report_path}")
        raise RuntimeError(f"Conformer generation failure rate {failure_rate:.2%} exceeds threshold {CRITICAL_FAILURE_RATE:.2%}")
    
    # Verify SASA column
    if 'surface_area' not in df_final.columns:
        logger.error("Surface area column missing from output")
        raise ValueError("Surface area column missing from output")
    
    nan_count = df_final['surface_area'].isna().sum()
    if nan_count > 0:
        logger.warning(f"Found {nan_count} NaN values in surface_area column")
        # Remove rows with NaN surface area if they exist (should be handled by failure logic)
        # But we keep them for now as per the failure report logic
    
    # Save final dataset
    df_final.to_parquet(output_path, index=False)
    logger.info(f"Saved final paired dataset to {output_path}")
    
    # Log dataset statistics
    logger.info(f"Dataset statistics:")
    logger.info(f"  Total molecules: {len(df_final)}")
    logger.info(f"  Mean surface area: {df_final['surface_area'].mean():.2f} Å²")
    logger.info(f"  Std surface area: {df_final['surface_area'].std():.2f} Å²")
    logger.info(f"  Min surface area: {df_final['surface_area'].min():.2f} Å²")
    logger.info(f"  Max surface area: {df_final['surface_area'].max():.2f} Å²")
    
    # Verify outputs
    assert params_path.exists(), "Conformer params file not created"
    assert failure_report_path.exists(), "Failure report file not created"
    assert output_path.exists(), "Output parquet file not created"
    
    # Verify params content
    with open(params_path, 'r') as f:
        saved_params = json.load(f)
        for key in CONFORMER_PARAMS_KEYS:
            assert key in saved_params, f"Parameter {key} missing from saved params"
    
    # Verify output columns
    df_check = pd.read_parquet(output_path)
    assert 'surface_area' in df_check.columns, "Surface area column missing from output"
    assert 'conformer_config_hash' in df_check.columns, "Conformer config hash column missing from output"
    
    logger.info("Task T015 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())