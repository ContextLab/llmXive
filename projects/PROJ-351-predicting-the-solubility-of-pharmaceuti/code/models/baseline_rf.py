"""
Random Forest Baseline Model (Task T013)

Implements Morgan fingerprint generation and Random Forest training for the ESOL dataset.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

import numpy as np
import pandas as pd
import pickle
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.seeds import get_seed

def generate_morgan_fingerprint(smiles: str, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Generates a Morgan fingerprint for a given SMILES string.
    
    Args:
        smiles: SMILES string of the molecule.
        radius: Radius of the fingerprint (default 2).
        n_bits: Number of bits in the fingerprint (default 2048).
    
    Returns:
        Numpy array representing the fingerprint.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")
    
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=int)
    AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
    return arr

def load_processed_data(data_path: str) -> Tuple[List[str], np.ndarray]:
    """
    Loads cleaned data from a pickle file or CSV.
    
    Args:
        data_path: Path to the data file.
    
    Returns:
        Tuple of (smiles_list, targets).
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    if path.suffix == '.pkl':
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        if isinstance(data, pd.DataFrame):
            return data['smiles'].tolist(), data['logS'].values
        elif isinstance(data, dict):
            return data['smiles'], np.array(data['logS'])
        elif isinstance(data, list):
            return [item['smiles'] for item in data], np.array([item['logS'] for item in data])
        else:
            raise ValueError(f"Unexpected data format in pickle: {type(data)}")
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def prepare_features_and_targets(smiles_list: List[str], n_bits: int = 2048) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generates fingerprints for a list of SMILES strings.
    
    Args:
        smiles_list: List of SMILES strings.
        n_bits: Number of bits in the fingerprint.
    
    Returns:
        Tuple of (features, targets). Note: targets are not generated here, only features.
        This function is for feature preparation only.
    """
    features = []
    for smiles in smiles_list:
        fp = generate_morgan_fingerprint(smiles, n_bits=n_bits)
        features.append(fp)
    return np.array(features)

def train_random_forest(X: np.ndarray, y: np.ndarray, **kwargs) -> RandomForestRegressor:
    """
    Trains a Random Forest model.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        **kwargs: Hyperparameters for RandomForestRegressor.
    
    Returns:
        Trained Random Forest model.
    """
    # Default parameters if not provided
    params = {
        'n_estimators': 100,
        'max_depth': None,
        'min_samples_split': 2,
        'min_samples_leaf': 1,
        'random_state': get_seed()
    }
    params.update(kwargs)
    
    model = RandomForestRegressor(**params)
    model.fit(X, y)
    return model

def evaluate_model(model: RandomForestRegressor, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Evaluates the model on a given dataset.
    
    Args:
        model: Trained Random Forest model.
        X: Feature matrix.
        y: Target vector.
    
    Returns:
        Dictionary with RMSE and R2 scores.
    """
    y_pred = model.predict(X)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)
    return {'rmse': rmse, 'r2': r2}

def save_model(model: RandomForestRegressor, path: str) -> None:
    """
    Saves the model to a pickle file.
    
    Args:
        model: Trained Random Forest model.
        path: Path to save the model.
    """
    with open(path, 'wb') as f:
        pickle.dump(model, f)

def main():
    """
    Main entry point for baseline RF training (T013).
    This is a placeholder for direct execution; T016a uses train_final_rf.py.
    """
    logger = logging.getLogger("baseline_rf")
    logger.info("Running baseline RF model definition (T013).")
    # This file defines the API; actual training is done in T016a.

if __name__ == "__main__":
    main()
