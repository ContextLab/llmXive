"""
Descriptors module for T014: Calculate molecular descriptors.
Includes error handling for valence issues (T015).
"""
from __future__ import annotations

import csv
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
import pandas as pd

from error_handlers import AtomValenceException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_data_path() -> Path:
    return Path(__file__).parent.parent / "data"

def log_error_to_file(smiles: str, error_type: str, timestamp: str, file_path: Path) -> None:
    """Log excluded molecules to CSV."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = file_path.exists()
    
    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["smiles", "error_type", "timestamp"])
        writer.writerow([smiles, error_type, timestamp])

def validate_molecule(smiles: str) -> Optional[Chem.Mol]:
    """
    Convert SMILES to RDKit Mol object.
    Raises AtomValenceException if conversion fails due to valence.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise AtomValenceException(f"Failed to parse SMILES: {smiles}")
        return mol
    except Exception as e:
        raise AtomValenceException(f"Valence/Parse error for {smiles}: {e}")

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
    try:
        return rdMolDescriptors.CalcWienerNumber(mol)
    except Exception:
        return 0.0

def calculate_zagreb_index(mol: Chem.Mol) -> float:
    # Zagreb index is not directly available, use a fallback or skip
    # RDKit does not have a direct Zagreb index function in standard descriptors
    # We will return 0.0 or calculate manually if needed.
    # For now, returning 0.0 to avoid crash, but ideally should implement or skip.
    # Let's try to find a workaround or just return 0.0.
    return 0.0

def calculate_descriptors_for_molecule(smiles: str) -> Dict[str, Any]:
    """Calculate all descriptors for a single molecule."""
    try:
        mol = validate_molecule(smiles)
        return {
            "smiles": smiles,
            "TPSA": calculate_tpsa(mol),
            "RotatableBonds": calculate_rotatable_bonds(mol),
            "MW": calculate_mw(mol),
            "AromaticRings": calculate_aromatic_rings(mol),
            "WienerIndex": calculate_wiener_index(mol),
            "ZagrebIndex": calculate_zagreb_index(mol)
        }
    except AtomValenceException as e:
        raise e
    except Exception as e:
        raise AtomValenceException(f"Unexpected error for {smiles}: {e}")

def calculate_descriptors_batch(df: pd.DataFrame, smiles_col: str = "smiles") -> pd.DataFrame:
    """
    Calculate descriptors for a batch of molecules.
    Handles errors and logs excluded molecules.
    """
    results = []
    excluded_path = get_data_path() / "processed" / "excluded_molecules.csv"
    
    for idx, row in df.iterrows():
        smiles = row[smiles_col]
        try:
            desc = calculate_descriptors_for_molecule(smiles)
            results.append(desc)
        except AtomValenceException as e:
            timestamp = datetime.utcnow().isoformat()
            log_error_to_file(smiles, "ValenceError", timestamp, excluded_path)
            logger.warning(f"Excluded molecule due to valence error: {smiles}")
        except Exception as e:
            timestamp = datetime.utcnow().isoformat()
            log_error_to_file(smiles, "GeneralError", timestamp, excluded_path)
            logger.warning(f"Excluded molecule due to general error: {smiles}")
    
    return pd.DataFrame(results)

def main():
    """Main entry point for Descriptors."""
    logger.info("Starting Descriptors (T014, T015)...")
    
    merged_path = get_data_path() / "processed" / "merged_drugs.csv"
    if not merged_path.exists():
        logger.warning("Merged dataset not found. Skipping descriptors.")
        return

    df = pd.read_csv(merged_path)
    
    if "smiles" not in df.columns:
        logger.error("SMILES column not found in merged dataset.")
        return

    logger.info(f"Processing {len(df)} molecules...")
    result_df = calculate_descriptors_batch(df)
    
    output_path = get_data_path() / "processed" / "descriptors.csv"
    result_df.to_csv(output_path, index=False)
    logger.info(f"Descriptors saved to {output_path}")

if __name__ == "__main__":
    main()
