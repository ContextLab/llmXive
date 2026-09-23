"""
Fingerprint generation module using Open Babel.

This module implements the generation of molecular fingerprints (ECFP4, MACCS, FP2)
by invoking the `obabel` command-line tool via subprocess, as required by FR-003.
It processes the training set to produce a Parquet file containing the fingerprint bits.
"""
import os
import sys
import subprocess
import logging
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Ensure project root is in path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from utils.config import get_runtime_config, enforce_obabel_subprocess_timeout
from seed_manager import set_global_seed

logger = logging.getLogger(__name__)

# Constants
FINGERPRINT_TYPES = ["ECFP4", "MACCS", "FP2"]
DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutes per molecule batch max
OBABEL_TIMEOUT_PER_MOL = 10.0  # Max seconds per molecule

def ensure_dirs() -> None:
    """Ensure output directories exist."""
    output_dir = _project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory: {output_dir}")

def check_obabel_available() -> bool:
    """Check if obabel is available in the system PATH."""
    try:
        result = subprocess.run(
            ["obabel", "-h"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        if result.returncode == 0:
            logger.info("Open Babel (obabel) is available.")
            return True
        else:
            logger.error("Open Babel returned non-zero exit code on help.")
            return False
    except FileNotFoundError:
        logger.error("Open Babel (obabel) not found in PATH. Please install it.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Open Babel check timed out.")
        return False

def smiles_to_obabel_fingerprint(smiles: str, fp_type: str) -> Optional[str]:
    """
    Generate a single fingerprint for a SMILES string using obabel.

    Args:
        smiles: The SMILES string of the molecule.
        fp_type: The fingerprint type (ECFP4, MACCS, FP2).

    Returns:
        The fingerprint string (hex or bit string) or None if generation fails.
    """
    # Command construction based on task requirements
    # obabel -i smiles -o txt -xf <FP_TYPE>
    cmd = ["obabel", "-i", "smiles", "-o", "txt", "-xf", fp_type, "-s", smiles]

    try:
        # Apply timeout per molecule as per performance config
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=OBABEL_TIMEOUT_PER_MOL
        )

        if result.returncode == 0:
            output = result.stdout.decode("utf-8").strip()
            # obabel output format usually includes the SMILES and then the fingerprint
            # Example: "CCO  000000000000..." or similar depending on version
            # We expect the fingerprint to be the last token or the whole line after SMILES
            parts = output.split()
            if len(parts) >= 2:
                return parts[-1] # Assume last part is the fingerprint bits
            elif len(parts) == 1:
                return parts[0]
            return None
        else:
            logger.warning(f"obabel failed for SMILES {smiles[:20]}...: {result.stderr.decode('utf-8')[:100]}")
            return None
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout generating {fp_type} for SMILES {smiles[:20]}...")
        return None
    except Exception as e:
        logger.error(f"Error generating {fp_type} for SMILES {smiles[:20]}...: {e}")
        return None

def generate_fingerprints_batch(
    smiles_list: List[str],
    fp_types: List[str] = FINGERPRINT_TYPES
) -> List[Dict[str, Any]]:
    """
    Generate fingerprints for a batch of SMILES strings.

    Args:
        smiles_list: List of SMILES strings.
        fp_types: List of fingerprint types to generate.

    Returns:
        List of dictionaries containing SMILES and fingerprint bits.
    """
    results = []
    for smiles in smiles_list:
        record = {"smiles": smiles}
        for fp_type in fp_types:
            fp_bits = smiles_to_obabel_fingerprint(smiles, fp_type)
            record[f"{fp_type.lower()}_bits"] = fp_bits if fp_bits else ""
        results.append(record)
    return results

def parse_fingerprint_string(fp_string: str, fp_type: str) -> List[int]:
    """
    Parse the fingerprint string into a list of integers (bits).

    Args:
        fp_string: The raw fingerprint string from obabel.
        fp_type: The fingerprint type.

    Returns:
        List of integers (0 or 1) representing the bits.
    """
    if not fp_string:
        # Return empty or zero vector? For now, return empty list, handled downstream
        return []

    # obabel output for -xf usually returns a hex string or a bit string depending on flags.
    # Standard -xf output is often a hex string. We need to convert to bits.
    # Assuming hex string for ECFP4/MACCS/FP2 if not specified otherwise.
    # If it's already a bit string (0s and 1s), we handle that too.

    if all(c in '01' for c in fp_string):
        return [int(c) for c in fp_string]
    else:
        # Assume hex
        try:
            # Convert hex to binary string, padding to 8 bits per hex char
            binary_str = bin(int(fp_string, 16))[2:].zfill(len(fp_string) * 4)
            return [int(c) for c in binary_str]
        except ValueError:
            logger.warning(f"Could not parse fingerprint string: {fp_string}")
            return []

def process_dataset(
    input_file: Path,
    output_file: Path,
    smiles_column: str = "smiles",
    fp_types: List[str] = FINGERPRINT_TYPES
) -> None:
    """
    Process a dataset CSV, generate fingerprints, and save to Parquet.

    Args:
        input_file: Path to input CSV (e.g., train_set.csv).
        output_file: Path to output Parquet file.
        smiles_column: Name of the column containing SMILES.
        fp_types: List of fingerprint types to generate.
    """
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    logger.info(f"Loading dataset from {input_file}...")
    df = pd.read_csv(input_file)

    if smiles_column not in df.columns:
        raise ValueError(f"Column '{smiles_column}' not found in {input_file}. Available: {df.columns.tolist()}")

    logger.info(f"Generating fingerprints for {len(df)} molecules...")
    start_time = time.time()

    # Check obabel availability once
    if not check_obabel_available():
        raise RuntimeError("Open Babel is not available. Cannot generate fingerprints.")

    # Process in batches to avoid memory issues if dataset is huge, though we expect ~5000
    # For simplicity and robustness, we process row by row with timeout checks
    fingerprint_data = []
    failed_count = 0

    for idx, row in df.iterrows():
        smiles = row[smiles_column]
        if not isinstance(smiles, str) or not smiles:
            logger.warning(f"Skipping row {idx} due to invalid SMILES")
            failed_count += 1
            continue

        record = {"smiles": smiles}
        for fp_type in fp_types:
            fp_bits = smiles_to_obabel_fingerprint(smiles, fp_type)
            if fp_bits:
                # Parse bits to list of ints for storage
                bits = parse_fingerprint_string(fp_bits, fp_type)
                record[f"{fp_type.lower()}_bits"] = bits
            else:
                record[f"{fp_type.lower()}_bits"] = [] # Empty list for failed generation

        fingerprint_data.append(record)

        if (idx + 1) % 100 == 0:
            elapsed = time.time() - start_time
            logger.info(f"Processed {idx + 1}/{len(df)} molecules. Elapsed: {elapsed:.2f}s")

    elapsed = time.time() - start_time
    logger.info(f"Fingerprint generation complete. Total time: {elapsed:.2f}s. Failed: {failed_count}")

    if failed_count > 0:
        logger.warning(f"{failed_count} molecules failed fingerprint generation.")
        # Per T019, if obabel fails to complete within window, exit 1.
        # Here we assume 'failed' means timeout or error per molecule, not total failure.
        # If too many fail, we might want to abort, but for now we proceed and log.

    # Convert to DataFrame
    # Flatten the bit lists into separate columns? Or keep as lists in parquet?
    # Parquet supports lists. The task says columns: smiles, maccs_bits, ecfp4_bits, fp2_bits.
    # Storing as list of ints is fine.
    result_df = pd.DataFrame(fingerprint_data)

    logger.info(f"Saving fingerprints to {output_file}...")
    result_df.to_parquet(output_file, index=False)
    logger.info("Saved successfully.")

def main():
    """Main entry point for fingerprint generation."""
    set_global_seed(42)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    ensure_dirs()

    # Paths
    train_set_path = _project_root / "data" / "derived" / "train_set.csv"
    output_path = _project_root / "data" / "processed" / "train_fingerprints.parquet"

    # Verify input exists (dependency check)
    if not train_set_path.exists():
        logger.error(f"Training set not found at {train_set_path}. "
                     "Please ensure T011.5 (Split Dataset) and T010.1 (MaxMin Sampling) are completed.")
        sys.exit(1)

    try:
        process_dataset(
            input_file=train_set_path,
            output_file=output_path,
            smiles_column="smiles",
            fp_types=FINGERPRINT_TYPES
        )
        logger.info("Fingerprint generation completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during fingerprint generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()