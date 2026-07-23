"""
Module to generate Open Babel fingerprints (MACCS, ECFP4, FP2) for molecular datasets.
Uses the `obabel` command-line tool via subprocess as per FR-003.
"""

import os
import sys
import subprocess
import logging
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

import pandas as pd
import numpy as np

# Import project utilities
from utils.config import check_obabel_timeout, enforce_obabel_subprocess_timeout, get_joblib_parallel_backend
from seed_manager import set_global_seed

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# Constants
FINGERPRINT_TYPES = ['MACCS', 'ECFP4', 'FP2']
DEFAULT_TIMEOUT_PER_MOLECULE = 30  # seconds
MAX_TOTAL_RUNTIME_HOURS = 6
TARGET_MOLECULES = 5000

def ensure_dirs():
    """Ensure output directories exist."""
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/derived").mkdir(parents=True, exist_ok=True)

def check_obabel_available() -> bool:
    """Check if obabel command is available in the system PATH."""
    try:
        result = subprocess.run(['obabel', '-h'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

def smiles_to_obabel_fingerprint(smiles: str, fp_type: str, timeout: int = DEFAULT_TIMEOUT_PER_MOLECULE) -> Optional[str]:
    """
    Generate a specific fingerprint type for a SMILES string using obabel.

    Args:
        smiles: The SMILES string of the molecule.
        fp_type: The fingerprint type ('MACCS', 'ECFP4', 'FP2').
        timeout: Timeout in seconds for the subprocess.

    Returns:
        Hex string of the fingerprint or None if generation fails.
    """
    if not check_obabel_available():
        logger.error("obabel command not found. Please install Open Babel.")
        return None

    # Map fingerprint types to obabel flags
    fp_flags = {
        'MACCS': '-xk',  # MACCS keys
        'ECFP4': '-xf ECFP4', # ECFP4 (often -xf ECFP4 or -xg depending on version, using standard ECFP4)
        'FP2': '-xf FP2' # FP2
    }

    if fp_type not in fp_flags:
        logger.warning(f"Unknown fingerprint type: {fp_type}. Skipping.")
        return None

    flag = fp_flags[fp_type]
    
    # Construct command: obabel -:"<smiles>" -xf <type> -O -
    # Note: -O - outputs to stdout. We capture stdout.
    cmd = ['obabel', '-:', smiles, flag, '-O', '-']
    
    try:
        # Enforce timeout per molecule
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            text=True
        )
        
        if process.returncode != 0:
            # Log error but return None to allow graceful degradation
            logger.debug(f"obabel failed for SMILES {smiles[:20]}... (truncated): {process.stderr.strip()}")
            return None
        
        output = process.stdout.strip()
        if not output:
            return None
        
        return output

    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout generating {fp_type} for {smiles[:20]}...")
        return None
    except Exception as e:
        logger.error(f"Error generating {fp_type} for {smiles[:20]}...: {e}")
        return None

def generate_fingerprints_batch(
    smiles_list: List[str], 
    fp_types: List[str] = FINGERPRINT_TYPES,
    timeout: int = DEFAULT_TIMEOUT_PER_MOLECULE
) -> List[Dict[str, Any]]:
    """
    Generate fingerprints for a batch of SMILES strings.

    Args:
        smiles_list: List of SMILES strings.
        fp_types: List of fingerprint types to generate.
        timeout: Timeout per molecule.

    Returns:
        List of dictionaries containing SMILES and fingerprint strings.
    """
    results = []
    for smiles in smiles_list:
        if not smiles or not isinstance(smiles, str):
            continue
        
        row = {'smiles': smiles}
        for fp_type in fp_types:
            fp_str = smiles_to_obabel_fingerprint(smiles, fp_type, timeout)
            row[fp_type.lower()] = fp_str
        results.append(row)
    return results

def process_dataset(
    input_path: str,
    output_path: str,
    smiles_column: str = 'smiles',
    fp_types: List[str] = FINGERPRINT_TYPES,
    timeout: int = DEFAULT_TIMEOUT_PER_MOLECULE,
    max_molecules: int = TARGET_MOLECULES
):
    """
    Process a dataset CSV, generating fingerprints for each molecule.
    Implements graceful reduction if time constraints are approached.

    Args:
        input_path: Path to input CSV with SMILES.
        output_path: Path to output Parquet file.
        smiles_column: Name of the SMILES column.
        fp_types: List of fingerprint types.
        timeout: Timeout per molecule.
        max_molecules: Maximum number of molecules to process (for safety).
    """
    if not check_obabel_available():
        raise RuntimeError("Open Babel (obabel) is not available. Cannot generate fingerprints.")

    ensure_dirs()
    
    logger.info(f"Loading dataset from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        logger.error(f"Input file {input_path} not found.")
        raise

    if smiles_column not in df.columns:
        logger.error(f"Column '{smiles_column}' not found in {input_path}. Available: {df.columns.tolist()}")
        raise ValueError(f"Column '{smiles_column}' not found.")

    # Limit dataset size if necessary (graceful reduction)
    if len(df) > max_molecules:
        logger.warning(f"Dataset has {len(df)} molecules. Reducing to {max_molecules} to meet time constraints.")
        df = df.head(max_molecules)

    logger.info(f"Processing {len(df)} molecules for fingerprints: {fp_types}")
    
    start_time = time.time()
    results = []
    successful = 0
    failed = 0

    # Process in batches or individually. For robustness with subprocess, individual is safer for timeout handling.
    # To speed up, we could parallelize, but obabel subprocess overhead might negate benefits on small runners.
    # We will process sequentially to ensure timeout logic is precise per molecule.
    
    for idx, row in df.iterrows():
        smiles = row[smiles_column]
        if pd.isna(smiles):
            failed += 1
            continue

        # Check global time limit
        elapsed = time.time() - start_time
        if elapsed > (MAX_TOTAL_RUNTIME_HOURS * 3600):
            logger.critical(f"Reached maximum runtime limit ({MAX_TOTAL_RUNTIME_HOURS}h). Stopping generation.")
            break

        res = smiles_to_obabel_fingerprint(str(smiles), 'MACCS', timeout) # Just checking one to see if we can proceed? 
        # Actually we need all types. Let's generate all.
        
        row_data = {'smiles': smiles}
        all_ok = True
        for fp_type in fp_types:
            fp_val = smiles_to_obabel_fingerprint(str(smiles), fp_type, timeout)
            row_data[fp_type.lower()] = fp_val
            if fp_val is None:
                all_ok = False
        
        results.append(row_data)
        if all_ok:
            successful += 1
        else:
            failed += 1

        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{len(df)}. Success: {successful}, Failed: {failed}")

    final_df = pd.DataFrame(results)
    
    # Save to Parquet
    final_df.to_parquet(output_path, index=False)
    total_time = time.time() - start_time
    logger.info(f"Fingerprint generation complete. Saved to {output_path}. Total time: {total_time:.2f}s")
    logger.info(f"Success: {successful}, Failed: {failed}")

def main():
    """Main entry point for fingerprint generation."""
    set_global_seed(42)
    
    # Input/Output paths as per task requirements
    input_file = "data/derived/train_set.csv"
    output_file = "data/processed/train_fingerprints.parquet"
    
    if not os.path.exists(input_file):
        logger.error(f"Input file {input_file} not found. Please ensure T011.5 (Split) is complete.")
        sys.exit(1)

    try:
        process_dataset(
            input_path=input_file,
            output_path=output_file,
            smiles_column='smiles',
            fp_types=['MACCS', 'ECFP4', 'FP2'],
            timeout=30,
            max_molecules=5000
        )
    except Exception as e:
        logger.error(f"Fatal error in fingerprint generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()