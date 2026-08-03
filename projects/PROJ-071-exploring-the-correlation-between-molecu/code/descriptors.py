from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit import RDLogger

# Disable RDKit warnings for cleaner logs
RDLogger.DisableLog('rdApp.*')

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure directories exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROCESSED_DIR / "descriptors.log")
    ]
)
logger = logging.getLogger("descriptors")

# Constants
DESCRIPTOR_COLUMNS = [
    "smiles", "MW", "TPSA", "RotatableBondCount", "AromaticRingCount", "WienerIndex", "ZagrebIndex"
]
EXCLUDED_FILE = PROCESSED_DIR / "excluded_molecules.csv"
MERGED_INPUT = PROCESSED_DIR / "merged_drugs.csv"
GATE_STATUS_FILE = DATA_DIR / "gate_status.json"


def get_data_path() -> Path:
    """Return the path to the merged dataset."""
    return MERGED_INPUT


def log_error_to_file(smiles: str, error_type: str, source_hash: str) -> None:
    """Log a failed molecule to the excluded molecules CSV."""
    timestamp = datetime.utcnow().isoformat()
    file_exists = os.path.exists(EXCLUDED_FILE)

    with open(EXCLUDED_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["smiles", "error_type", "timestamp", "source_hash"])
        writer.writerow([smiles, error_type, timestamp, source_hash])


def validate_molecule(smiles: str) -> Optional[Chem.Mol]:
    """
    Validate and return an RDKit molecule object.
    Returns None if the SMILES is invalid.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        # Sanitize to catch valence issues immediately
        Chem.SanitizeMol(mol)
        return mol
    except Exception:
        return None


def calculate_tpsa(mol: Chem.Mol) -> float:
    """Calculate Topological Polar Surface Area."""
    return Descriptors.TPSA(mol)


def calculate_rotatable_bonds(mol: Chem.Mol) -> int:
    """Calculate Rotatable Bond Count."""
    return rdMolDescriptors.CalcNumRotatableBonds(mol)


def calculate_mw(mol: Chem.Mol) -> float:
    """Calculate Molecular Weight."""
    return Descriptors.MolWt(mol)


def calculate_aromatic_rings(mol: Chem.Mol) -> int:
    """Calculate Aromatic Ring Count."""
    return rdMolDescriptors.CalcNumAromaticRings(mol)


def calculate_wiener_index(mol: Chem.Mol) -> float:
    """Calculate Wiener Index."""
    return Descriptors.WienerIndex(mol)


def calculate_zagreb_index(mol: Chem.Mol) -> float:
    """Calculate Zagreb Index."""
    # Using the built-in RDKit descriptor directly as per task spec
    return Descriptors.Zagreb(mol)


def calculate_descriptors_for_molecule(
    smiles: str, source_hash: str
) -> Optional[Dict[str, Any]]:
    """
    Calculate all required descriptors for a single molecule.
    Returns a dict of descriptors or None if calculation fails.
    """
    mol = validate_molecule(smiles)
    if mol is None:
        log_error_to_file(smiles, "Invalid SMILES or Sanitization Failed", source_hash)
        return None

    try:
        return {
            "smiles": smiles,
            "MW": calculate_mw(mol),
            "TPSA": calculate_tpsa(mol),
            "RotatableBondCount": calculate_rotatable_bonds(mol),
            "AromaticRingCount": calculate_aromatic_rings(mol),
            "WienerIndex": calculate_wiener_index(mol),
            "ZagrebIndex": calculate_zagreb_index(mol)
        }
    except Exception as e:
        # Catch specific RDKit exceptions if possible, generic otherwise
        error_type = type(e).__name__
        log_error_to_file(smiles, error_type, source_hash)
        logger.warning(f"Descriptor calculation failed for {smiles}: {e}")
        return None


def calculate_descriptors_batch(input_path: Path) -> Path:
    """
    Read the merged dataset, calculate descriptors, and save results.
    Returns the path to the output CSV.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path = PROCESSED_DIR / "descriptors_calculated.csv"
    results = []
    total = 0
    success = 0

    # Calculate hash of input file for provenance
    with open(input_path, "rb") as f:
        source_hash = hashlib.sha256(f.read()).hexdigest()

    logger.info(f"Starting descriptor calculation on {input_path}")

    with open(input_path, "r", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        # Ensure required columns exist
        if "smiles" not in reader.fieldnames:
            raise ValueError("Input CSV must contain 'smiles' column")

        for row in reader:
            total += 1
            smiles = row["smiles"].strip()
            if not smiles:
                continue

            res = calculate_descriptors_for_molecule(smiles, source_hash)
            if res:
                # Merge with original row data to preserve degradation info
                full_record = {**row, **res}
                results.append(full_record)
                success += 1

    # Write results
    if results:
        fieldnames = list(results[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        logger.info(f"Processed {total} molecules. Success: {success}. Output: {output_path}")
    else:
        logger.warning("No valid descriptors calculated. Output file not created.")

    return output_path


def check_gate_status() -> bool:
    """
    Check if the data availability gate passed.
    Returns True if PASS, False otherwise.
    """
    if not GATE_STATUS_FILE.exists():
        logger.error("Gate status file not found. Cannot proceed.")
        return False

    with open(GATE_STATUS_FILE, "r") as f:
        status = json.load(f)

    if status.get("status") == "PASS":
        return True
    else:
        reason = status.get("reason", "Unknown reason")
        logger.warning(f"Gate status is FAIL: {reason}. Skipping descriptor calculation.")
        return False


def main() -> None:
    """Main entry point for descriptor calculation."""
    # Check Gate
    if not check_gate_status():
        # If gate failed, we do not run, but we exit cleanly (0) as per pipeline design
        # The failure is already logged and recorded in gate_status.json
        sys.exit(0)

    input_path = get_data_path()
    try:
        output_path = calculate_descriptors_batch(input_path)
        # Verify output exists and is non-empty
        if not output_path.exists() or os.path.getsize(output_path) == 0:
            raise RuntimeError("Descriptor calculation produced no output.")
        logger.info("Descriptor calculation completed successfully.")
    except Exception as e:
        logger.error(f"Descriptor calculation failed: {e}")
        raise


if __name__ == "__main__":
    main()