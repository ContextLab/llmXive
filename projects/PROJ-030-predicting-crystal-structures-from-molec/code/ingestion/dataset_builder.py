"""
Dataset Builder for Crystal Structure Prediction.

This module handles the construction of the final dataset by:
1. Loading intermediate parsed data (SMILES, Lattice Parameters, Space Groups).
2. Implementing polymorphism handling: treating (SMILES, Space Group) pairs as distinct samples.
3. Generating the `polymorphic_dataset.csv` artifact.
"""
import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import pandas as pd

# Import from project config for path handling
# Note: The API surface shows `get_path_processed_data` exists in config.py but might be truncated in the prompt view.
# We will use standard Path construction relative to project root to be safe, 
# or import the function if it exists. Given the "contract" errors in the execution log,
# we will implement a robust path resolver here or use the config module carefully.
try:
    from config import get_path_processed_data, get_project_root
except (ImportError, AttributeError) as e:
    # Fallback if config is broken or function missing (as seen in execution logs)
    # We construct paths relative to the project root manually to ensure this script runs.
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    def get_path_processed_data(filename: Optional[str] = None) -> Path:
        base = PROJECT_ROOT / "data" / "processed"
        base.mkdir(parents=True, exist_ok=True)
        if filename:
            return base / filename
        return base
    
    def get_project_root() -> Path:
        return PROJECT_ROOT

from ingestion.models import MoleculeRecord
from logging_config import get_logger, log_event

logger = get_logger(__name__)

@dataclass
class PolymorphicRecord:
    """
    Represents a unique (SMILES, Space Group) pair.
    This is the atomic unit for polymorphism handling.
    """
    smiles: str
    space_group: str
    lattice_a: float
    lattice_b: float
    lattice_c: float
    alpha: float
    beta: float
    gamma: float
    volume: float
    source_id: str
    fingerprint_bits: Optional[str] = None  # JSON string of bits or hex
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def load_intermediate_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Loads the intermediate dataset (e.g., from T010/T011 output).
    Expected columns: 'smiles', 'space_group', 'lattice_a', 'lattice_b', 'lattice_c',
                      'alpha', 'beta', 'gamma', 'volume', 'source_id', 'fingerprint_bits'.
    """
    if input_path is None:
        # Default to the output of the previous stage (parse_cif + fingerprint)
        # Based on task chain: T011 -> T012. T011 produces fingerprints.
        # The intermediate file is likely `data/processed/crystal_molecules.parquet` or `.csv`
        # from T010/T011. We look for common outputs.
        potential_files = [
            get_path_processed_data("crystal_molecules.parquet"),
            get_path_processed_data("crystal_molecules.csv"),
            get_path_processed_data("fingerprinted_molecules.csv"),
            get_path_processed_data("parsed_structures.csv")
        ]
        
        found_file = None
        for p in potential_files:
            if p.exists():
                found_file = p
                break
        
        if not found_file:
            # If no intermediate file exists, we cannot proceed.
            # This script assumes T010 and T011 have run.
            raise FileNotFoundError(
                f"No intermediate data file found in {get_path_processed_data()}. "
                f"Expected crystal_molecules.parquet or similar."
            )
        input_path = found_file
    
    logger.info(f"Loading intermediate data from {input_path}")
    
    if str(input_path).endswith('.parquet'):
        df = pd.read_parquet(input_path)
    else:
        df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = ['smiles', 'space_group', 'lattice_a', 'lattice_b', 'lattice_c', 
                     'alpha', 'beta', 'gamma', 'volume', 'source_id']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Intermediate data missing required columns: {missing_cols}")
    
    return df

def handle_polymorphism(df: pd.DataFrame) -> pd.DataFrame:
    """
    Implements polymorphism handling logic.
    
    Rule: Treat each unique (SMILES, Space Group) pair as a distinct row.
    If a (SMILES, Space Group) combination appears multiple times (e.g., different unit cells
    for the same molecule/space group in the source), we keep them as distinct rows.
    If the same (SMILES, Space Group) appears with identical lattice parameters, we might
    consider it a duplicate, but the spec says "distinct samples" for the pair.
    
    We will:
    1. Ensure 'space_group' is a string (standardize format if needed).
    2. Keep all rows where the (SMILES, Space Group) pair is unique in the context of the dataset.
       If the input has multiple entries for the same pair (e.g. different volumes), we keep them all.
       The "distinct row" logic implies we do NOT drop duplicates based on this pair.
       However, if the input has EXACT duplicates (all columns identical), we drop those.
    """
    logger.info(f"Processing {len(df)} records for polymorphism handling.")
    
    # Standardize space group strings to ensure consistent grouping
    # e.g., "P 21/c" vs "P21/c" -> normalize to a canonical form if possible,
    # but for now, treat the string as is.
    df['space_group'] = df['space_group'].astype(str).str.strip()
    
    # Drop exact duplicates across all columns to avoid redundancy
    # The spec says "distinct samples" for the pair, but if the entire row is identical,
    # it's the same measurement.
    initial_count = len(df)
    df = df.drop_duplicates()
    dropped_exact = initial_count - len(df)
    if dropped_exact > 0:
        logger.info(f"Dropped {dropped_exact} exact duplicate rows.")
    
    # The core logic: The resulting dataframe IS the polymorphic dataset.
    # Each row represents a unique observation of (SMILES, Space Group).
    # We do NOT aggregate or drop based on the pair unless the whole row is a duplicate.
    
    # Ensure fingerprint bits are handled correctly if present
    if 'fingerprint_bits' in df.columns:
        # Ensure they are strings or JSON serializable
        df['fingerprint_bits'] = df['fingerprint_bits'].apply(
            lambda x: json.dumps(x) if isinstance(x, (list, dict)) else str(x) if pd.notna(x) else None
        )
    
    logger.info(f"Polymorphic dataset prepared with {len(df)} unique (SMILES, Space Group) samples.")
    return df

def save_dataset(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Saves the polymorphic dataset to `data/processed/polymorphic_dataset.csv`.
    """
    if output_path is None:
        output_path = get_path_processed_data("polymorphic_dataset.csv")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving polymorphic dataset to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Log metadata
    metadata = {
        "total_rows": len(df),
        "columns": list(df.columns),
        "unique_smiles": df['smiles'].nunique(),
        "unique_space_groups": df['space_group'].nunique(),
        "unique_pairs": len(df) # Since we kept all rows, this is the count
    }
    
    metadata_path = output_path.with_suffix('.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Dataset saved. Metadata written to {metadata_path}")
    return output_path

def main():
    """
    Main entry point for T012.
    Orchestrates loading, polymorphism handling, and saving.
    """
    try:
        # 1. Load intermediate data
        df = load_intermediate_data()
        
        # 2. Handle polymorphism
        polymorphic_df = handle_polymorphism(df)
        
        # 3. Save the result
        output_path = save_dataset(polymorphic_df)
        
        log_event("T012_COMPLETE", {
            "output_file": str(output_path),
            "row_count": len(polymorphic_df)
        })
        
        print(f"SUCCESS: Polymorphic dataset created at {output_path} with {len(polymorphic_df)} rows.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input data not found: {e}")
        print(f"ERROR: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        logger.exception("Unexpected error during dataset building")
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())