from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit import RDLogger

# Disable RDKit warnings to keep logs clean
RDLogger.DisableLog('rdApp.*')

# Import shared logging utilities
from logging_config import get_logger, log_operation, LogEntry

# Import error handling types
from error_handlers import AtomValenceException

# Project root and data paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

def get_data_path() -> Path:
    return PROCESSED_DIR / "merged_drugs.csv"

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    if not file_path.exists():
        return "FILE_NOT_FOUND"
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def log_error_to_file(
    smiles: str,
    error_type: str,
    timestamp: str,
    source_hash: str,
    output_path: Optional[Path] = None
) -> None:
    """
    Log a molecule error to the excluded_molecules.csv file.
    Schema: smiles, error_type, timestamp, source_hash
    """
    if output_path is None:
        output_path = PROCESSED_DIR / "excluded_molecules.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = output_path.exists() and output_path.stat().st_size > 0

    with open(output_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['smiles', 'error_type', 'timestamp', 'source_hash'])
        writer.writerow([smiles, error_type, timestamp, source_hash])

def validate_molecule(smiles: str) -> Optional[Chem.Mol]:
    """
    Convert SMILES to RDKit Mol object.
    Raises AtomValenceException if valence is non-standard.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            # RDKit returns None for unparseable SMILES, but we want to be explicit
            # about valence errors specifically.
            return None
        
        # Check for valence errors explicitly
        # rdchem.AtomValenceException is raised when sanitization fails due to valence
        Chem.SanitizeMol(mol)
        return mol
    except Exception as e:
        # Check if it's a valence exception
        if "valence" in str(e).lower() or isinstance(e, Chem.rdchem.AtomValenceException):
            raise AtomValenceException(f"Valence error for SMILES: {smiles}") from e
        # Re-raise other errors
        raise

def calculate_tpsa(mol: Chem.Mol) -> float:
    return Descriptors.TPSA(mol)

def calculate_rotatable_bonds(mol: Chem.Mol) -> int:
    return Descriptors.NumRotatableBonds(mol)

def calculate_mw(mol: Chem.Mol) -> float:
    return Descriptors.MolWt(mol)

def calculate_aromatic_rings(mol: Chem.Mol) -> int:
    return rdMolDescriptors.CalcNumAromaticRings(mol)

def calculate_wiener_index(mol: Chem.Mol) -> float:
    # Wiener index is not directly in Descriptors, use CalcWienerNumber
    return rdMolDescriptors.CalcWienerNumber(mol)

def calculate_zagreb_index(mol: Chem.Mol) -> float:
    return Descriptors.Zagreb(mol)

def calculate_descriptors_for_molecule(
    mol: Chem.Mol,
    smiles: str,
    source_hash: str,
    excluded_path: Path
) -> Dict[str, Any]:
    """
    Calculate all descriptors for a single molecule.
    Handles AtomValenceException by logging to excluded_molecules.csv.
    """
    try:
        tpsa = calculate_tpsa(mol)
        rot_bonds = calculate_rotatable_bonds(mol)
        mw = calculate_mw(mol)
        arom_rings = calculate_aromatic_rings(mol)
        wiener = calculate_wiener_index(mol)
        zagreb = calculate_zagreb_index(mol)

        return {
            "smiles": smiles,
            "tpsa": tpsa,
            "rotatable_bonds": rot_bonds,
            "mw": mw,
            "aromatic_rings": arom_rings,
            "wiener_index": wiener,
            "zagreb_index": zagreb,
            "status": "success"
        }
    except AtomValenceException as e:
        timestamp = datetime.utcnow().isoformat()
        error_type = "AtomValenceException"
        log_error_to_file(smiles, error_type, timestamp, source_hash, excluded_path)
        return {
            "smiles": smiles,
            "status": "failed",
            "error_type": error_type,
            "reason": str(e)
        }
    except Exception as e:
        timestamp = datetime.utcnow().isoformat()
        error_type = type(e).__name__
        log_error_to_file(smiles, error_type, timestamp, source_hash, excluded_path)
        return {
            "smiles": smiles,
            "status": "failed",
            "error_type": error_type,
            "reason": str(e)
        }

def calculate_descriptors_batch(
    df: pd.DataFrame,
    smiles_col: str = "canonical_smiles",
    excluded_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Calculate descriptors for a batch of molecules.
    Returns a DataFrame with original columns + descriptors.
    Excludes failed molecules from the main result but logs them.
    """
    if excluded_path is None:
        excluded_path = PROCESSED_DIR / "excluded_molecules.csv"

    source_hash = calculate_file_hash(get_data_path())
    
    results = []
    valid_rows = []

    for idx, row in df.iterrows():
        smiles = row[smiles_col]
        if not isinstance(smiles, str) or pd.isna(smiles):
            continue

        try:
            mol = validate_molecule(smiles)
            if mol is None:
                # Invalid SMILES, log and skip
                timestamp = datetime.utcnow().isoformat()
                log_error_to_file(smiles, "InvalidSMILES", timestamp, source_hash, excluded_path)
                continue

            res = calculate_descriptors_for_molecule(mol, smiles, source_hash, excluded_path)
            results.append(res)
            
            if res["status"] == "success":
                valid_rows.append(idx)
        except Exception as e:
            # Catch-all for unexpected errors
            timestamp = datetime.utcnow().isoformat()
            error_type = type(e).__name__
            log_error_to_file(smiles, error_type, timestamp, source_hash, excluded_path)

    # Create result DataFrame
    if not results:
        return pd.DataFrame()

    result_df = pd.DataFrame(results)
    
    # Merge back with original data for successful rows only
    # Filter original df to valid indices
    valid_df = df.iloc[valid_rows].reset_index(drop=True)
    
    # Ensure result_df has same order (it should if we appended in order)
    # Join descriptors to valid rows
    final_df = pd.concat([valid_df, result_df[result_df['status'] == 'success'].drop(columns=['status', 'smiles'])], axis=1)
    
    return final_df

def check_gate_status() -> bool:
    """Check if the data availability gate passed."""
    gate_file = DATA_DIR / "gate_status.json"
    if not gate_file.exists():
        return False
    with open(gate_file, 'r') as f:
        data = json.load(f)
    return data.get("status") == "PASS"

def main():
    """Main entry point for descriptor calculation."""
    logger = get_logger("descriptors")
    log_operation("calculate_descriptors", task="T015")

    if not check_gate_status():
        logger.info("Gate not passed, skipping descriptor calculation.")
        sys.exit(0)

    input_path = get_data_path()
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    logger.info("Calculating descriptors...")
    result_df = calculate_descriptors_batch(df)

    output_path = PROCESSED_DIR / "descriptors_calculated.csv"
    if not result_df.empty:
        result_df.to_csv(output_path, index=False)
        logger.info(f"Saved descriptors to {output_path}")
    else:
        logger.warning("No valid molecules found to calculate descriptors.")

    logger.info("Descriptor calculation complete.")

if __name__ == "__main__":
    main()
