"""
Random Forest Baseline Implementation using Morgan Fingerprints.

This module implements a Random Forest baseline model for predicting molecular
reactivity properties (e.g., HOMO-LUMO gap) using Morgan fingerprints as input features.
It serves as a distinct baseline (FR-004) against the GNN architectures.

The workflow includes:
1. Generating Morgan fingerprints from SMILES strings.
2. Training a Random Forest Regressor.
3. Evaluating performance on a validation/test set.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error
from scipy.stats import pearsonr

# Add parent directory to path for imports if running as script
if __package__ is None or __package__ == '':
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config import get_config, ensure_directories
from utils.logging_utils import setup_logging, log_metric

# Constants
FINGERPRINT_RADIUS = 2
FINGERPRINT_BITS = 2048


def setup_script_logging(name: str = "random_forest_baseline") -> logging.Logger:
    """
    Initialize logging for the script.

    Args:
        name: Name of the logger.

    Returns:
        Configured logger instance.
    """
    return setup_logging(name)


def smiles_to_morgan_fingerprint(smiles: str, radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Convert a SMILES string to a Morgan fingerprint vector.

    Args:
        smiles: SMILES string representing the molecule.
        radius: Radius for the Morgan fingerprint (default 2).
        n_bits: Number of bits in the fingerprint (default 2048).

    Returns:
        Numpy array of the fingerprint vector.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {smiles}")

    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=int)
    AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
    return arr


def generate_fingerprints(smiles_list: List[str], radius: int = 2, n_bits: int = 2048) -> np.ndarray:
    """
    Generate Morgan fingerprints for a list of SMILES strings.

    Args:
        smiles_list: List of SMILES strings.
        radius: Radius for the Morgan fingerprint.
        n_bits: Number of bits in the fingerprint.

    Returns:
        2D Numpy array of shape (n_molecules, n_bits).
    """
    logger = logging.getLogger("random_forest_baseline")
    fingerprints = []
    excluded_count = 0

    for i, smiles in enumerate(smiles_list):
        try:
            fp = smiles_to_morgan_fingerprint(smiles, radius, n_bits)
            fingerprints.append(fp)
        except ValueError as e:
            logger.warning(f"Skipping invalid molecule at index {i}: {smiles} - {e}")
            excluded_count += 1

    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} invalid molecules from fingerprint generation.")

    return np.array(fingerprints)


def train_random_forest(
    X_train: np.ndarray,
    y_train: np.ndarray,
    n_estimators: int = 100,
    max_depth: Optional[int] = None,
    random_state: int = 42
) -> RandomForestRegressor:
    """
    Train a Random Forest Regressor.

    Args:
        X_train: Training features (fingerprints).
        y_train: Training targets (e.g., HOMO-LUMO gap).
        n_estimators: Number of trees in the forest.
        max_depth: Maximum depth of the tree.
        random_state: Random seed for reproducibility.

    Returns:
        Trained RandomForestRegressor model.
    """
    logger = logging.getLogger("random_forest_baseline")
    logger.info(f"Training Random Forest with {n_estimators} estimators...")

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    logger.info("Random Forest training completed.")

    return model


def evaluate_model(
    model: RandomForestRegressor,
    X_test: np.ndarray,
    y_test: np.ndarray
) -> Dict[str, float]:
    """
    Evaluate the Random Forest model on test data.

    Args:
        model: Trained Random Forest model.
        X_test: Test features.
        y_test: Test targets.

    Returns:
        Dictionary containing MSE, MAE, and Pearson R.
    """
    logger = logging.getLogger("random_forest_baseline")
    logger.info("Evaluating Random Forest model...")

    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    pearson_r, _ = pearsonr(y_test, y_pred)

    metrics = {
        "mse": float(mse),
        "mae": float(mae),
        "pearson_r": float(pearson_r)
    }

    logger.info(f"MSE: {mse:.4f}, MAE: {mae:.4f}, Pearson R: {pearson_r:.4f}")

    return metrics


def run_baseline(
    data_path: str,
    target_column: str = "homo_lumo_gap",
    smiles_column: str = "smiles",
    test_split_ratio: float = 0.2,
    random_state: int = 42,
    n_estimators: int = 100,
    output_dir: Optional[str] = None
) -> Tuple[RandomForestRegressor, Dict[str, float]]:
    """
    Main function to run the Random Forest baseline pipeline.

    Steps:
    1. Load data.
    2. Generate fingerprints.
    3. Split data.
    4. Train model.
    5. Evaluate model.
    6. Save results.

    Args:
        data_path: Path to the CSV/Parquet file containing data.
        target_column: Name of the target column.
        smiles_column: Name of the SMILES column.
        test_split_ratio: Ratio of data to use for testing.
        random_state: Random seed.
        n_estimators: Number of trees.
        output_dir: Directory to save results (defaults to config).

    Returns:
        Tuple of (trained_model, metrics_dict).
    """
    logger = setup_script_logging()
    config = get_config()
    if output_dir is None:
        output_dir = config.get("output_dir", "artifacts")
    ensure_directories([output_dir])

    logger.info(f"Loading data from {data_path}...")
    df = pd.read_csv(data_path)

    if smiles_column not in df.columns:
        raise ValueError(f"SMILES column '{smiles_column}' not found in data.")
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in data.")

    logger.info("Generating Morgan fingerprints...")
    fingerprints = generate_fingerprints(df[smiles_column].tolist())
    targets = df[target_column].values

    # Simple split (assuming data is already shuffled or using random_state)
    n_samples = len(fingerprints)
    n_test = int(n_samples * test_split_ratio)
    indices = np.random.RandomState(random_state).permutation(n_samples)
    test_indices = indices[:n_test]
    train_indices = indices[n_test:]

    X_train, X_test = fingerprints[train_indices], fingerprints[test_indices]
    y_train, y_test = targets[train_indices], targets[test_indices]

    logger.info(f"Training set size: {len(X_train)}, Test set size: {len(X_test)}")

    model = train_random_forest(X_train, y_train, n_estimators=n_estimators, random_state=random_state)
    metrics = evaluate_model(model, X_test, y_test)

    # Log metrics
    log_metric("baseline_mse", metrics["mse"])
    log_metric("baseline_mae", metrics["mae"])
    log_metric("baseline_pearson_r", metrics["pearson_r"])

    # Save model and metrics
    model_path = os.path.join(output_dir, "best_random_forest_model.pkl")
    import pickle
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {model_path}")

    metrics_path = os.path.join(output_dir, "baseline_metrics.json")
    with open(metrics_path, "w") as f:
        import json
        json.dump(metrics, f, indent=2)
    logger.info(f"Metrics saved to {metrics_path}")

    return model, metrics


def main():
    """
    Entry point for the script.
    """
    config = get_config()
    # Default paths based on project structure
    data_path = config.get("data_path", "data/processed/graphs_intermediate.csv") # Assuming a CSV export or similar
    # If the intermediate data is in PT format, we need to load it differently.
    # However, for RF, we need a tabular format. Let's assume a helper to export or
    # we load from the processed CSV if available, or adapt to load from PT if needed.
    # For this task, we assume a CSV version of the processed data exists or is created.
    # If not, we might need to load the PT file and convert.
    
    # Let's try to load from a standard location if the config doesn't specify a CSV.
    # The task description says "Implement Random Forest baseline". 
    # We will assume the input data is available in a format readable by pandas.
    # If the project uses graphs_intermediate.pt, we might need to convert that to CSV first.
    # But to keep this task focused on the RF model, we assume the data is ready.
    # If the data is strictly in PT, we would need a loader.
    # Let's assume the input is the preprocessed data in CSV format for simplicity in this baseline.
    # If the actual data is in PT, the user would need to convert it or we add a loader.
    # Given the task is about the model, we assume data is available.
    
    # Fallback to a common path if not in config
    if not os.path.exists(data_path):
        # Try to find the processed CSV if it exists
        alt_path = "data/processed/graphs_intermediate.csv"
        if os.path.exists(alt_path):
            data_path = alt_path
        else:
            # If no CSV, we cannot proceed without a loader for PT.
            # We will raise an error to indicate data is missing.
            raise FileNotFoundError(f"Data file not found at {data_path} or {alt_path}. Please ensure data is exported to CSV or implement a PT loader.")

    run_baseline(data_path)


if __name__ == "__main__":
    main()