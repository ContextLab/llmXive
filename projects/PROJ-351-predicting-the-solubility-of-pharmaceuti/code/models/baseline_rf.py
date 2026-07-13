"""
Random Forest Baseline Model for ESOL Solubility Prediction.

Implements Morgan Fingerprints and RandomForestRegressor training.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# Configure logger
logger = logging.getLogger(__name__)

def generate_morgan_fingerprint(smiles: str, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Generate a Morgan fingerprint for a given SMILES string.
    
    Args:
        smiles: SMILES string of the molecule.
        radius: Radius of the fingerprint.
        n_bits: Number of bits in the fingerprint.
        
    Returns:
        Numpy array of the fingerprint.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return np.zeros(n_bits)
        
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        arr = np.zeros(n_bits)
        AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
        return arr
    except Exception as e:
        logger.warning(f"Failed to generate fingerprint for {smiles}: {e}")
        return np.zeros(n_bits)

def load_processed_data(data_path: str) -> pd.DataFrame:
    """
    Load the processed CSV data.
    
    Args:
        data_path: Path to the CSV file.
        
    Returns:
        DataFrame with SMILES and logS columns.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    return pd.read_csv(data_path)

def prepare_features_and_targets(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare features (fingerprints) and targets (logS) from the DataFrame.
    
    Args:
        df: DataFrame with 'SMILES' and 'logS' columns.
        
    Returns:
        Tuple of (X, y) arrays.
    """
    smiles_list = df['SMILES'].values
    logS_list = df['logS'].values
    
    fps = [generate_morgan_fingerprint(smiles) for smiles in smiles_list]
    X = np.array(fps)
    y = np.array(logS_list)
    
    return X, y

def train_random_forest(X: np.ndarray, y: np.ndarray, n_estimators: int = 100, max_depth: int = 10) -> RandomForestRegressor:
    """
    Train a Random Forest Regressor.
    
    Args:
        X: Feature matrix.
        y: Target vector.
        n_estimators: Number of trees.
        max_depth: Maximum depth of trees.
        
    Returns:
        Trained RandomForestRegressor model.
    """
    logger.info(f"Training Random Forest with {n_estimators} trees and max_depth={max_depth}")
    model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, random_state=42, n_jobs=-1)
    model.fit(X, y)
    logger.info("Training completed.")
    return model

def evaluate_model(model: RandomForestRegressor, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    """
    Evaluate the model on the given data.
    
    Args:
        model: Trained model.
        X: Feature matrix.
        y: Target vector.
        
    Returns:
        Dictionary with 'r2' and 'rmse' metrics.
    """
    y_pred = model.predict(X)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    r2 = r2_score(y, y_pred)
    
    logger.info(f"Evaluation - RMSE: {rmse:.4f}, R2: {r2:.4f}")
    return {"rmse": float(rmse), "r2": float(r2)}

def save_model(model: RandomForestRegressor, path: str):
    """
    Save the model to disk.
    
    Args:
        model: Model to save.
        path: Path to save the model.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    logger.info(f"Model saved to {path}")

def main():
    """
    Main entry point for training the Random Forest baseline.
    """
    # Default paths (can be overridden by args in a real CLI)
    train_path = "data/processed/train.csv"
    test_path = "data/processed/test.csv"
    model_save_path = "models/baseline_rf.pkl"
    metrics_save_path = "results/baseline_metrics.json"
    
    # Ensure directories exist
    Path(model_save_path).parent.mkdir(parents=True, exist_ok=True)
    Path(metrics_save_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Load Data
    try:
        train_df = load_processed_data(train_path)
        test_df = load_processed_data(test_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Prepare Features
    X_train, y_train = prepare_features_and_targets(train_df)
    X_test, y_test = prepare_features_and_targets(test_df)
    
    # Train
    model = train_random_forest(X_train, y_train)
    
    # Evaluate
    metrics = evaluate_model(model, X_test, y_test)
    
    # Save Model
    save_model(model, model_save_path)
    
    # Save Metrics
    with open(metrics_save_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Pipeline complete. Metrics saved to {metrics_save_path}")

if __name__ == "__main__":
    main()