import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """Configure and return a logger."""
    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger

def compute_file_checksum(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_file_directory(file_path: Union[str, Path]) -> Path:
    """Ensure the directory for a file path exists."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.parent

def safe_json_load(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file, returning None if it doesn't exist or is invalid."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def safe_json_save(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
    """Safely save data to a JSON file."""
    try:
        path = Path(file_path)
        ensure_file_directory(path)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Failed to save JSON to {file_path}: {e}")
        return False

def record_checksums(checksums: Dict[str, str], output_path: Union[str, Path]) -> None:
    """Record file checksums to a JSON file."""
    safe_json_save(checksums, output_path)

def handle_missing_values(data: Dict[str, Any], outcome_col: str, treatment_col: str) -> Dict[str, Any]:
    """
    Perform listwise deletion on the dataset to handle missing values.
    
    Args:
        data: Dictionary containing 'X' (features/observations) and 'y' (outcome).
             'X' is expected to be a list of dicts or a 2D array-like structure.
             'y' is expected to be a list.
        outcome_col: Key name for the outcome variable in the data dict if X is list of dicts.
        treatment_col: Key name for the treatment variable in the data dict if X is list of dicts.
    
    Returns:
        A new dictionary with 'X' and 'y' filtered to rows where both outcome and treatment are not None/NaN.
    """
    import numpy as np
    
    X = data.get('X')
    y = data.get('y')
    
    if X is None or y is None:
        raise ValueError("Data must contain 'X' and 'y' keys.")
    
    # Convert to numpy arrays for easier handling if they aren't already
    # Assuming X is a 2D array or list of lists/dicts
    # If X is a list of dicts, we need to extract the specific columns
    
    n_samples = len(y)
    
    if isinstance(X, list) and len(X) > 0 and isinstance(X[0], dict):
        # Extract treatment and outcome columns from list of dicts
        # We assume the treatment is in X and outcome is in y, but sometimes outcome might be in X too
        # Based on typical usage in this project, y is the outcome.
        # We need to check if the treatment column in X has missing values too.
        
        # Let's assume the treatment column is the first column or identified by a key
        # Since the signature is generic, we'll assume X is a 2D array-like for calculation
        # and handle the dict case if needed by the caller or by standardizing input.
        
        # For now, let's assume X is a 2D array (numpy or list of lists)
        # and y is a 1D array (numpy or list).
        # If X is list of dicts, the caller should have already converted it or we handle it here.
        # Let's handle the list of dicts case if the keys are provided.
        # However, the task description says "listwise deletion before power calculation".
        # Power calculation usually needs a treatment vector and an outcome vector.
        
        # Let's assume the data dict structure is:
        # { 'X': array-like (N, features), 'y': array-like (N,), 'treatment': array-like (N,) }
        # OR
        # { 'X': list of dicts, 'y': list } where treatment is in X.
        
        # Given the context of T016, we need to clean rows where outcome OR treatment is missing.
        # Let's assume the standard structure passed to power functions is (X, y, treatment)
        # But the function signature here takes `data` dict.
        
        # Let's look at how data is used in main.py or loaders.
        # loaders.py returns data with 'X' and 'y'. Treatment is often derived or is a column in X.
        # For listwise deletion, we need to identify the treatment column index or name.
        
        # To make this robust, we will assume:
        # 1. If 'treatment' is in data, use it.
        # 2. If 'treatment_col' is provided and X is list of dicts, use that key.
        # 3. Otherwise, assume treatment is the last column of X (common convention in some pipelines) 
        #    or the first. Let's assume the caller ensures X contains the treatment column if needed,
        #    or we treat the whole row.
        
        # Actually, the simplest interpretation for "listwise deletion" in this context:
        # Remove any row where the outcome (y) is missing OR the treatment assignment is missing.
        
        # Let's assume the data dict has:
        # 'X': 2D array (N, p)
        # 'y': 1D array (N)
        # 'treatment': 1D array (N) (optional, if not in X)
        
        # If 'treatment' is not in data, we might need to infer it from X or assume no missing treatment.
        # But the task implies we need to handle missing values in the relevant variables.
        
        # Let's implement a generic row filter based on y and a treatment vector.
        # We need to extract the treatment vector.
        
        treatment = data.get('treatment')
        if treatment is None and isinstance(X, list) and len(X) > 0 and isinstance(X[0], dict):
            # Try to get treatment from X using treatment_col
            if treatment_col and all(treatment_col in row for row in X):
                treatment = [row[treatment_col] for row in X]
            else:
                # Fallback: assume no treatment missing or treat as all valid if not found
                # But strictly, if we can't find treatment, we can't check its missingness.
                # Let's assume if not found, we only check y.
                treatment = None
        
        if isinstance(X, np.ndarray):
            X = X.tolist()
        if isinstance(y, np.ndarray):
            y = y.tolist()
        if treatment is not None and isinstance(treatment, np.ndarray):
            treatment = treatment.tolist()
        
        # Filter rows
        valid_indices = []
        for i in range(n_samples):
            y_val = y[i]
            t_val = treatment[i] if treatment is not None else None
            
            # Check if y is missing
            if y_val is None or (isinstance(y_val, float) and np.isnan(y_val)):
                continue
            
            # Check if treatment is missing
            if t_val is not None:
                if t_val is None or (isinstance(t_val, float) and np.isnan(t_val)):
                    continue
            
            valid_indices.append(i)
        
        # Construct new data
        new_X = [X[i] for i in valid_indices]
        new_y = [y[i] for i in valid_indices]
        
        result = {'X': new_X, 'y': new_y}
        if treatment is not None:
            result['treatment'] = [treatment[i] for i in valid_indices]
        
        return result
        
    else:
        # Assume X and y are array-like (lists of lists or numpy arrays)
        # We need to know which column in X is the treatment.
        # If not specified, we can't reliably do listwise deletion on treatment.
        # However, the task says "handle missing values via listwise deletion".
        # Usually this means dropping rows with any NaN in the variables used for analysis.
        # The analysis uses y and treatment.
        
        # Let's assume the treatment is provided separately or is the last column of X.
        # If treatment is not provided, we assume no missing treatment or only drop based on y.
        
        # Let's assume the caller passes a 'treatment' key if it's separate.
        treatment = data.get('treatment')
        
        # Convert to numpy for easier NaN handling
        X_arr = np.array(X)
        y_arr = np.array(y)
        
        # Create a mask for valid y
        y_mask = ~(np.isnan(y_arr) | (y_arr == None))
        
        if treatment is not None:
            t_arr = np.array(treatment)
            t_mask = ~(np.isnan(t_arr) | (t_arr == None))
            combined_mask = y_mask & t_mask
        else:
            # If no treatment provided, assume only y matters or treatment is in X?
            # If treatment is in X, we should check all columns of X?
            # Listwise deletion usually applies to the specific variables used.
            # If we don't know the treatment column, we might drop rows with any NaN in X?
            # That's too aggressive. Let's assume if treatment is not provided, we only check y.
            # OR, if X is the design matrix including treatment, we check all columns?
            # Let's stick to: drop if y is missing. If treatment is separate, drop if treatment is missing.
            # If treatment is inside X, the caller should have extracted it.
            combined_mask = y_mask
            
        new_X = X_arr[combined_mask].tolist()
        new_y = y_arr[combined_mask].tolist()
        
        result = {'X': new_X, 'y': new_y}
        if treatment is not None:
            result['treatment'] = t_arr[combined_mask].tolist()
            
        return result
