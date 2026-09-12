import os
import sys
import time
import signal
from pathlib import Path
from typing import List, Optional, Dict, Any

import pandas as pd
import logging
from rdkit import Chem

# Import from sibling modules based on API surface
from utils.data_loader import fetch_nist_data, fetch_pubchem_data, fetch_mtr_data
from utils.logger import setup_logging, log_missing_data
from config import load_config

# Custom exceptions for timeout handling
class TimeoutError(Exception):
    pass

class MemoryLimitError(Exception):
    pass

def setup_timeout_handler(timeout_seconds: int):
    """Setup signal handler for timeout enforcement."""
    def handler(signum, frame):
        raise TimeoutError(f"TIMEOUT: Graph construction exceeded {timeout_seconds} seconds")
    
    # Only works on Unix-like systems
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(timeout_seconds)
    else:
        logging.warning("SIGALRM not available on this platform, timeout enforcement disabled")

def cancel_timeout_handler():
    """Cancel the timeout handler."""
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(0)

def parse_smiles_to_mol(smiles: str) -> Optional[Any]:
    """Parse SMILES string to RDKit Mol object."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol
    except Exception as e:
        logging.warning(f"Failed to parse SMILES '{smiles}': {e}")
        return None

def compute_descriptors(mol: Any) -> Dict[str, float]:
    """Compute basic molecular descriptors."""
    if mol is None:
        return {}
    
    # Compute basic descriptors
    descriptors = {
        'num_atoms': mol.GetNumAtoms(),
        'num_bonds': mol.GetNumBonds(),
        'mol_wt': sum(atom.GetMass() for atom in mol.GetAtoms()),
        'num_h_acceptors': sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() in [7, 8, 9]),
        'num_h_donors': sum(1 for atom in mol.GetAtoms() if atom.GetAtomicNum() == 7 and atom.GetTotalNumHs() > 0)
    }
    return descriptors

def handle_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Handle duplicate SMILES by aggregating targets using mean function."""
    if df.empty:
        return df
    
    # Group by SMILES and aggregate
    grouped = df.groupby('smiles').agg({
        'target': ['mean', 'count'],
        'source_id': lambda x: list(x)
    }).reset_index()
    
    # Flatten column names
    grouped.columns = ['smiles', 'target_mean', 'count', 'source_id']
    
    return grouped

def filter_missing_permeability(df: pd.DataFrame, target_col: str = 'target') -> pd.DataFrame:
    """Filter rows with missing permeability values and log reasons."""
    if df.empty:
        return df
    
    initial_count = len(df)
    
    # Filter out rows with missing target
    mask = df[target_col].notna()
    filtered_df = df[mask].copy()
    
    excluded_count = initial_count - len(filtered_df)
    if excluded_count > 0:
        log_missing_data(reason="Missing target variable", count=excluded_count)
        logging.info(f"Excluded {excluded_count} rows due to missing target variable")
    
    return filtered_df

def log_exclusion_statistics(exclusion_reasons: Dict[str, int], total_rows: int) -> None:
    """
    Log exclusion reasons and exclusion rate statistics.
    
    Args:
        exclusion_reasons: Dictionary mapping exclusion reason strings to counts
        total_rows: Total number of rows before filtering
    """
    if not exclusion_reasons:
        logging.info("No exclusions recorded.")
        return

    logging.info("=" * 60)
    logging.info("EXCLUSION STATISTICS")
    logging.info("=" * 60)
    
    total_excluded = sum(exclusion_reasons.values())
    exclusion_rate = (total_excluded / total_rows * 100) if total_rows > 0 else 0.0
    
    logging.info(f"Total rows processed: {total_rows}")
    logging.info(f"Total rows excluded: {total_excluded}")
    logging.info(f"Overall exclusion rate: {exclusion_rate:.2f}%")
    logging.info("-" * 40)
    logging.info("Exclusion breakdown by reason:")
    
    for reason, count in sorted(exclusion_reasons.items(), key=lambda x: x[1], reverse=True):
        rate = (count / total_rows * 100) if total_rows > 0 else 0.0
        logging.info(f"  - {reason}: {count} ({rate:.2f}%)")
    
    logging.info("=" * 60)

def ingest_pubchem_data(output_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Ingest PubChem data with logging for exclusion reasons and statistics.
    
    Args:
        output_dir: Directory to save processed data (optional)
        
    Returns:
        Processed DataFrame
    """
    logging.info("Starting PubChem data ingestion...")
    
    # Fetch data
    df = fetch_pubchem_data()
    
    if df is None or df.empty:
        logging.warning("PubChem data fetch returned empty or None.")
        return pd.DataFrame()
    
    # Track exclusions
    exclusion_reasons = {}
    initial_count = len(df)
    
    # 1. Filter missing SMILES
    if 'smiles' in df.columns:
        mask_smiles = df['smiles'].notna() & (df['smiles'] != '')
        excluded_smiles = initial_count - mask_smiles.sum()
        if excluded_smiles > 0:
            exclusion_reasons["Missing or empty SMILES"] = excluded_smiles
        df = df[mask_smiles]
    
    # 2. Parse SMILES and filter invalid
    valid_mols = []
    invalid_count = 0
    for idx, row in df.iterrows():
        mol = parse_smiles_to_mol(row['smiles'])
        if mol is not None:
            valid_mols.append(row)
        else:
            invalid_count += 1
    
    if invalid_count > 0:
        exclusion_reasons["Invalid SMILES (RDKit parse fail)"] = invalid_count
    
    df = pd.DataFrame(valid_mols) if valid_mols else pd.DataFrame()
    
    # 3. Filter missing permeability (target)
    if not df.empty and 'target' in df.columns:
        initial_target = len(df)
        df = filter_missing_permeability(df, target_col='target')
        excluded_target = initial_target - len(df)
        if excluded_target > 0 and "Missing target variable" not in exclusion_reasons:
            exclusion_reasons["Missing target variable"] = excluded_target
    
    # 4. Log exclusion statistics
    log_exclusion_statistics(exclusion_reasons, initial_count)
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "pubchem_processed.csv"
        df.to_csv(output_path, index=False)
        logging.info(f"Saved processed PubChem data to {output_path}")
    
    return df

def main():
    """Main entry point for ingestion pipeline."""
    # Load configuration
    config = load_config()
    timeout_seconds = config.get('TIMEOUT_GRAPHS', 1800)  # Default 30 mins
    
    # Setup logging
    setup_logging()
    
    # Setup timeout handler
    setup_timeout_handler(timeout_seconds)
    
    try:
        # Ingest PubChem as example for T016
        # In a full run, this would merge NIST, PubChem, MTR
        df_pubchem = ingest_pubchem_data(output_dir=Path("data/processed"))
        
        if not df_pubchem.empty:
            # Save deduplicated version
            df_dedup = handle_duplicates(df_pubchem)
            df_dedup.to_csv("data/processed/deduplicated.csv", index=False)
            logging.info("Saved deduplicated dataset.")
        
        logging.info("Ingestion pipeline completed successfully.")
        
    except TimeoutError as e:
        logging.error(str(e))
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error during ingestion: {e}", exc_info=True)
        sys.exit(1)
    finally:
        cancel_timeout_handler()

if __name__ == "__main__":
    main()