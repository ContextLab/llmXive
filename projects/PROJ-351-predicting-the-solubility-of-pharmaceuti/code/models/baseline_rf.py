"""
Random Forest Baseline Model for ESOL Solubility Prediction.

Implements a Random Forest regressor using Morgan fingerprints (radius=2, 2048 bits)
as input features. This model serves as a performance baseline for the GNN models.
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
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.model_selection import train_test_split

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def generate_morgan_fingerprint(smiles: str, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Generate a Morgan fingerprint (ECFP) for a given SMILES string.

    Args:
        smiles: The SMILES string of the molecule.
        radius: Radius of the fingerprint (default 2 for ECFP4).
        n_bits: Number of bits in the fingerprint vector (default 2048).

    Returns:
        A numpy array of shape (n_bits,) representing the fingerprint.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
        arr = np.zeros((n_bits,), dtype=np.int8)
        AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
        return arr
    except Exception as e:
        logger.warning(f"Failed to generate fingerprint for SMILES '{smiles}': {e}")
        return None

def load_processed_data(split_type: str = "train") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load processed data from the split indices.

    Args:
        split_type: One of 'train', 'val', or 'test'.

    Returns:
        Tuple of (features_df, targets_df) where features are SMILES and targets are logS.
    """
    # Path to split indices (created by T006)
    splits_path = PROJECT_ROOT / "data" / "processed" / "splits"
    if not splits_path.exists():
        raise FileNotFoundError(f"Split indices not found at {splits_path}")

    # Load the split indices JSON
    with open(splits_path / "split_indices.json", "r") as f:
        splits = json.load(f)

    if split_type not in splits:
        raise ValueError(f"Split type '{split_type}' not found in split_indices.json")

    indices = splits[split_type]

    # Load the cleaned data (created by T005)
    cleaned_data_path = PROJECT_ROOT / "data" / "processed" / "cleaned_data.csv"
    if not cleaned_data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {cleaned_data_path}")

    df = pd.read_csv(cleaned_data_path)
    logger.info(f"Loaded {len(df)} molecules from cleaned data")

    # Filter to the specific split indices
    split_df = df.iloc[indices].reset_index(drop=True)
    logger.info(f"Loaded {len(split_df)} molecules for {split_type} split")

    return split_df

def prepare_features_and_targets(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert SMILES to Morgan fingerprints and extract logS targets.

    Args:
        df: DataFrame with 'smiles' and 'logS' columns.

    Returns:
        Tuple of (X, y) where X is the fingerprint matrix and y is the logS array.
    """
    logger.info("Generating Morgan fingerprints for all molecules...")
    fingerprints = []
    valid_indices = []
    invalid_count = 0

    for i, row in df.iterrows():
        fp = generate_morgan_fingerprint(row['smiles'])
        if fp is not None:
            fingerprints.append(fp)
            valid_indices.append(i)
        else:
            invalid_count += 1

    if invalid_count > 0:
        logger.warning(f"Excluded {invalid_count} molecules due to fingerprint generation failure")

    X = np.array(fingerprints)
    y = df.iloc[valid_indices]['logS'].values

    logger.info(f"Generated {len(X)} valid fingerprints")
    return X, y

def train_random_forest(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: Optional[np.ndarray] = None,
    y_val: Optional[np.ndarray] = None,
    n_estimators: int = 100,
    max_depth: int = None,
    random_state: int = 42
) -> RandomForestRegressor:
    """
    Train a Random Forest regressor.

    Args:
        X_train: Training feature matrix.
        y_train: Training target values.
        X_val: Validation feature matrix (optional).
        y_val: Validation target values (optional).
        n_estimators: Number of trees in the forest.
        max_depth: Maximum depth of trees.
        random_state: Random seed for reproducibility.

    Returns:
        Trained RandomForestRegressor model.
    """
    logger.info(f"Training Random Forest with {n_estimators} estimators...")

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
        verbose=1
    )

    model.fit(X_train, y_train)

    if X_val is not None and y_val is not None:
        val_pred = model.predict(X_val)
        val_r2 = r2_score(y_val, val_pred)
        val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
        logger.info(f"Validation R²: {val_r2:.4f}, RMSE: {val_rmse:.4f}")

    return model

def evaluate_model(
    model: RandomForestRegressor,
    X_test: np.ndarray,
    y_test: np.ndarray,
    predictions_path: Optional[str] = None
) -> Dict[str, float]:
    """
    Evaluate the model on the test set.

    Args:
        model: Trained Random Forest model.
        X_test: Test feature matrix.
        y_test: Test target values.
        predictions_path: Path to save predictions (optional).

    Returns:
        Dictionary with evaluation metrics.
    """
    logger.info("Evaluating model on test set...")

    y_pred = model.predict(X_test)

    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = np.mean(np.abs(y_test - y_pred))

    metrics = {
        'r2': float(r2),
        'rmse': float(rmse),
        'mae': float(mae),
        'n_samples': len(y_test)
    }

    logger.info(f"Test R²: {r2:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}")

    if predictions_path:
        os.makedirs(os.path.dirname(predictions_path), exist_ok=True)
        predictions_df = pd.DataFrame({
            'true': y_test,
            'predicted': y_pred
        })
        predictions_df.to_csv(predictions_path, index=False)
        logger.info(f"Predictions saved to {predictions_path}")

    return metrics

def main():
    """
    Main function to train and evaluate the Random Forest baseline.
    """
    logger.info("Starting Random Forest Baseline Training")

    # Ensure seeded environment
    from config.seeds import set_seed
    set_seed(42)

    # Load training data
    try:
        train_df = load_processed_data("train")
        val_df = load_processed_data("val")
        test_df = load_processed_data("test")
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        sys.exit(1)

    # Prepare features and targets
    X_train, y_train = prepare_features_and_targets(train_df)
    X_val, y_val = prepare_features_and_targets(val_df)
    X_test, y_test = prepare_features_and_targets(test_df)

    if len(X_train) == 0:
        logger.error("No training data available after fingerprint generation")
        sys.exit(1)

    # Train model
    model = train_random_forest(
        X_train, y_train,
        X_val, y_val,
        n_estimators=100,
        max_depth=None,
        random_state=42
    )

    # Evaluate model
    metrics = evaluate_model(
        model, X_test, y_test,
        predictions_path=str(PROJECT_ROOT / "results" / "rf_predictions.csv")
    )

    # Save metrics
    metrics_path = PROJECT_ROOT / "results" / "baseline_metrics.json"
    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)

    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Metrics saved to {metrics_path}")

    # Log training metrics using the project's logging utility
    from setup_logging import log_training_metrics
    log_training_metrics(
        model_type="RandomForest",
        metrics=metrics,
        output_path=str(PROJECT_ROOT / "data" / "logs" / "baseline_training.log")
    )

    logger.info("Random Forest Baseline Training Complete")

if __name__ == "__main__":
    main()