"""
Integration test for code/generate_descriptors.py on 50 molecules.

This test verifies that the descriptor generation pipeline:
1. Loads exactly 50 molecules from the experimental barrier dataset.
2. Invokes DFTB+ for geometry optimization and descriptor extraction.
3. Produces a valid CSV output (descriptors_semi.csv) with:
   - 50 rows (one per molecule)
   - No NaN values in critical columns
   - HOMO and LUMO in eV
   - Mulliken charges summing to the net molecular charge
4. Handles convergence failures gracefully (skips and logs).
5. Validates physical ranges (HOMO < LUMO).

Prerequisites:
- The experimental barrier dataset must be downloaded to data/experimental_barrier.csv
- DFTB+ must be installed and accessible in PATH
- The test expects the output file data/descriptors_semi.csv to be generated
"""

import csv
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"

sys.path.insert(0, str(CODE_DIR))

from generate_descriptors import (
    process_molecule,
    validate_descriptors,
    smiles_to_xyz,
    create_dftb_input,
    run_dftb_work,
    parse_dftb_output
)
from utils.error_utils import ConvergenceError, OOMError, handle_convergence_failure, handle_oom
from utils.memory_monitor import run_with_memory_limit

# Constants for test
TEST_INPUT_FILE = DATA_DIR / "experimental_barrier.csv"
TEST_OUTPUT_FILE = DATA_DIR / "descriptors_semi.csv"
TEST_WORK_DIR = DATA_DIR / "dftb_work"
EXPECTED_ROW_COUNT = 50
MAX_MEMORY_BYTES = 6.5 * 1024**3  # 6.5 GB

def _load_test_molecules(count: int = EXPECTED_ROW_COUNT) -> List[Dict[str, Any]]:
    """Load a subset of molecules from the experimental barrier dataset."""
    if not TEST_INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Test data file {TEST_INPUT_FILE} not found. "
            "Please run code/download_data.py first."
        )

    molecules = []
    with open(TEST_INPUT_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= count:
                break
            molecules.append(row)

    if len(molecules) < count:
        raise ValueError(
            f"Expected {count} molecules but found {len(molecules)} in {TEST_INPUT_FILE}"
        )

    return molecules

def _cleanup_work_dir():
    """Remove the DFTB work directory if it exists."""
    if TEST_WORK_DIR.exists():
        shutil.rmtree(TEST_WORK_DIR)
    TEST_WORK_DIR.mkdir(parents=True, exist_ok=True)

def _run_dftb_pipeline(molecules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run the DFTB+ descriptor generation pipeline on the provided molecules."""
    results = []
    failed_count = 0

    for idx, mol in enumerate(molecules):
        smiles = mol["SMILES"]
        mol_id = f"mol_{idx:03d}"

        try:
            # Convert SMILES to XYZ
            xyz_path = TEST_WORK_DIR / f"{mol_id}.xyz"
            if not smiles_to_xyz(smiles, str(xyz_path)):
                raise RuntimeError(f"Failed to convert SMILES to XYZ for {smiles}")

            # Create DFTB input
            dftb_in_path = TEST_WORK_DIR / f"{mol_id}.gen"
            create_dftb_input(str(xyz_path), str(dftb_in_path))

            # Run DFTB+ with memory protection
            work_subdir = TEST_WORK_DIR / mol_id
            work_subdir.mkdir(exist_ok=True)

            success = run_with_memory_limit(
                ["dftb+", str(dftb_in_path)],
                cwd=str(work_subdir),
                memory_limit_bytes=MAX_MEMORY_BYTES
            )

            if not success:
                # Check for specific failure types
                log_file = work_subdir / "dftb.log"
                if log_file.exists():
                    with open(log_file, "r") as f:
                        log_content = f.read()
                    if "convergence" in log_content.lower():
                        handle_convergence_failure(mol_id, log_content)
                    elif "oom" in log_content.lower() or "out of memory" in log_content.lower():
                        handle_oom(mol_id, log_content)
                failed_count += 1
                continue

            # Parse DFTB output
            output_path = work_subdir / "detailed.out"
            if not output_path.exists():
                raise FileNotFoundError(f"DFTB+ output not found for {mol_id}")

            descriptors = parse_dftb_output(str(output_path))

            if descriptors is None:
                raise ValueError(f"Failed to parse DFTB+ output for {mol_id}")

            # Validate descriptors
            is_valid, errors = validate_descriptors(descriptors)
            if not is_valid:
                print(f"Validation failed for {mol_id}: {errors}")
                failed_count += 1
                continue

            # Add metadata
            descriptors["SMILES"] = smiles
            descriptors["mol_id"] = mol_id
            descriptors["original_row"] = idx
            results.append(descriptors)

        except Exception as e:
            print(f"Error processing {mol_id}: {str(e)}")
            failed_count += 1
            continue

    return results

def _write_results(results: List[Dict[str, Any]], output_path: Path):
    """Write results to CSV file."""
    if not results:
        raise RuntimeError("No results to write - all molecules failed processing")

    fieldnames = [
        "mol_id", "SMILES", "HOMO", "LUMO", "gap", "mayer_order",
        "total_charge", "net_charge", "converged"
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

def _validate_output_csv(output_path: Path):
    """Validate the generated CSV file."""
    if not output_path.exists():
        raise FileNotFoundError(f"Output file {output_path} was not created")

    with open(output_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Check row count
    if len(rows) != EXPECTED_ROW_COUNT:
        raise AssertionError(
            f"Expected {EXPECTED_ROW_COUNT} rows but found {len(rows)}"
        )

    # Check for NaN values in critical columns
    critical_cols = ["HOMO", "LUMO", "gap", "mayer_order", "total_charge"]
    for i, row in enumerate(rows):
        for col in critical_cols:
            if col not in row or row[col] == "" or row[col] == "nan":
                raise AssertionError(f"NaN or missing value in {col} at row {i}")

    # Check physical ranges
    for i, row in enumerate(rows):
        try:
            homo = float(row["HOMO"])
            lumo = float(row["LUMO"])
            if homo >= lumo:
                raise AssertionError(
                    f"HOMO ({homo}) >= LUMO ({lumo}) at row {i}. "
                    "Physical constraint violated."
                )
        except ValueError as e:
            raise AssertionError(f"Invalid float value at row {i}: {e}")

    # Check charge consistency (within tolerance)
    for i, row in enumerate(rows):
        try:
            total_charge = float(row["total_charge"])
            net_charge = float(row["net_charge"])
            if abs(total_charge - net_charge) > 0.1:
                raise AssertionError(
                    f"Charge mismatch at row {i}: total={total_charge}, net={net_charge}"
                )
        except ValueError as e:
            raise AssertionError(f"Invalid charge value at row {i}: {e}")

    return True

def test_generate_descriptors_integration():
    """
    Integration test: Run DFTB+ on 50 molecules and validate output.

    This test:
    1. Loads 50 molecules from experimental_barrier.csv
    2. Runs the full DFTB+ descriptor generation pipeline
    3. Validates the output CSV meets all requirements
    4. Ensures no NaN values and physical constraints are satisfied
    """
    print("Starting integration test for descriptor generation...")

    # Cleanup and setup
    _cleanup_work_dir()

    # Load test molecules
    molecules = _load_test_molecules(EXPECTED_ROW_COUNT)
    print(f"Loaded {len(molecules)} molecules for testing")

    # Run the pipeline
    results = _run_dftb_pipeline(molecules)
    print(f"Successfully processed {len(results)} molecules")

    if len(results) == 0:
        raise AssertionError("No molecules were successfully processed")

    # Write results
    _write_results(results, TEST_OUTPUT_FILE)
    print(f"Results written to {TEST_OUTPUT_FILE}")

    # Validate output
    _validate_output_csv(TEST_OUTPUT_FILE)
    print("Output validation passed")

    print("Integration test completed successfully!")

if __name__ == "__main__":
    test_generate_descriptors_integration()
