"""
Data ingestion module for loading and filtering diffusion datasets.

This module handles:
- Loading CSV files
- Filtering for FCC crystal structure and self-diffusion mode
- Unit standardization to eV/atom
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import logging

from config import DATA_DIR
from utils.logging import get_logger

logger = get_logger(__name__)

# Conversion constant: 1 eV/atom = 96.485 kJ/mol
EV_TO_KJ_PER_MOL = 96.485

def load_and_filter(file_path: str, output_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load a CSV file, filter for FCC self-diffusion entries, and standardize units.
    
    Args:
        file_path: Path to the input CSV file
        output_path: Optional path to save the filtered results
    
    Returns:
        Filtered DataFrame containing only FCC self-diffusion entries
    
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If required columns are missing
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    logger.info(f"Loading data from {file_path}")
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to read CSV file: {e}")
        raise
    
    # Validate required columns
    required_columns = ['element', 'crystal_structure', 'diffusion_mode', 'activation_energy_eV', 'unit']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    
    # Filter for FCC crystal structure (case-insensitive)
    fcc_mask = df['crystal_structure'].astype(str).str.upper().str.strip() == 'FCC'
    df_fcc = df[fcc_mask].copy()
    logger.info(f"Filtered to {len(df_fcc)} FCC rows (from {len(df)})")
    
    # Filter for self-diffusion mode (case-insensitive)
    self_mask = df_fcc['diffusion_mode'].astype(str).str.lower().str.strip() == 'self'
    df_filtered = df_fcc[self_mask].copy()
    logger.info(f"Filtered to {len(df_filtered)} self-diffusion rows (from {len(df_fcc)})")
    
    # Standardize units to eV/atom
    df_filtered = _standardize_units(df_filtered)
    
    # Save to output if specified
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df_filtered.to_csv(output_path, index=False)
        logger.info(f"Saved filtered data to {output_path}")
    
    return df_filtered

def _standardize_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert activation energy to eV/atom if necessary.
    
    Supported units:
    - eV/atom: No conversion needed
    - kJ/mol: Divide by 96.485
    
    Args:
        df: DataFrame with 'activation_energy_eV' and 'unit' columns
    
    Returns:
        DataFrame with standardized units
    """
    df = df.copy()
    
    # Identify rows needing conversion
    kj_mask = df['unit'].astype(str).str.lower().str.strip() == 'kj/mol'
    
    if kj_mask.any():
        logger.info(f"Converting {kj_mask.sum()} rows from kJ/mol to eV/atom")
        df.loc[kj_mask, 'activation_energy_eV'] = df.loc[kj_mask, 'activation_energy_eV'] / EV_TO_KJ_PER_MOL
        df.loc[kj_mask, 'unit'] = 'eV/atom'
    
    # Normalize unit strings
    df['unit'] = df['unit'].astype(str).str.strip()
    
    # Validate all units are now eV/atom (case-insensitive check)
    valid_units = ['eV/atom', 'ev/atom']
    invalid_mask = ~df['unit'].str.lower().isin(valid_units)
    
    if invalid_mask.any():
        logger.warning(f"Found {invalid_mask.sum()} rows with unsupported units: {df.loc[invalid_mask, 'unit'].unique()}")
        # Normalize to standard format
        df.loc[df['unit'].str.lower() == 'ev/atom', 'unit'] = 'eV/atom'
    
    return df

def load_multiple_files(file_paths: list, output_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Load and combine multiple CSV files.
    
    Args:
        file_paths: List of paths to CSV files
        output_dir: Optional directory to save the combined results
    
    Returns:
        Combined DataFrame with all filtered entries
    """
    all_dfs = []
    
    for file_path in file_paths:
        try:
            df = load_and_filter(file_path)
            if len(df) > 0:
                all_dfs.append(df)
                logger.info(f"Loaded {len(df)} rows from {file_path}")
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            continue
    
    if not all_dfs:
        logger.warning("No valid data found in any input files")
        return pd.DataFrame()
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    logger.info(f"Combined {len(combined_df)} total rows from {len(all_dfs)} files")
    
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / 'combined_filtered.csv'
        combined_df.to_csv(output_path, index=False)
        logger.info(f"Saved combined data to {output_path}")
    
    return combined_df

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        result = load_and_filter(input_file, output_file)
        print(f"Filtered {len(result)} rows")
        if len(result) > 0:
            print(result.head())
    else:
        print("Usage: python ingestion.py <input_file> [output_file]")
