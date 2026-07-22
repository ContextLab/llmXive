"""
Fingerprint generation module using Open Babel (obabel) command-line tool.

This module generates MACCS, ECFP4, and FP2 fingerprints for molecular datasets
by invoking the `obabel` CLI via subprocess. It strictly adheres to the
requirement of failing loudly if the process exceeds runtime constraints.
"""

import os
import sys
import subprocess
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Generator

import pandas as pd
import numpy as np

# Import local utilities
from utils.config import enforce_obabel_subprocess_timeout, MAX_DEPTH
from logging_utils import setup_logger

# Configure logger
logger = setup_logger("fingerprints")

# Constants
FINGERPRINT_TYPES = ["ECFP4", "MACCS", "FP2"]
OUTPUT_COLUMNS = ["smiles", "fingerprint_type", "bits"]
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
DERIVED_DIR = DATA_DIR / "derived"

def ensure_dirs():
    """Ensure output directories exist."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

def check_obabel_available() -> bool:
    """
    Check if the 'obabel' command-line tool is available in the system PATH.
    Returns True if available, False otherwise.
    """
    try:
        # Run a simple version check
        result = subprocess.run(
            ["obabel", "-V"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        if result.returncode == 0:
            logger.info("Open Babel (obabel) is available.")
            return True
        else:
            logger.error("Open Babel returned a non-zero exit code during version check.")
            return False
    except FileNotFoundError:
        logger.error("Open Babel (obabel) not found in PATH. Please install it.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Open Babel version check timed out.")
        return False

def smiles_to_obabel_fingerprint(smiles: str, fp_type: str) -> Optional[str]:
    """
    Generate a specific fingerprint for a single SMILES string using obabel.

    Args:
        smiles: The SMILES string of the molecule.
        fp_type: The fingerprint type (ECFP4, MACCS, FP2).

    Returns:
        A hexadecimal string of the fingerprint bits, or None if generation fails.
    """
    if not smiles or not isinstance(smiles, str):
        logger.warning(f"Invalid SMILES provided: {smiles}")
        return None

    # Map internal types to obabel flags
    # ECFP4 -> -x 4 (or -x ecfp4 in some versions, but -x 4 is standard for ECFP4)
    # MACCS -> -x m (or -x maccs)
    # FP2   -> -x 2 (or -x fp2)
    # Note: Open Babel's -x flag is for fingerprints.
    # -x 4 is ECFP4 (radius 2, diameter 4)
    # -x m is MACCS keys
    # -x 2 is FP2 (path based)
    
    # Standard mapping for 'obabel' CLI
    fp_map = {
        "ECFP4": "4",
        "MACCS": "m",
        "FP2": "2"
    }

    if fp_type not in fp_map:
        logger.error(f"Unsupported fingerprint type: {fp_type}")
        return None

    obabel_flag = fp_map[fp_type]
    
    # Construct command: obabel -:"<smiles>" -xf <flag> -ohex
    # -:"..." reads from string
    # -xf <flag> specifies the fingerprint type
    # -ohex outputs in hexadecimal format
    cmd = ["obabel", f"-:{smiles}", "-xf", obabel_flag, "-ohex"]

    try:
        # Use the configured timeout from config.py
        timeout_seconds = enforce_obabel_subprocess_timeout()
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            text=True
        )

        if result.returncode != 0:
            # Log the error but return None to allow batch processing to continue
            logger.warning(f"obabel failed for SMILES {smiles[:20]}... ({fp_type}): {result.stderr.strip()}")
            return None

        # Output is usually one line with the hex string
        output = result.stdout.strip()
        if not output:
            logger.warning(f"Empty output for SMILES {smiles[:20]}... ({fp_type})")
            return None

        return output

    except subprocess.TimeoutExpired:
        # CRITICAL: If timeout occurs, we must fail loudly as per task requirements
        # However, for a batch process, we might want to raise an exception immediately
        # to stop the whole run, as partial fingerprints are invalid.
        logger.critical(f"obabel process timed out for SMILES {smiles[:20]}... ({fp_type}). "
                        f"Raising exception to fail the pipeline.")
        raise TimeoutError(f"Open Babel process timed out after {timeout_seconds}s for SMILES: {smiles}")
    
    except Exception as e:
        logger.error(f"Unexpected error running obabel for {smiles[:20]}...: {e}")
        return None

def generate_fingerprints_batch(smiles_list: List[str], fp_types: List[str]) -> Generator[Dict[str, Any], None, None]:
    """
    Generate fingerprints for a batch of SMILES strings.
    Yields dictionaries with 'smiles', 'fingerprint_type', and 'bits'.
    
    Args:
        smiles_list: List of SMILES strings.
        fp_types: List of fingerprint types to generate.
    
    Yields:
        Dict containing the result for each molecule/fingerprint pair.
    """
    for smiles in smiles_list:
        for fp_type in fp_types:
            bits = smiles_to_obabel_fingerprint(smiles, fp_type)
            yield {
                "smiles": smiles,
                "fingerprint_type": fp_type,
                "bits": bits
            }

def process_dataset(input_path: Path, output_path: Path):
    """
    Process a dataset from a CSV file, generating fingerprints for all molecules,
    and saving the results to a Parquet file.
    
    Args:
        input_path: Path to the input CSV (train_set.csv).
        output_path: Path to the output Parquet file.
    """
    if not check_obabel_available():
        raise RuntimeError("Open Babel (obabel) is not available. Cannot proceed.")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading dataset from {input_path}...")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load input CSV: {e}")

    required_cols = ["smiles"]
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Input CSV must contain columns: {required_cols}")

    logger.info(f"Dataset loaded: {len(df)} molecules. Generating fingerprints...")
    
    # Prepare data collection
    results = []
    total_molecules = len(df)
    
    # Start timer for batch monitoring
    start_time = time.time()
    
    # Iterate and generate
    # We collect results in a list and then convert to DataFrame to avoid memory fragmentation
    # However, for very large datasets, a generator to parquet might be better.
    # Given the constraint of ~5000 molecules, list accumulation is fine.
    
    for idx, row in df.iterrows():
        smiles = row["smiles"]
        if not isinstance(smiles, str) or not smiles:
            logger.warning(f"Skipping invalid SMILES at index {idx}")
            continue

        for fp_type in FINGERPRINT_TYPES:
            try:
                bits = smiles_to_obabel_fingerprint(smiles, fp_type)
                if bits is not None:
                    results.append({
                        "smiles": smiles,
                        "fingerprint_type": fp_type,
                        "bits": bits
                    })
                else:
                    # Log but don't crash for individual failures, 
                    # though the task says fail loudly if time exceeded.
                    # Individual failures (e.g. invalid SMILES) are handled by returning None.
                    pass
            except TimeoutError:
                # This is a critical failure for the whole run
                raise

        # Progress logging
        if (idx + 1) % 100 == 0:
            elapsed = time.time() - start_time
            logger.info(f"Processed {idx + 1}/{total_molecules} molecules. Elapsed: {elapsed:.1f}s")

    if not results:
        raise RuntimeError("No fingerprints were generated. Check input data and obabel installation.")

    logger.info(f"Conversion complete. Total records: {len(results)}")
    
    # Create DataFrame
    fp_df = pd.DataFrame(results)
    
    # Save to Parquet
    logger.info(f"Saving fingerprints to {output_path}...")
    ensure_dirs()
    fp_df.to_parquet(output_path, index=False)
    logger.info(f"Successfully saved {len(fp_df)} fingerprint records to {output_path}")

def main():
    """Main entry point for fingerprint generation."""
    # Define paths based on project structure
    # Input: data/derived/train_set.csv (from T011.5)
    # Output: data/processed/fingerprints.parquet
    input_file = DATA_DIR / "derived" / "train_set.csv"
    output_file = PROCESSED_DIR / "fingerprints.parquet"

    # Check if input exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}. "
                     f"Please ensure T011.5 (Train/Test Split) has been completed.")
        sys.exit(1)

    try:
        process_dataset(input_file, output_file)
        logger.info("Fingerprint generation completed successfully.")
    except TimeoutError as e:
        logger.critical(f"CRITICAL: Fingerprint generation failed due to timeout: {e}")
        logger.critical("Pipeline must be aborted to prevent partial data artifacts.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"CRITICAL: Fingerprint generation failed unexpectedly: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()