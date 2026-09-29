"""
Fingerprint generation module using Open Babel.

Generates MACCS, ECFP4, and FP2 fingerprints for molecular datasets by invoking
the `obabel` command-line tool via subprocess.
"""

import os
import sys
import subprocess
import logging
import time
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from data.preprocess import ensure_dirs as ensure_data_dirs
from utils.config import get_runtime_config, check_obabel_timeout

# Configure logging
logger = logging.getLogger(__name__)

def ensure_dirs():
    """Ensure output directories exist."""
    output_dirs = [
        Path("data/processed"),
        Path("data/derived")
    ]
    for directory in output_dirs:
        directory.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directories: {output_dirs}")

def check_obabel_available(timeout: float = 30.0) -> bool:
    """
    Check if obabel is available and responsive.

    Args:
        timeout: Maximum time in seconds to wait for the command.

    Returns:
        True if obabel is available, False otherwise.
    """
    try:
        result = subprocess.run(
            ["obabel", "-h"],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if result.returncode == 0:
            logger.info("Open Babel (obabel) is available.")
            return True
        else:
            logger.error(f"Open Babel returned error code: {result.returncode}")
            return False
    except FileNotFoundError:
        logger.error("Open Babel (obabel) not found in PATH. Please install it.")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Open Babel check timed out.")
        return False

def smiles_to_obabel_fingerprint(smiles: str, fingerprint_type: str, timeout: float = 60.0) -> Optional[str]:
    """
    Generate a specific fingerprint type for a single SMILES string using obabel.

    Args:
        smiles: The SMILES string of the molecule.
        fingerprint_type: The type of fingerprint (ECFP4, MACCS, FP2).
        timeout: Maximum time in seconds for the subprocess.

    Returns:
        The fingerprint string (hex or space-separated bits), or None if failed.
    """
    if not smiles or not isinstance(smiles, str):
        logger.warning(f"Invalid SMILES provided: {smiles}")
        return None

    try:
        # Prepare input for obabel
        # obabel expects SMILES input via stdin or file. We use stdin.
        input_data = f"{smiles}\n"

        # Construct command
        # -i smiles: input format
        # -o txt: output format (text)
        # -xf <type>: fingerprint type
        cmd = ["obabel", "-i", "smiles", "-o", "txt", "-xf", fingerprint_type]

        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:
            # Output is typically the SMILES followed by the fingerprint on the next line
            # or sometimes just the fingerprint depending on version/options.
            # We expect the fingerprint to be the last non-empty line or the second line.
            output_lines = result.stdout.strip().split('\n')
            if len(output_lines) >= 2:
                # The second line usually contains the fingerprint
                fingerprint_str = output_lines[1].strip()
                return fingerprint_str
            elif len(output_lines) == 1:
                # If only one line, it might be the fingerprint if SMILES was suppressed
                # But usually obabel outputs the molecule first.
                # Let's assume the last non-empty line is the fingerprint if it looks like bits
                for line in reversed(output_lines):
                    if line.strip():
                        return line.strip()
            return None
        else:
            logger.error(f"obabel failed for SMILES: {smiles}. Error: {result.stderr}")
            return None
    except subprocess.TimeoutExpired:
        logger.error(f"obabel timed out for SMILES: {smiles}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error generating fingerprint for {smiles}: {e}")
        return None

def generate_fingerprints_batch(smiles_list: List[str], fingerprint_types: List[str], timeout_per_mol: float = 60.0) -> List[Dict[str, Any]]:
    """
    Generate fingerprints for a list of SMILES strings.

    Args:
        smiles_list: List of SMILES strings.
        fingerprint_types: List of fingerprint types to generate.
        timeout_per_mol: Timeout per molecule.

    Returns:
        List of dictionaries containing SMILES and fingerprint values.
    """
    results = []
    start_time = time.time()
    total = len(smiles_list)
    logger.info(f"Starting fingerprint generation for {total} molecules.")

    for i, smiles in enumerate(smiles_list):
        if i % 100 == 0:
            elapsed = time.time() - start_time
            logger.info(f"Processed {i}/{total} molecules. Elapsed: {elapsed:.2f}s")

        row = {"smiles": smiles}
        for fp_type in fingerprint_types:
            fp_value = smiles_to_obabel_fingerprint(smiles, fp_type, timeout_per_mol)
            row[f"fp_{fp_type}"] = fp_value if fp_value else "NULL"

        results.append(row)

        # Check total time constraint
        if time.time() - start_time > 3600: # 1 hour limit safety check
            logger.warning("Approaching 1-hour limit. Stopping batch generation.")
            break

    return results

def parse_fingerprint_string(fp_str: str, fp_type: str) -> str:
    """
    Parse and normalize fingerprint string.

    Args:
        fp_str: The raw fingerprint string from obabel.
        fp_type: The fingerprint type.

    Returns:
        Normalized string representation.
    """
    if not fp_str or fp_str == "NULL":
        return "NULL"

    # obabel output for fingerprints is often space-separated bits or hex
    # We keep the raw string as generated, assuming downstream handles parsing
    # if necessary, but for CSV storage, we store the string representation.
    # Ensure no newlines
    return fp_str.replace('\n', ' ').strip()

def process_dataset(input_file: str, output_file: str, fingerprint_types: List[str] = None):
    """
    Process a dataset CSV file to generate fingerprints.

    Args:
        input_file: Path to input CSV with 'smiles' column.
        output_file: Path to output CSV with fingerprints.
        fingerprint_types: List of fingerprint types. Defaults to ['ECFP4', 'MACCS', 'FP2'].
    """
    if fingerprint_types is None:
        fingerprint_types = ["ECFP4", "MACCS", "FP2"]

    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        # Check if it's the diverse subset or raw data
        if "diverse_subset" in input_file:
            logger.error("Please ensure T010.1 (Execute MaxMin Sampling) has completed.")
        elif "train_set" in input_file or "test_set" in input_file:
            logger.error("Please ensure T011.5 (Split Dataset) has completed.")
        raise FileNotFoundError(f"Input file not found: {input_file}")

    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)

    if "smiles" not in df.columns:
        logger.error(f"Input file {input_file} does not contain 'smiles' column.")
        raise ValueError(f"Missing 'smiles' column in {input_file}")

    # Remove rows with missing or invalid SMILES
    df = df.dropna(subset=["smiles"])
    df = df[df["smiles"].str.strip() != ""]

    logger.info(f"Processing {len(df)} valid molecules.")

    # Generate fingerprints
    # To avoid subprocess overhead per molecule in a loop for large datasets,
    # we could batch, but obabel is typically line-by-line.
    # We will process in chunks or sequentially.
    # Given the constraint, we process sequentially with timeout checks.

    all_results = []
    start_time = time.time()
    config = get_runtime_config()
    timeout_per_mol = config.get("obabel_timeout_per_mol", 60.0)

    for idx, row in df.iterrows():
        smiles = row["smiles"]
        row_result = {"smiles": smiles}
        for fp_type in fingerprint_types:
            fp_val = smiles_to_obabel_fingerprint(smiles, fp_type, timeout_per_mol)
            row_result[f"fp_{fp_type}"] = fp_val if fp_val else "NULL"
        all_results.append(row_result)

        # Progress logging
        if (idx + 1) % 500 == 0:
            logger.info(f"Processed {idx + 1}/{len(df)} molecules.")

        # Global timeout check (e.g., 45 mins as per T010.1 constraint logic)
        if time.time() - start_time > 2700:
            logger.warning("45-minute limit for fingerprint generation reached. Saving partial results.")
            break

    logger.info(f"Saving results to {output_file}")
    result_df = pd.DataFrame(all_results)
    result_df.to_csv(output_file, index=False)
    logger.info(f"Fingerprint generation complete. Saved to {output_file}")

def generate_fingerprints():
    """
    Main entry point for generating fingerprints for the full diverse dataset.
    This function orchestrates the generation for all molecules to prevent data leakage.
    """
    ensure_dirs()

    # Check obabel availability
    if not check_obabel_available():
        logger.error("Open Babel not available. Cannot proceed.")
        # Write a log file indicating failure
        log_path = Path("data/derived/fingerprint_log.txt")
        with open(log_path, "w") as f:
            f.write("ERROR: Open Babel not available. Partial progress saved: None.\n")
        sys.exit(1)

    # Determine input file
    # The task specifies generating for "all molecules in the full diverse dataset"
    # The diverse subset is produced by T010.1 at data/derived/diverse_subset.csv
    input_file = Path("data/derived/diverse_subset.csv")

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T010.1 (Execute MaxMin Sampling) and T011.5 (Split Dataset) are completed.")
        # Create a log file for the failure
        log_path = Path("data/derived/fingerprint_log.txt")
        with open(log_path, "w") as f:
            f.write(f"ERROR: Input file {input_file} not found. Partial progress saved: None.\n")
        sys.exit(1)

    output_file = Path("data/processed/full_fingerprints.csv")

    try:
        process_dataset(str(input_file), str(output_file))
        logger.info("Fingerprint generation completed successfully.")
    except Exception as e:
        logger.error(f"Error during fingerprint generation: {e}")
        # Save partial progress if any
        log_path = Path("data/derived/fingerprint_log.txt")
        with open(log_path, "a") as f:
            f.write(f"ERROR: {str(e)}. Partial progress saved.\n")
        sys.exit(1)

def main():
    """Main function to run the fingerprint generation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/fingerprint.log', mode='a'),
            logging.StreamHandler()
        ]
    )
    # Ensure logs directory exists
    Path("logs").mkdir(parents=True, exist_ok=True)

    generate_fingerprints()

if __name__ == "__main__":
    main()
