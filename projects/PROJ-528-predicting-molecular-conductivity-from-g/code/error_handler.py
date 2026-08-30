import logging
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
from code.config import TARGET_VAR, DATA_PATH
from code.validators import validate_smiles, check_target_range

logger = logging.getLogger(__name__)

def validate_smiles_batch(smiles_list: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """
    Validate a batch of SMILES strings.
    
    Returns:
        Tuple of (valid_smiles, invalid_smiles, error_messages)
    """
    valid = []
    invalid = []
    errors = []
    
    for smiles in smiles_list:
        if not isinstance(smiles, str) or not smiles.strip():
            invalid.append(smiles)
            errors.append("Empty or non-string SMILES")
            continue
            
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            invalid.append(smiles)
            errors.append("RDKit failed to parse SMILES")
        else:
            valid.append(smiles)
            errors.append(None)
    
    return valid, invalid, errors

def check_conductivity_column(df: pd.DataFrame) -> bool:
    """
    Check if the target variable column exists in the dataframe.
    
    Args:
        df: Input dataframe
        
    Returns:
        True if target column exists, False otherwise
    """
    target_col = TARGET_VAR
    if target_col not in df.columns:
        logger.error(f"Target variable '{target_col}' not found in dataframe. "
                    f"Available columns: {list(df.columns)}")
        return False
    return True

def handle_invalid_smiles(invalid_smiles: List[str], error_messages: List[str]) -> None:
    """
    Log and handle invalid SMILES strings.
    
    Args:
        invalid_smiles: List of invalid SMILES strings
        error_messages: Corresponding error messages
    """
    if not invalid_smiles:
        return
        
    logger.warning(f"Encountered {len(invalid_smiles)} invalid SMILES strings")
    for smiles, error in zip(invalid_smiles, error_messages):
        logger.warning(f"Invalid SMILES '{smiles}': {error}")

def handle_missing_conductivity(df: pd.DataFrame) -> bool:
    """
    Check for missing conductivity values and handle them.
    
    Args:
        df: Input dataframe
        
    Returns:
        True if valid target data exists, False if missing/invalid
    """
    target_col = TARGET_VAR
    
    if target_col not in df.columns:
        logger.error(f"Target variable '{target_col}' is missing from the dataset")
        return False
        
    missing_count = df[target_col].isna().sum()
    if missing_count > 0:
        logger.warning(f"Found {missing_count} missing values in '{target_col}'")
        # Log details about missing values
        missing_indices = df[df[target_col].isna()].index.tolist()
        logger.debug(f"Missing values at indices: {missing_indices[:10]}...")
        
    # Check if all values are missing
    if missing_count == len(df):
        logger.error(f"All values in '{target_col}' are missing")
        return False
        
    return True

def process_molecule_with_error_handling(smiles: str, target_value: Optional[float] = None) -> Dict[str, Any]:
    """
    Process a single molecule with comprehensive error handling.
    
    Args:
        smiles: SMILES string to process
        target_value: Optional target value (conductivity or HOMO-LUMO gap)
        
    Returns:
        Dictionary with processing status and any error messages
    """
    result = {
        'smiles': smiles,
        'status': 'pending',
        'error_msg': None,
        'target_valid': False,
        'mol_object': None
    }
    
    # Validate SMILES
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        result['status'] = 'invalid_smiles'
        result['error_msg'] = 'RDKit failed to parse SMILES'
        return result
        
    result['mol_object'] = mol
    result['status'] = 'valid_smiles'
    
    # Validate target if provided
    if target_value is not None:
        if pd.isna(target_value):
            result['status'] = 'missing_target'
            result['error_msg'] = 'Target value is missing'
        else:
            try:
                float(target_value)
                result['target_valid'] = True
            except (ValueError, TypeError):
                result['status'] = 'invalid_target'
                result['error_msg'] = f'Target value "{target_value}" is not numeric'
    else:
        result['status'] = 'missing_target'
        result['error_msg'] = 'No target value provided'
        
    return result

def validate_target_range(values: pd.Series, min_range: float = 3.0) -> bool:
    """
    Validate that the target variable has sufficient dynamic range.
    
    Args:
        values: Series of target values
        min_range: Minimum required log-transformed range
        
    Returns:
        True if range is sufficient, False otherwise
    """
    non_na_values = values.dropna()
    if len(non_na_values) == 0:
        logger.error("No valid target values found for range validation")
        return False
        
    # Check log range if values are positive
    positive_values = non_na_values[non_na_values > 0]
    if len(positive_values) > 0:
        log_values = np.log10(positive_values)
        log_range = log_values.max() - log_values.min()
        if log_range < min_range:
            logger.warning(f"Log-transformed target range ({log_range:.2f}) is less than "
                         f"minimum required ({min_range})")
            return False
    
    return True