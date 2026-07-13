"""
generate_descriptors.py

Invokes DFTB+ for geometry optimization and descriptor extraction.
Implements logging for invocation, timing, and resource usage (Task T017).
"""
import csv
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import resource
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import utilities from existing modules
from utils.error_utils import (
    detect_convergence_failure,
    check_oom_in_log,
    handle_convergence_failure,
    handle_oom,
    run_with_oom_protection,
    ConvergenceError,
    OOMError,
)
from utils.validation_utils import validate_physical_ranges

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/descriptor_generation.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)

ZENODO_RECORD_ID = "1234567"  # Placeholder for actual Zenodo ID
DFTB_INPUT_TEMPLATE = """
[System]
Coordinates = {xyz_file}
[Hamiltonian]
Method = DFTB
[Driver]
GeometricOptimization = Yes
MaxCycles = 200
"""

def smiles_to_xyz(smiles: str, output_path: str) -> None:
    """Convert SMILES to XYZ format using RDKit (simplified stub for context)."""
    # In a real implementation, this would use RDKit to generate coordinates
    # For now, we assume a placeholder or external conversion
    logger.warning(f"SMILES to XYZ conversion stub called for {smiles}")
    with open(output_path, "w") as f:
        f.write("1\n")
        f.write("Generated\n")
        f.write("C 0.0 0.0 0.0\n")

def create_dftb_input(xyz_file: str, input_dir: str) -> str:
    """Create DFTB+ input file (gen.inp) from XYZ."""
    os.makedirs(input_dir, exist_ok=True)
    input_path = os.path.join(input_dir, "gen.inp")
    with open(input_path, "w") as f:
        f.write(DFTB_INPUT_TEMPLATE.format(xyz_file=os.path.basename(xyz_file)))
    return input_path

def run_dftb_work(input_dir: str, dftb_binary: str = "dftb+") -> Tuple[bool, str]:
    """
    Run DFTB+ in the input directory.
    Returns (success, message).
    Logs timing and resource usage.
    """
    logger.info(f"Starting DFTB+ invocation in {input_dir}")
    start_time = time.time()

    try:
        # Get initial memory usage (RSS)
        rusage_start = resource.getrusage(resource.RUSAGE_CHILDREN)
        initial_rss = rusage_start.ru_maxrss  # In KB on Linux

        proc = subprocess.run(
            [dftb_binary],
            cwd=input_dir,
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout
        )

        rusage_end = resource.getrusage(resource.RUSAGE_CHILDREN)
        final_rss = rusage_end.ru_maxrss
        elapsed_time = time.time() - start_time

        logger.info(
            f"DFTB+ finished in {elapsed_time:.2f}s. "
            f"Peak RSS: {final_rss / 1024:.2f} MB"
        )

        if proc.returncode != 0:
            log_content = proc.stderr if proc.stderr else proc.stdout
            if check_oom_in_log(log_content):
                logger.error("OOM detected in DFTB+ log.")
                return False, "OOM"
            if detect_convergence_failure(log_content):
                logger.error("Convergence failure detected in DFTB+ log.")
                return False, "Convergence"
            logger.error(f"DFTB+ failed with code {proc.returncode}: {proc.stderr}")
            return False, "RuntimeError"

        return True, "Success"

    except subprocess.TimeoutExpired:
        logger.error(f"DFTB+ timed out after 3600s")
        return False, "Timeout"
    except FileNotFoundError:
        logger.error(f"DFTB+ binary not found: {dftb_binary}")
        return False, "BinaryNotFound"
    except Exception as e:
        logger.error(f"Unexpected error running DFTB+: {e}")
        return False, str(e)

def parse_dftb_output(input_dir: str) -> Optional[Dict[str, float]]:
    """
    Parse DFTB+ output (e.g., dftb.out) for HOMO, LUMO, charges.
    Returns dict with descriptors or None if parsing fails.
    """
    output_file = os.path.join(input_dir, "dftb.out")
    if not os.path.exists(output_file):
        logger.error(f"Output file not found: {output_file}")
        return None

    descriptors = {}
    try:
        with open(output_file, "r") as f:
            content = f.read()

        # Regex patterns for DFTB+ output (example)
        homo_match = re.search(r"HOMO.*?\s+([-+]?\d*\.\d+)", content)
        lumo_match = re.search(r"LUMO.*?\s+([-+]?\d*\.\d+)", content)
        charge_match = re.search(r"Total charge.*?\s+([-+]?\d*\.\d+)", content)

        if homo_match:
            descriptors["HOMO"] = float(homo_match.group(1))
        if lumo_match:
            descriptors["LUMO"] = float(lumo_match.group(1))
        if charge_match:
            descriptors["TotalCharge"] = float(charge_match.group(1))

        if not descriptors:
            logger.warning("No descriptors found in DFTB+ output.")
            return None

        return descriptors

    except Exception as e:
        logger.error(f"Error parsing DFTB+ output: {e}")
        return None

def process_molecule(
    smiles: str,
    row_id: int,
    data_dir: str,
    dftb_binary: str = "dftb+",
) -> Optional[Dict]:
    """
    Process a single molecule: convert, run DFTB+, parse, validate.
    Includes logging for timing and resource usage (Task T017).
    """
    logger.info(f"Processing molecule {row_id}: {smiles}")
    start_total = time.time()

    work_dir = os.path.join(data_dir, f"mol_{row_id}")
    os.makedirs(work_dir, exist_ok=True)

    xyz_file = os.path.join(work_dir, "input.xyz")
    smiles_to_xyz(smiles, xyz_file)

    create_dftb_input(xyz_file, work_dir)

    success, msg = run_dftb_work(work_dir, dftb_binary)

    if not success:
        if msg == "Convergence":
            handle_convergence_failure(row_id, smiles, logger)
        elif msg == "OOM":
            handle_oom(row_id, smiles, logger)
        else:
            logger.error(f"Skipping molecule {row_id} due to {msg}")
        return None

    descriptors = parse_dftb_output(work_dir)
    if not descriptors:
        logger.error(f"Failed to parse descriptors for molecule {row_id}")
        return None

    # Validate physical ranges
    try:
        validate_physical_ranges(descriptors, logger)
    except Exception as e:
        logger.warning(f"Validation failed for molecule {row_id}: {e}")
        return None

    elapsed_total = time.time() - start_total
    logger.info(
        f"Molecule {row_id} completed in {elapsed_total:.2f}s. "
        f"Descriptors: {descriptors}"
    )

    result = {
        "id": row_id,
        "SMILES": smiles,
        **descriptors,
        "processing_time_s": elapsed_total,
    }
    return result

def main():
    """Main entry point to process dataset and generate descriptors."""
    logger.info("Starting descriptor generation pipeline.")
    data_dir = "data/processed"
    os.makedirs(data_dir, exist_ok=True)

    # Load input CSV (assumed to be downloaded by T004)
    input_csv = "data/raw/experimental_barrier.csv"
    if not os.path.exists(input_csv):
        logger.error(f"Input CSV not found: {input_csv}")
        sys.exit(1)

    results = []
    with open(input_csv, "r") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            smiles = row["SMILES"]
            result = process_molecule(smiles, i, data_dir)
            if result:
                results.append(result)

    output_csv = "data/descriptors_semi.csv"
    if results:
        with open(output_csv, "w", newline="") as f:
            fieldnames = list(results[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        logger.info(f"Successfully wrote {len(results)} descriptors to {output_csv}")
    else:
        logger.warning("No descriptors generated.")

if __name__ == "__main__":
    main()