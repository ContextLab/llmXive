"""
Error handling module for molecular conductivity pipeline.
Implements FR-012: Error handling for invalid SMILES and missing conductivity.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem

logger = logging.getLogger(__name__)

def validate_smiles_batch(smiles_list: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """
    Validate a batch of SMILES strings.
    
    Args:
        smiles_list: List of SMILES strings to validate
        
    Returns:
        Tuple of (valid_smiles, invalid_smiles, error_messages)
    """
    valid_smiles = []
    invalid_smiles = []
    error_messages = []
    
    for smiles in smiles_list:
        try:
            if not isinstance(smiles, str) or not smiles.strip():
                invalid_smiles.append(smiles)
                error_messages.append("Empty or non-string SMILES")
                continue
                
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                invalid_smiles.append(smiles)
                error_messages.append("RDKit failed to parse SMILES")
            else:
                # Additional validation: check if molecule has at least one atom
                if mol.GetNumAtoms() == 0:
                    invalid_smiles.append(smiles)
                    error_messages.append("Molecule has no atoms")
                else:
                    valid_smiles.append(smiles)
                    error_messages.append("")
                    
        except Exception as e:
            invalid_smiles.append(smiles)
            error_messages.append(f"Exception during validation: {str(e)}")
            
    return valid_smiles, invalid_smiles, error_messages

def check_conductivity_column(df: pd.DataFrame) -> Tuple[bool, Optional[str]]:
    """
    Check if the DataFrame contains a valid conductivity column.
    
    Args:
        df: DataFrame to check
        
    Returns:
        Tuple of (has_conductivity, column_name)
        If conductivity is found, returns (True, column_name)
        If conductivity is missing, returns (False, None)
    """
    possible_names = ['conductivity', 'log_conductivity', 'conductivity_log', 'log_cond']
    
    for col in possible_names:
        if col in df.columns:
            # Check if the column has valid numeric data
            if df[col].dtype not in ['float64', 'int64', 'float32', 'int32']:
                try:
                    df[col] = pd.to_numeric(df[col], errors='raise')
                except (ValueError, TypeError):
                    logger.warning(f"Column '{col}' could not be converted to numeric")
                    continue
                    
            # Check for missing values
            if df[col].isna().all():
                logger.warning(f"Column '{col}' contains only NaN values")
                continue
                
            return True, col
            
    logger.error("No valid conductivity column found in DataFrame")
    logger.error(f"Available columns: {list(df.columns)}")
    return False, None

def handle_invalid_smiles(df: pd.DataFrame, smiles_col: str = 'smiles') -> pd.DataFrame:
    """
    Handle invalid SMILES in the DataFrame by marking them and logging.
    
    Args:
        df: DataFrame with SMILES column
        smiles_col: Name of the SMILES column
        
    Returns:
        DataFrame with 'valid' and 'error_msg' columns added
    """
    if smiles_col not in df.columns:
        raise ValueError(f"SMILES column '{smiles_col}' not found in DataFrame")
        
    valid_smiles, invalid_smiles, error_messages = validate_smiles_batch(df[smiles_col].tolist())
    
    df['valid'] = df[smiles_col].apply(lambda x: x in valid_smiles)
    df['error_msg'] = df[smiles_col].apply(lambda x: error_messages[valid_smiles.index(x)] if x in valid_smiles else error_messages[invalid_smiles.index(x)])
    
    invalid_count = df['valid'].sum() == 0
    if invalid_count > 0:
        logger.warning(f"Found {invalid_count} invalid SMILES out of {len(df)} total")
        for idx, row in df[df['valid'] == False].iterrows():
            logger.warning(f"Invalid SMILES at index {idx}: {row[smiles_col]} - {row['error_msg']}")
            
    return df

def handle_missing_conductivity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing conductivity data by filtering or logging.
    
    Args:
        df: DataFrame with conductivity column
        
    Returns:
        DataFrame with rows containing missing conductivity removed
        
    Raises:
        ValueError: If no valid conductivity data exists
    """
    has_conductivity, col_name = check_conductivity_column(df)
    
    if not has_conductivity:
        raise ValueError("No valid conductivity column found in DataFrame")
        
    original_count = len(df)
    df = df.dropna(subset=[col_name])
    removed_count = original_count - len(df)
    
    if removed_count > 0:
        logger.warning(f"Removed {removed_count} rows with missing conductivity values")
        
    if len(df) == 0:
        raise ValueError("All rows had missing conductivity values - no valid data remaining")
        
    logger.info(f"Remaining {len(df)} rows with valid conductivity data")
    return df

def process_molecule_with_error_handling(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Process a single SMILES string with comprehensive error handling.
    
    Args:
        smiles: SMILES string to process
        
    Returns:
        Dictionary with processing result or None if invalid
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"Failed to parse SMILES: {smiles}")
            return None
            
        if mol.GetNumAtoms() == 0:
            logger.warning(f"SMILES results in empty molecule: {smiles}")
            return None
            
        return {
            'smiles': smiles,
            'valid': True,
            'mol': mol,
            'num_atoms': mol.GetNumAtoms(),
            'num_bonds': mol.GetNumBonds()
        }
        
    except Exception as e:
        logger.error(f"Exception processing SMILES {smiles}: {str(e)}")
        return None

def validate_target_range(values: pd.Series, min_range: float = 3.0) -> Tuple[bool, float]:
    """
    Validate that the target variable has sufficient dynamic range.
    
    Args:
        values: Series of target values
        min_range: Minimum required log range
        
    Returns:
        Tuple of (is_valid, actual_range)
    """
    valid_values = values.dropna()
    if len(valid_values) == 0:
        logger.error("No valid values in target series")
        return False, 0.0
        
    actual_range = valid_values.max() - valid_values.min()
    is_valid = actual_range >= min_range
    
    if not is_valid:
        logger.warning(f"Target range ({actual_range:.2f}) is below minimum ({min_range})")
        
    return is_valid, actual_range