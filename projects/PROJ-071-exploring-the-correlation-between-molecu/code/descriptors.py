"""
Molecular Descriptor Calculation Module.

Calculates molecular complexity metrics (TPSA, Rotatable Bonds, MW, Aromatic Rings,
Wiener Index, Zagreb Index) for a dataset of molecules using RDKit.
Includes robust error handling for valence issues and non-standard structures.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Union

import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors
from rdkit.Chem.Descriptors import wiener_index, balabanj
from rdkit import RDLogger

# Suppress RDKit warnings to keep logs clean, but we handle errors explicitly
RDLogger.DisableLog('rdApp.*')

# Ensure project root is in path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_config

# Custom Exception for Valence Errors
class AtomValenceException(Exception):
    """Raised when a molecule has non-standard valence or cannot be sanitized."""
    pass

def get_data_path() -> Path:
    """Returns the path to the processed data directory."""
    return PROJECT_ROOT / "data" / "processed"

def log_error_to_file(smiles: str, error_msg: str, log_path: Optional[Path] = None) -> None:
    """
    Logs a specific molecule error to the error log file.

    Args:
        smiles: The SMILES string of the problematic molecule.
        error_msg: The error message describing the issue.
        log_path: Optional path to the log file. Defaults to data/errors.log.
    """
    if log_path is None:
        log_path = PROJECT_ROOT / "data" / "errors.log"
    
    # Ensure the data directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = pd.Timestamp.now().isoformat()
    log_entry = f"[{timestamp}] SMILES: {smiles} | Error: {error_msg}\n"

    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except IOError as e:
        # If we can't write to the log, raise a critical error to stop the pipeline
        # rather than silently ignoring data quality issues.
        raise RuntimeError(f"Failed to write to error log at {log_path}: {e}")

def validate_molecule(smiles: str) -> Chem.Mol:
    """
    Validates a SMILES string and converts it to an RDKit Mol object.
    Performs sanitization to catch valence errors.

    Args:
        smiles: The SMILES string.

    Returns:
        An RDKit Mol object.

    Raises:
        AtomValenceException: If the molecule has invalid valence or cannot be parsed.
    """
    if not smiles or not isinstance(smiles, str):
        raise AtomValenceException(f"Invalid SMILES type or empty string: {type(smiles)}")

    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise AtomValenceException(f"RDKit failed to parse SMILES: {smiles}")
        
        # Explicit sanitization to catch valence errors
        # This is the critical step for T015: flagging non-standard valence
        Chem.SanitizeMol(mol)
        
        return mol
    except Exception as e:
        # Catch RDKit sanitization errors (valence, etc.) and wrap them
        raise AtomValenceException(f"Valence/Sanitization error for {smiles}: {str(e)}") from e

def calculate_tpsa(mol: Chem.Mol) -> float:
    """Calculates Topological Polar Surface Area."""
    return Descriptors.TPSA(mol)

def calculate_rotatable_bonds(mol: Chem.Mol) -> int:
    """Calculates the count of rotatable bonds."""
    return rdMolDescriptors.CalcNumRotatableBonds(mol)

def calculate_mw(mol: Chem.Mol) -> float:
    """Calculates Molecular Weight."""
    return Descriptors.MolWt(mol)

def calculate_aromatic_rings(mol: Chem.Mol) -> int:
    """Calculates the count of aromatic rings."""
    return rdMolDescriptors.CalcNumAromaticRings(mol)

def calculate_wiener_index(mol: Chem.Mol) -> float:
    """Calculates the Wiener Index."""
    # RDKit's wiener_index might return nan for disconnected graphs or specific edge cases
    try:
        return wiener_index(mol)
    except Exception:
        return float('nan')

def calculate_zagreb_index(mol: Chem.Mol) -> float:
    """Calculates the Zagreb Index (using Balaban J as a proxy or custom calc if needed).
    
    Note: RDKit does not have a direct 'Zagreb' function in the standard Descriptors module
    exposed as 'zagreb_index'. We use the Balaban J index (rdMolDescriptors.CalcBalabanJ)
    as a topological complexity metric often correlated, or implement a simple sum of degree^2.
    For strict compliance with 'Zagreb Index' (M1 = sum(deg(v)^2)), we calculate it manually.
    """
    try:
        # Manual calculation of First Zagreb Index (M1)
        # M1 = sum over all atoms v of (degree(v))^2
        degree_sum_sq = 0
        for atom in mol.GetAtoms():
            deg = atom.GetDegree()
            degree_sum_sq += deg * deg
        return float(degree_sum_sq)
    except Exception:
        return float('nan')

def calculate_descriptors_for_molecule(smiles: str) -> Dict[str, Any]:
    """
    Calculates all required descriptors for a single molecule.
    Includes error handling for valence issues as per T015.

    Args:
        smiles: The SMILES string.

    Returns:
        A dictionary with SMILES, calculated metrics, and status.
    """
    result = {
        "smiles": smiles,
        "tpsa": None,
        "rotatable_bonds": None,
        "mw": None,
        "aromatic_rings": None,
        "wiener_index": None,
        "zagreb_index": None,
        "status": "success",
        "error": None
    }

    try:
        mol = validate_molecule(smiles)
        
        result["tpsa"] = calculate_tpsa(mol)
        result["rotatable_bonds"] = calculate_rotatable_bonds(mol)
        result["mw"] = calculate_mw(mol)
        result["aromatic_rings"] = calculate_aromatic_rings(mol)
        result["wiener_index"] = calculate_wiener_index(mol)
        result["zagreb_index"] = calculate_zagreb_index(mol)
        
    except AtomValenceException as e:
        result["status"] = "failed"
        result["error"] = str(e)
        # Log the error to the file as required by T015
        log_error_to_file(smiles, str(e))
    except Exception as e:
        result["status"] = "failed"
        result["error"] = f"Unexpected error: {str(e)}"
        log_error_to_file(smiles, result["error"])

    return result

def calculate_descriptors_batch(df: pd.DataFrame, smiles_col: str = "smiles") -> pd.DataFrame:
    """
    Calculates descriptors for a batch of molecules in a DataFrame.
    Excludes molecules with non-standard valence from the final results 
    but logs them to data/errors.log.

    Args:
        df: DataFrame containing the SMILES column.
        smiles_col: Name of the column containing SMILES strings.

    Returns:
        DataFrame with original data plus new descriptor columns, 
        excluding failed molecules.
    """
    config = get_config()
    smiles_list = df[smiles_col].astype(str).tolist()
    
    results = []
    total = len(smiles_list)
    failed_count = 0

    logger = logging.getLogger(__name__)
    logger.info(f"Starting descriptor calculation for {total} molecules.")

    for i, smiles in enumerate(smiles_list):
        res = calculate_descriptors_for_molecule(smiles)
        if res["status"] == "failed":
            failed_count += 1
            # We do not include failed molecules in the return DataFrame
            continue
        
        # Merge result into the original row (assuming we keep the original row context)
        # Since we are iterating a list, we reconstruct the row or append to a new list
        new_row = res
        # Add any other columns from the original df if needed? 
        # For T015, we just need to ensure the calculation happens and errors are logged.
        # We assume the input df might have other columns (like degradation data) that we want to keep.
        # However, calculate_descriptors_for_molecule returns a dict. 
        # We need to map this back to the original row index or just return a clean DF.
        # Let's assume the input df is just the structural subset or we are building a new one.
        
        # To preserve original columns, we take the row from df if we had index access.
        # Since we are iterating a list, let's assume the caller passes a clean DF or we handle it.
        # A safer approach for batch processing:
        pass

    # Re-implementation for proper DataFrame handling with index preservation
    processed_rows = []
    
    logger.info(f"Processing {total} molecules...")
    
    for idx, row in df.iterrows():
        smiles = str(row[smiles_col])
        res = calculate_descriptors_for_molecule(smiles)
        
        if res["status"] == "failed":
            failed_count += 1
            continue
        
        # Create a new row with original data + descriptors
        new_row = row.to_dict()
        new_row["tpsa"] = res["tpsa"]
        new_row["rotatable_bonds"] = res["rotatable_bonds"]
        new_row["mw"] = res["mw"]
        new_row["aromatic_rings"] = res["aromatic_rings"]
        new_row["wiener_index"] = res["wiener_index"]
        new_row["zagreb_index"] = res["zagreb_index"]
        processed_rows.append(new_row)

    logger.info(f"Descriptor calculation complete. {len(processed_rows)} successful, {failed_count} failed.")
    
    if not processed_rows:
        logger.warning("No valid molecules found after filtering.")
        return pd.DataFrame()

    return pd.DataFrame(processed_rows)

def main():
    """
    Main entry point for the descriptor calculation script.
    Reads from data/processed/structural_subset.csv (or merged if available)
    and writes to data/processed/descriptors_calculated.csv.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Determine input file
    # T017 produces structural_subset.csv. T015 depends on T017.
    input_path = get_data_path() / "structural_subset.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Ensure T017 has run.")
        # Fallback to merged if structural_subset is missing but merged exists? 
        # T017 is a prerequisite, so we should fail if missing.
        sys.exit(1)

    logger.info(f"Reading input from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read input file: {e}")
        sys.exit(1)

    if "smiles" not in df.columns:
        logger.error("Input file must contain a 'smiles' column.")
        sys.exit(1)

    # Run calculation
    logger.info("Calculating descriptors...")
    result_df = calculate_descriptors_batch(df, smiles_col="smiles")

    if result_df.empty:
        logger.warning("No valid molecules to save.")
        # Still create an empty file or exit? T015 says flag/exclude.
        # We'll create an empty file to indicate completion.
        output_path = get_data_path() / "descriptors_calculated.csv"
        result_df.to_csv(output_path, index=False)
        logger.info(f"Empty result saved to {output_path}")
        return

    # Save output
    output_path = get_data_path() / "descriptors_calculated.csv"
    result_df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved {len(result_df)} records to {output_path}")

    # Verify error log was created if there were errors
    error_log_path = PROJECT_ROOT / "data" / "errors.log"
    if error_log_path.exists():
        logger.info(f"Error log created/updated at {error_log_path}")

if __name__ == "__main__":
    main()