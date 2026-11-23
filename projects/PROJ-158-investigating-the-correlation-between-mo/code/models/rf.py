"""
Random Forest Baseline Model for DSSC Performance Prediction.

This module generates Morgan fingerprints from SMILES and trains a
Random Forest regressor to predict Power Conversion Efficiency (PCE).
It serves as a baseline for comparison against the GCN model (FR-005).
"""

import os
import sys
import logging
import pickle
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from rdkit import Chem
from rdkit.Chem import AllChem

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.config import get_config, ensure_dirs
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Constants
FINGERPRINT_RADIUS = 2
FINGERPRINT_NBITS = 2048
MODEL_OUTPUT_PATH = "results/model_artifacts/random_forest_model.pkl"
METRICS_OUTPUT_PATH = "results/model_artifacts/random_forest_metrics.json"
INPUT_DATA_PATH = "data/processed/cleaned_data.csv"


def generate_morgan_fingerprints(smiles_list: List[str]) -> np.ndarray:
    """
    Generate Morgan fingerprints for a list of SMILES strings.

    Args:
        smiles_list: List of SMILES strings.

    Returns:
        numpy array of shape (n_molecules, n_bits) containing binary fingerprints.
    """
    fingerprints = []
    invalid_indices = []

    for i, smiles in enumerate(smiles_list):
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                invalid_indices.append(i)
                continue
            fp = AllChem.GetMorganFingerprintAsBitVect(
                mol, radius=FINGERPRINT_RADIUS, nBits=FINGERPRINT_NBITS
            )
            arr = np.zeros((FINGERPRINT_NBITS,), dtype=np.int8)
            AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
            fingerprints.append(arr)
        except Exception as e:
            logger.warning(f"Failed to generate fingerprint for SMILES at index {i}: {e}")
            invalid_indices.append(i)

    if invalid_indices:
        logger.warning(f"Skipped {len(invalid_indices)} molecules due to fingerprint generation errors.")

    if not fingerprints:
        raise ValueError("No valid fingerprints generated. Check input data.")

    return np.array(fingerprints)


def train_random_forest(
    X: np.ndarray,
    y: np.ndarray,
    test_size: float = 0.2,
    random_state: int = 42,
    n_estimators: int = 100,
    max_depth: Optional[int] = None
) -> Tuple[RandomForestRegressor, Dict[str, float]]:
    """
    Train a Random Forest regressor and evaluate on a hold-out set.

    Args:
        X: Feature matrix (fingerprints).
        y: Target values (PCE).
        test_size: Fraction of data to use for testing.
        random_state: Random seed for reproducibility.
        n_estimators: Number of trees in the forest.
        max_depth: Maximum depth of the trees.

    Returns:
        Tuple of (trained_model, metrics_dict).
    """
    from sklearn.model_selection import train_test_split

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    logger.info(f"Training set size: {len(X_train)}, Test set size: {len(X_test)}")

    # Initialize and train model
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    # Calculate metrics
    metrics = {
        "train": {
            "mae": float(mean_absolute_error(y_train, y_pred_train)),
            "rmse": float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
            "r2": float(r2_score(y_train, y_pred_train))
        },
        "test": {
            "mae": float(mean_absolute_error(y_test, y_pred_test)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
            "r2": float(r2_score(y_test, y_pred_test))
        }
    }

    logger.info(f"RF Training MAE: {metrics['train']['mae']:.4f}, Test MAE: {metrics['test']['mae']:.4f}")

    return model, metrics


def save_model_and_metrics(
    model: RandomForestRegressor,
    metrics: Dict[str, float],
    model_path: str,
    metrics_path: str
) -> None:
    """
    Save the trained model and metrics to disk.

    Args:
        model: Trained Random Forest model.
        metrics: Dictionary of evaluation metrics.
        model_path: Path to save the model pickle.
        metrics_path: Path to save the metrics JSON.
    """
    ensure_dirs([model_path, metrics_path])

    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")

    # Save metrics as JSON
    import json
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")


def main() -> None:
    """
    Main execution function for the Random Forest baseline.
    1. Loads preprocessed data from data/processed/cleaned_data.csv.
    2. Generates Morgan fingerprints.
    3. Trains the Random Forest model.
    4. Saves the model and metrics to results/model_artifacts/.
    """
    config = get_config()
    ensure_dirs([MODEL_OUTPUT_PATH, METRICS_OUTPUT_PATH])

    input_path = Path(config["DATA_PROCESSED_DIR"]) / INPUT_DATA_PATH.split('/')[-1]
    # Use the exact path relative to project root if it exists, otherwise construct it
    if not input_path.exists():
        # Fallback to relative path from config if absolute fails
        input_path = Path(INPUT_DATA_PATH)

    if not input_path.exists():
        logger.error(f"Input data file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    if 'smiles' not in df.columns or 'pce' not in df.columns:
        logger.error("Input data must contain 'smiles' and 'pce' columns.")
        sys.exit(1)

    smiles_list = df['smiles'].astype(str).tolist()
    y = df['pce'].values

    logger.info(f"Generating Morgan fingerprints for {len(smiles_list)} molecules...")
    X = generate_morgan_fingerprints(smiles_list)

    logger.info("Training Random Forest model...")
    model, metrics = train_random_forest(X, y)

    logger.info("Saving model and metrics...")
    save_model_and_metrics(model, metrics, MODEL_OUTPUT_PATH, METRICS_OUTPUT_PATH)

    logger.info("Random Forest baseline training completed successfully.")


if __name__ == "__main__":
    main()
