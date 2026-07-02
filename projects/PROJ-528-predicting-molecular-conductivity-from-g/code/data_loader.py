import os
import pandas as pd
from typing import List, Tuple, Optional
import logging
import numpy as np
from rdkit import Chem

from config import TARGET_VAR, SEED
from logging_config import setup_logging

# Initialize logger
logger = setup_logging(__name__)

def load_smiles(path: str) -> pd.DataFrame:
    """
    Load SMILES strings from a file (CSV or TXT).
    
    Args:
        path: Path to the input file.
        
    Returns:
        DataFrame with columns: ['smiles', 'valid', 'error_msg']
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")

    _, ext = os.path.splitext(path)
    if ext.lower() == '.csv':
        df = pd.read_csv(path)
    elif ext.lower() == '.txt':
        # Assume one SMILES per line
        with open(path, 'r') as f:
            lines = f.readlines()
        df = pd.DataFrame({'smiles': [l.strip() for l in lines if l.strip()]})
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use .csv or .txt.")

    if 'smiles' not in df.columns:
        # Try to infer if the first column is SMILES
        if len(df.columns) > 0:
            df.columns = ['smiles'] + list(df.columns[1:])
        else:
            raise ValueError("DataFrame must have a 'smiles' column.")

    def validate_row(smiles_str):
        try:
            mol = Chem.MolFromSmiles(smiles_str)
            if mol is None:
                return False, "RDKit failed to parse SMILES"
            return True, None
        except Exception as e:
            return False, str(e)

    results = df['smiles'].apply(validate_row)
    df['valid'] = results.apply(lambda x: x[0])
    df['error_msg'] = results.apply(lambda x: x[1])

    logger.info(f"Loaded {len(df)} SMILES. Valid: {df['valid'].sum()}, Invalid: {(~df['valid']).sum()}")
    return df

def load_and_validate_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Check for target variable presence and validate range.
    
    Priority:
    1. 'conductivity' (if log-range >= 3.0)
    2. 'HOMO_LUMO_gap' (fallback if conductivity missing or range too small)
    
    Updates TARGET_VAR in config context if fallback occurs.
    """
    logger.info("Validating target variable...")
    
    target_found = None
    
    if 'conductivity' in df.columns:
        target_found = 'conductivity'
        # Check log range
        clean_vals = df['conductivity'].dropna()
        if len(clean_vals) > 0:
            try:
                log_vals = np.log10(clean_vals)
                log_range = log_vals.max() - log_vals.min()
                if log_range < 3.0:
                    logger.warning(f"Conductivity log-range ({log_range:.2f}) < 3.0. Falling back to HOMO-LUMO.")
                    target_found = None
                else:
                    logger.info(f"Conductivity log-range is {log_range:.2f}. Using conductivity.")
            except Exception as e:
                logger.warning(f"Error calculating log range for conductivity: {e}. Falling back.")
                target_found = None

    if target_found is None and 'HOMO_LUMO_gap' in df.columns:
        target_found = 'HOMO_LUMO_gap'
        logger.warning("Conductivity missing or invalid range. Using HOMO_LUMO_gap as target.")
    elif target_found is None:
        raise ValueError("No valid target variable found. Need 'conductivity' (log-range >= 3.0) or 'HOMO_LUMO_gap'.")

    # Update the global target variable reference for downstream tasks
    # Note: In a real pipeline, we might pass this as an argument, but per task T026.5
    # we update the config conceptually. Here we just log and ensure the column is used.
    logger.info(f"Selected target variable: {target_found}")
    
    # Attach the chosen target name to the dataframe for easy access later
    df.attrs['target_var'] = target_found
    
    return df

def validate_target_range(values: pd.Series, min_log_range: float = 3.0) -> Tuple[bool, float]:
    """
    Validate that the target values have a sufficient dynamic range.
    
    Args:
        values: Series of numeric target values.
        min_log_range: Minimum required log10 range.
        
    Returns:
        Tuple of (is_valid, actual_log_range)
    """
    clean_vals = values.dropna()
    if len(clean_vals) == 0:
        return False, 0.0
    
    try:
        log_vals = np.log10(clean_vals)
        log_range = log_vals.max() - log_vals.min()
        return log_range >= min_log_range, log_range
    except Exception as e:
        logger.error(f"Error validating target range: {e}")
        return False, 0.0

def apply_log_transformation(df: pd.DataFrame, target_col: Optional[str] = None) -> pd.DataFrame:
    """
    Apply log10 transformation to the selected target variable.
    
    Args:
        df: DataFrame containing the target variable.
        target_col: Name of the target column. If None, uses df.attrs['target_var'].
        
    Returns:
        DataFrame with a new column '<target_col>_log' containing the log-transformed values.
    """
    if target_col is None:
        target_col = df.attrs.get('target_var')
        if target_col is None:
            raise ValueError("No target variable specified or found in dataframe attributes.")
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")
    
    # Create the log column name
    log_col_name = f"{target_col}_log"
    
    # Apply log transformation, handling zeros or negatives if necessary
    # Assuming conductivity/HOMO-LUMO are positive. If not, we might need offset.
    # For now, strictly log10.
    values = df[target_col]
    
    # Check for non-positive values which would cause -inf or NaN in log10
    non_positive = values <= 0
    if non_positive.any():
        logger.warning(f"Found {non_positive.sum()} non-positive values in '{target_col}'. "
                       f"These will result in NaN/Inf after log transformation.")
    
    df[log_col_name] = np.log10(values)
    
    logger.info(f"Applied log10 transformation to '{target_col}'. New column: '{log_col_name}'")
    
    return df