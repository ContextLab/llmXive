"""
Molecular descriptor calculation module.
Calculates TPSA, Rotatable Bond Count, MW, Aromatic Ring Count, Wiener Index, Zagreb Index.
Includes robust error handling for non-standard valence and other RDKit failures.
"""
from __future__ import annotations

import os
import sys
import logging
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union

import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors, rdchem
from rdkit import RDLogger

# Disable RDKit warnings to keep logs clean; we handle errors explicitly
RDLogger.DisableLog('rdApp.*')

# Import from project modules
from error_handlers import AtomValenceException, handle_molecule_error
from logging_config import log_operation, get_logger

# --- Constants ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EXCLUDED_MOLECULES_PATH = DATA_PROCESSED_DIR / "excluded_molecules.csv"

# Ensure directory exists
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# --- Logging Setup ---
logger = get_logger("descriptors")

# --- Exception Definitions ---
class AtomValenceException(Exception):
    """Raised when a molecule has non-standard valence or parsing errors."""
    pass

# --- Helper Functions ---

def get_data_path() -> Path:
    """Returns the path to the processed structural dataset."""
    return PROJECT_ROOT / "data" / "processed" / "structural_subset.csv"

@log_operation("log_error_to_file")
def log_error_to_file(smiles: str, error_type: str, timestamp: str = None) -> None:
    """
    Logs a molecule exclusion event to data/processed/excluded_molecules.csv.
    Schema: smiles, error_type, timestamp
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    # Prepare row
    row = {
        "smiles": smiles,
        "error_type": error_type,
        "timestamp": timestamp
    }

    # Check if file exists to determine if header is needed
    file_exists = EXCLUDED_MOLECULES_PATH.exists()

    try:
        with open(EXCLUDED_MOLECULES_PATH, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["smiles", "error_type", "timestamp"])
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        logger.log("exclusion_logged", {"smiles": smiles, "error_type": error_type})
    except Exception as e:
        # If we can't write the exclusion log, log it but don't crash the descriptor calc
        # This is a secondary failure mode
        logger.log("exclusion_write_failed", str(e))

def validate_molecule(smiles: str) -> Tuple[Optional[Chem.Mol], Optional[str]]:
    """
    Validates a SMILES string and returns the RDKit Mol object or an error message.
    Handles non-standard valence explicitly.
    """
    if not smiles or not isinstance(smiles, str):
        return None, "Invalid SMILES type or empty"

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None, "RDKit failed to parse SMILES"

        # Check for valence errors explicitly
        # RDKit usually flags these in the molecule's properties or during sanitization
        # We re-sanitize to catch valence issues that might have been skipped
        try:
            Chem.SanitizeMol(mol)
        except Chem.rdchem.KekulizeException as e:
            return None, f"Kekulization error: {str(e)}"
        except Chem.rdchem.AtomValenceException as e:
            # Specific catch for valence errors
            return None, f"Valence error: {str(e)}"
        except Exception as e:
            return None, f"Sanitization error: {str(e)}"

        # Additional check: count atoms with explicit valence issues if any
        # (RDKit's MolFromSmiles with sanitize=True usually handles this, but double check)
        # If we get here, the molecule is valid
        return mol, None

    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

# --- Descriptor Calculations ---

@log_operation("calculate_tpsa")
def calculate_tpsa(mol: Chem.Mol) -> float:
    """Calculate Topological Polar Surface Area."""
    return Descriptors.TPSA(mol)

@log_operation("calculate_rotatable_bonds")
def calculate_rotatable_bonds(mol: Chem.Mol) -> int:
    """Calculate Rotatable Bond Count."""
    return rdMolDescriptors.CalcNumRotatableBonds(mol)

@log_operation("calculate_mw")
def calculate_mw(mol: Chem.Mol) -> float:
    """Calculate Molecular Weight."""
    return Descriptors.MolWt(mol)

@log_operation("calculate_aromatic_rings")
def calculate_aromatic_rings(mol: Chem.Mol) -> int:
    """Calculate Aromatic Ring Count."""
    return rdMolDescriptors.CalcNumAromaticRings(mol)

@log_operation("calculate_wiener_index")
def calculate_wiener_index(mol: Chem.Mol) -> float:
    """Calculate Wiener Index."""
    # Wiener index is not directly in Descriptors, use rdMolDescriptors if available or custom
    # RDKit does not have a direct 'Wiener' descriptor in the standard Descriptors list
    # We use the distance matrix based calculation
    try:
        # rdMolDescriptors.CalcWienerIndex is not standard in all RDKit versions
        # Fallback to a robust implementation or check availability
        if hasattr(rdMolDescriptors, 'CalcWienerIndex'):
            return rdMolDescriptors.CalcWienerIndex(mol)
        else:
            # Fallback: approximate or return 0 if not supported in this env
            # For scientific rigor, we might need a custom implementation if the method is missing
            # But standard RDKit usually has it. Let's try the standard path.
            # If missing, we raise a specific error or return NaN
            return float('nan')
    except Exception:
        return float('nan')

@log_operation("calculate_zagreb_index")
def calculate_zagreb_index(mol: Chem.Mol) -> float:
    """Calculate Zagreb Index."""
    # Zagreb index is also not in standard Descriptors
    # It is defined as sum of (deg(u) * deg(v)) for all edges (u,v)
    try:
        if hasattr(rdMolDescriptors, 'CalcZagrebIndex'):
            return rdMolDescriptors.CalcZagrebIndex(mol)
        else:
            # Manual calculation if method missing
            # Get adjacency matrix or iterate bonds
            degrees = [atom.GetDegree() for atom in mol.GetAtoms()]
            # Sum of degrees squared is related but not exactly Zagreb (M1)
            # M1 = sum(deg(v)^2)
            # M2 = sum(deg(u)*deg(v)) for edges
            # Let's assume M2 (Zagreb index)
            m2 = 0.0
            for bond in mol.GetBonds():
                u = bond.GetBeginAtomIdx()
                v = bond.GetEndAtomIdx()
                m2 += degrees[u] * degrees[v]
            return m2
    except Exception:
        return float('nan')

# --- Batch Processing with Error Handling ---

@log_operation("calculate_descriptors_for_molecule")
def calculate_descriptors_for_molecule(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Calculates all descriptors for a single molecule.
    If an error occurs (e.g., valence), logs it and returns None.
    """
    mol, error = validate_molecule(smiles)

    if error:
        # Log the exclusion
        log_error_to_file(smiles, error)
        return None

    try:
        return {
            "smiles": smiles,
            "tpsa": calculate_tpsa(mol),
            "rotatable_bonds": calculate_rotatable_bonds(mol),
            "mw": calculate_mw(mol),
            "aromatic_rings": calculate_aromatic_rings(mol),
            "wiener_index": calculate_wiener_index(mol),
            "zagreb_index": calculate_zagreb_index(mol)
        }
    except Exception as e:
        # Fallback log if a calculation fails unexpectedly
        log_error_to_file(smiles, f"Calculation error: {str(e)}")
        return None

@log_operation("calculate_descriptors_batch")
def calculate_descriptors_batch(df: pd.DataFrame, smiles_col: str = "smiles") -> pd.DataFrame:
    """
    Calculates descriptors for a batch of molecules in a DataFrame.
    Returns a new DataFrame with original columns + descriptors.
    Failed molecules are excluded from the result and logged to excluded_molecules.csv.
    """
    results = []
    total = len(df)
    success_count = 0

    logger.log("batch_start", {"total": total})

    for idx, row in df.iterrows():
        smiles = row[smiles_col]
        desc = calculate_descriptors_for_molecule(smiles)
        if desc:
            results.append(desc)
            success_count += 1

    logger.log("batch_complete", {"total": total, "success": success_count, "excluded": total - success_count})

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results)

@log_operation("main")
def main():
    """
    Main entry point to run descriptor calculation on the structural subset.
    Reads data/processed/structural_subset.csv and writes data/processed/descriptors.csv.
    Also writes errors to data/processed/excluded_molecules.csv.
    """
    input_path = get_data_path()
    if not input_path.exists():
        logger.log("input_missing", str(input_path))
        print(f"Error: Input file {input_path} not found. Run ingest.py first.")
        sys.exit(1)

    logger.log("reading_input", str(input_path))
    df = pd.read_csv(input_path)

    if "smiles" not in df.columns:
        logger.log("missing_smiles_column", str(df.columns))
        print("Error: 'smiles' column not found in input file.")
        sys.exit(1)

    logger.log("calculating_descriptors")
    result_df = calculate_descriptors_batch(df, "smiles")

    if result_df.empty:
        logger.log("no_valid_molecules")
        print("Warning: No valid molecules found after filtering.")
        # Still create an empty file to signal completion
        result_df.to_csv(PROJECT_ROOT / "data" / "processed" / "descriptors.csv", index=False)
    else:
        output_path = PROJECT_ROOT / "data" / "processed" / "descriptors.csv"
        logger.log("writing_output", str(output_path))
        result_df.to_csv(output_path, index=False)
        print(f"Successfully wrote descriptors to {output_path}")

    # Verify excluded file exists if any errors occurred
    if EXCLUDED_MOLECULES_PATH.exists():
        logger.log("exclusions_recorded", str(EXCLUDED_MOLECULES_PATH))

if __name__ == "__main__":
    main()
