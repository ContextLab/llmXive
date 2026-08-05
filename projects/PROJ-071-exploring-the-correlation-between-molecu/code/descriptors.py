"""
Molecular Descriptor Calculation Module (Task T014).

Calculates molecular descriptors (TPSA, Rotatable Bonds, MW, Aromatic Rings,
Wiener Index, Zagreb Index) using RDKit. Implements robust error handling
to log invalid molecules to data/processed/excluded_molecules.csv.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit.Chem.rdchem import AtomValenceException, MolSanitizeException

# Local imports (API surface provided)
from logging_config import get_logger, log_operation, log_pipeline_start, log_pipeline_complete
from error_handlers import AtomValenceException as CustomAtomValenceException, DescriptorCalculationError

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
EXCLUDED_FILE = PROCESSED_DIR / "excluded_molecules.csv"
MERGED_FILE = PROCESSED_DIR / "merged_drugs.csv"
GATE_STATUS_FILE = DATA_DIR / "gate_status.json"

# Initialize logger
logger = get_logger("descriptors")

def calculate_file_hash(filepath: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "FILE_NOT_FOUND"

def get_source_hash() -> str:
    """Get hash of the source data file (merged_drugs.csv)."""
    if not MERGED_FILE.exists():
        return "NO_SOURCE_FILE"
    return calculate_file_hash(MERGED_FILE)

def log_error_to_file(smiles: str, error_type: str, source_hash: str) -> None:
    """
    Log a molecule error to the excluded_molecules.csv file.
    Ensures the file header exists if the file is new.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().isoformat()

    file_exists = EXCLUDED_FILE.exists()
    header = ["smiles", "error_type", "timestamp", "source_hash"]

    with open(EXCLUDED_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow([smiles, error_type, timestamp, source_hash])

def validate_molecule(smiles: str) -> Optional[Chem.Mol]:
    """
    Convert SMILES to RDKit Mol object and sanitize.
    Raises custom exceptions on failure.
    """
    if not smiles or not isinstance(smiles, str):
        raise CustomAtomValenceException("Invalid SMILES format: None or empty")

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise CustomAtomValenceException(f"RDKit failed to parse SMILES: {smiles}")

    # Sanitize to catch valence errors
    try:
        Chem.SanitizeMol(mol)
    except ValueError as e:
        # RDKit raises ValueError for sanitization issues, map to our custom exception
        raise CustomAtomValenceException(f"Sanitization failed: {str(e)}")

    return mol

def calculate_tpsa(mol: Chem.Mol) -> float:
    return Descriptors.TPSA(mol)

def calculate_rotatable_bonds(mol: Chem.Mol) -> int:
    return rdMolDescriptors.CalcNumRotatableBonds(mol)

def calculate_mw(mol: Chem.Mol) -> float:
    return Descriptors.MolWt(mol)

def calculate_aromatic_rings(mol: Chem.Mol) -> int:
    return rdMolDescriptors.CalcNumAromaticRings(mol)

def calculate_wiener_index(mol: Chem.Mol) -> float:
    # Wiener index is the sum of distances between all pairs of atoms
    # RDKit does not have a direct 'Wiener' descriptor in Descriptors,
    # but we can calculate it via the distance matrix.
    try:
        dists = rdMolDescriptors.GetDistanceMatrix(mol)
        # Sum of upper triangle (excluding diagonal)
        total = 0.0
        n = len(dists)
        for i in range(n):
            for j in range(i + 1, n):
                total += dists[i][j]
        return float(total)
    except Exception:
        return float('nan')

def calculate_zagreb_index(mol: Chem.Mol) -> float:
    # First Zagreb Index: Sum of squared degrees of all vertices
    try:
        adj = mol.GetAdjacencyMatrix()
        total = 0.0
        for row in adj:
            degree = sum(row)
            total += degree ** 2
        return float(total)
    except Exception:
        return float('nan')

def calculate_descriptors_for_molecule(smiles: str, source_hash: str) -> Dict[str, Any]:
    """
    Calculate all descriptors for a single molecule.
    Returns a dict with results or logs an error if calculation fails.
    """
    try:
        mol = validate_molecule(smiles)
        return {
            "smiles": smiles,
            "tpsa": calculate_tpsa(mol),
            "rotatable_bonds": calculate_rotatable_bonds(mol),
            "mw": calculate_mw(mol),
            "aromatic_rings": calculate_aromatic_rings(mol),
            "wiener_index": calculate_wiener_index(mol),
            "zagreb_index": calculate_zagreb_index(mol),
            "status": "success"
        }
    except (CustomAtomValenceException, AtomValenceException, MolSanitizeException, ValueError) as e:
        error_type = type(e).__name__
        error_msg = str(e)
        log_error_to_file(smiles, f"{error_type}: {error_msg}", source_hash)
        return {
            "smiles": smiles,
            "status": "error",
            "error_type": error_type,
            "error_message": error_msg
        }
    except Exception as e:
        # Catch-all for unexpected errors
        error_type = type(e).__name__
        log_error_to_file(smiles, f"UnexpectedError: {str(e)}", source_hash)
        return {
            "smiles": smiles,
            "status": "error",
            "error_type": error_type,
            "error_message": str(e)
        }

def calculate_descriptors_batch(df: pd.DataFrame, source_hash: str) -> pd.DataFrame:
    """
    Calculate descriptors for a batch of molecules in a DataFrame.
    Adds descriptor columns to the dataframe.
    """
    results = []
    for idx, row in df.iterrows():
        smiles = row.get("smiles") or row.get("canonical_smiles")
        if not smiles:
            log_error_to_file("N/A", "MissingSMILES", source_hash)
            continue

        res = calculate_descriptors_for_molecule(smiles, source_hash)
        results.append(res)

    result_df = pd.DataFrame(results)

    # Filter out errors from the main calculation result if we want a clean DF,
    # but for this task we return the full result set.
    # We will return the DF with descriptor columns filled where possible.
    return result_df

def check_gate_status() -> bool:
    """Check if the data availability gate passed."""
    if not GATE_STATUS_FILE.exists():
        return False
    try:
        with open(GATE_STATUS_FILE, "r") as f:
            status = json.load(f)
        return status.get("status") == "PASS"
    except (json.JSONDecodeError, KeyError):
        return False

def get_data_path() -> Path:
    return MERGED_FILE

@log_operation
def main() -> int:
    """
    Main entry point for descriptor calculation.
    1. Checks gate status.
    2. Loads merged_drugs.csv.
    3. Calculates descriptors.
    4. Saves output to data/processed/descriptors.csv (or updates merged).
    """
    log_pipeline_start("T014_Descriptor_Calculation", {"task": "T014"})

    # Ensure output directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Check Gate
    if not check_gate_status():
        logger.log("GateCheck", {"status": "FAIL", "reason": "Gate not passed or missing"})
        print("Data Availability Gate failed. Skipping descriptor calculation.")
        return 0

    # Load Data
    if not MERGED_FILE.exists():
        logger.log("LoadData", {"status": "FAIL", "reason": "merged_drugs.csv not found"})
        print(f"Error: {MERGED_FILE} not found.")
        return 1

    try:
        df = pd.read_csv(MERGED_FILE)
    except Exception as e:
        logger.log("LoadData", {"status": "FAIL", "error": str(e)})
        print(f"Error reading {MERGED_FILE}: {e}")
        return 1

    if df.empty:
        logger.log("LoadData", {"status": "WARN", "reason": "DataFrame is empty"})
        print("Warning: Merged dataset is empty.")
        return 0

    # Calculate Source Hash
    source_hash = get_source_hash()
    logger.log("SourceHash", {"hash": source_hash})

    # Calculate Descriptors
    print(f"Calculating descriptors for {len(df)} molecules...")
    descriptor_df = calculate_descriptors_batch(df, source_hash)

    # Merge results back or save separately
    # The task implies we produce the calculated metrics.
    # We will save a new file: data/processed/descriptors.csv
    output_path = PROCESSED_DIR / "descriptors.csv"

    # Ensure we have a clean output with only successful calculations for the main analysis
    # Or save the full log including errors? The spec says "log error to excluded...".
    # Let's save the successful ones to descriptors.csv and errors are in excluded_molecules.csv
    successful = descriptor_df[descriptor_df["status"] == "success"]

    if not successful.empty:
        # Select columns for output
        output_cols = ["smiles", "tpsa", "rotatable_bonds", "mw", "aromatic_rings", "wiener_index", "zagreb_index"]
        # Ensure all cols exist
        for col in output_cols:
            if col not in successful.columns:
                successful[col] = None

        successful[output_cols].to_csv(output_path, index=False)
        logger.log("SaveOutput", {"path": str(output_path), "count": len(successful)})
        print(f"Saved {len(successful)} successful descriptor records to {output_path}")
    else:
        logger.log("SaveOutput", {"status": "FAIL", "reason": "No successful calculations"})
        print("No successful descriptor calculations to save.")

    log_pipeline_complete("T014_Descriptor_Calculation")
    return 0

if __name__ == "__main__":
    sys.exit(main())