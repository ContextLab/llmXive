import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
from code.config import TARGET_VAR, DATA_PATH

logger = logging.getLogger(__name__)

def validate_smiles_batch(smiles_list: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """
    Validates a batch of SMILES strings.
    
    Returns:
        valid_smiles: List of successfully parsed SMILES
        invalid_smiles: List of SMILES that failed parsing
        error_messages: List of error messages corresponding to invalid SMILES
    """
    valid_smiles = []
    invalid_smiles = []
    error_messages = []

    for smiles in smiles_list:
        if not isinstance(smiles, str) or not smiles.strip():
            invalid_smiles.append(str(smiles))
            error_messages.append("Empty or non-string SMILES")
            continue
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            invalid_smiles.append(smiles)
            error_messages.append("RDKit failed to parse SMILES")
        else:
            valid_smiles.append(smiles)
    
    return valid_smiles, invalid_smiles, error_messages

def check_conductivity_column(df: pd.DataFrame) -> bool:
    """
    Checks if the target variable column exists in the DataFrame.
    
    Args:
        df: DataFrame containing molecular data
        
    Returns:
        True if the target column exists, False otherwise
        
    Raises:
        ValueError: If the target variable is missing from the dataset
    """
    if TARGET_VAR not in df.columns:
        available_cols = list(df.columns)
        logger.error(f"Target variable '{TARGET_VAR}' not found in dataset.")
        logger.error(f"Available columns: {available_cols}")
        
        # Check for common fallbacks
        if 'conductivity' in df.columns:
            logger.warning("Found 'conductivity' column but config TARGET_VAR is different.")
        if 'HOMO_LUMO_gap' in df.columns:
            logger.warning("Found 'HOMO_LUMO_gap' column which might be a fallback target.")
        
        raise ValueError(f"Missing target variable '{TARGET_VAR}' in dataset. "
                       f"Ensure the data contains the required conductivity column or "
                       f"update config.py TARGET_VAR if using a proxy.")
    return True

def handle_invalid_smiles(df: pd.DataFrame, valid_smiles_col: str = 'smiles') -> pd.DataFrame:
    """
    Filters out invalid SMILES from the DataFrame and logs the issue.
    
    Args:
        df: Input DataFrame with a 'smiles' column
        valid_smiles_col: Name of the column containing SMILES strings
        
    Returns:
        DataFrame containing only valid molecules
    """
    valid_count = 0
    invalid_count = 0
    invalid_indices = []
    
    for idx, row in df.iterrows():
        smiles = row[valid_smiles_col]
        if pd.isna(smiles) or not isinstance(smiles, str) or not smiles.strip():
            invalid_indices.append(idx)
            invalid_count += 1
            continue
            
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            invalid_indices.append(idx)
            invalid_count += 1
            logger.warning(f"Invalid SMILES at index {idx}: '{smiles[:50]}...'")
        else:
            valid_count += 1
    
    if invalid_count > 0:
        logger.warning(f"Removing {invalid_count} invalid SMILES entries. "
                     f"Keeping {valid_count} valid entries.")
        df_clean = df.drop(index=invalid_indices).reset_index(drop=True)
        return df_clean
    
    return df

def handle_missing_conductivity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handles missing conductivity values by logging and removing rows with NaN.
    
    Args:
        df: DataFrame containing the target variable column
        
    Returns:
        DataFrame with rows containing missing target values removed
        
    Raises:
        ValueError: If all target values are missing
    """
    if TARGET_VAR not in df.columns:
        raise ValueError(f"Cannot handle missing {TARGET_VAR}: column not found.")
    
    missing_mask = df[TARGET_VAR].isna()
    missing_count = missing_mask.sum()
    total_count = len(df)
    
    if missing_count > 0:
        logger.warning(f"Found {missing_count} rows with missing {TARGET_VAR} values "
                     f"({(missing_count/total_count)*100:.2f}% of data).")
        df_clean = df.dropna(subset=[TARGET_VAR]).reset_index(drop=True)
        
        if len(df_clean) == 0:
            raise ValueError(f"All {total_count} rows had missing {TARGET_VAR} values. "
                           "Dataset is unusable.")
        
        logger.info(f"Retained {len(df_clean)} rows after removing missing target values.")
        return df_clean
    
    return df

def process_molecule_with_error_handling(smiles: str, target_val: Optional[float] = None) -> Dict[str, Any]:
    """
    Processes a single molecule with comprehensive error handling.
    
    Args:
        smiles: SMILES string to process
        target_val: Optional target value (conductivity)
        
    Returns:
        Dictionary with processing status and data
    """
    result = {
        'smiles': smiles,
        'status': 'pending',
        'error_msg': None,
        'molecule': None,
        'target': target_val
    }
    
    # Validate SMILES
    if not isinstance(smiles, str) or not smiles.strip():
        result['status'] = 'invalid'
        result['error_msg'] = 'Empty or non-string SMILES'
        return result
    
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        result['status'] = 'invalid'
        result['error_msg'] = 'RDKit failed to parse SMILES'
        return result
    
    result['molecule'] = mol
    result['status'] = 'valid'
    
    # Check target value if provided
    if target_val is not None and pd.isna(target_val):
        result['status'] = 'missing_target'
        result['error_msg'] = 'Target value is NaN'
    
    return result

def validate_target_range(df: pd.DataFrame, min_range: float = 3.0) -> bool:
    """
    Validates that the target variable has sufficient dynamic range.
    
    Args:
        df: DataFrame containing the target variable
        min_range: Minimum required range (max - min)
        
    Returns:
        True if range is sufficient, False otherwise
        
    Raises:
        ValueError: If target column is missing or range is insufficient
    """
    if TARGET_VAR not in df.columns:
        raise ValueError(f"Target column '{TARGET_VAR}' not found in DataFrame.")
    
    target_data = df[TARGET_VAR].dropna()
    
    if len(target_data) == 0:
        raise ValueError("No valid target values found after removing NaNs.")
    
    actual_range = target_data.max() - target_data.min()
    
    if actual_range < min_range:
        logger.warning(f"Target variable range ({actual_range:.2f}) is less than "
                     f"required minimum ({min_range}). Model performance may be limited.")
        return False
    
    logger.info(f"Target variable range ({actual_range:.2f}) meets minimum requirement ({min_range}).")
    return True