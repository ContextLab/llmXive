"""
Train Random Forest models for Morgan and MACCS fingerprints.

This module implements the training logic for User Story 2, creating
CPU-only Random Forest models for each fold and fingerprint type.
"""
import os
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, balanced_accuracy_score
from sklearn.exceptions import NotFittedError

# Import project utilities and constants
from utils import init_random_seed, get_logger
from constants import MORGAN_RADIUS, MORGAN_BITS, MACCS_BITS, N_FOLDS, TANIMOTO_THRESHOLD

# Ensure CPU-only execution
os.environ["CUDA_VISIBLE_DEVICES"] = ""

logger = get_logger(__name__)


def load_split_indices(split_dir: Path) -> List[Dict[str, np.ndarray]]:
    """
    Load split indices from the split directory.

    Args:
        split_dir: Path to the directory containing split files.

    Returns:
        List of dictionaries containing train/test indices for each fold.
    """
    splits = []
    for fold_idx in range(N_FOLDS):
        split_file = split_dir / f"split_fold_{fold_idx}.pkl"
        if not split_file.exists():
            raise FileNotFoundError(f"Split file not found: {split_file}")

        with open(split_file, "rb") as f:
            split_data = pickle.load(f)
        splits.append(split_data)

    logger.info(f"Loaded {len(splits)} split configurations.")
    return splits


def load_fingerprint_data(data_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load fingerprint data from the processed data directory.

    Args:
        data_dir: Path to the data directory containing fingerprint CSVs.

    Returns:
        Tuple of (fingerprints_df, labels_df)
    """
    # Assuming fingerprints are stored in a specific format after T017
    # We expect 'data/processed/fingerprints_morgan.csv' and 'data/processed/fingerprints_maccs.csv'
    # and 'data/processed/organophosphates_filtered.csv' for labels

    morgan_path = data_dir / "fingerprints_morgan.csv"
    maccs_path = data_dir / "fingerprints_maccs.csv"
    labels_path = data_dir / "organophosphates_filtered.csv"

    if not morgan_path.exists() or not maccs_path.exists() or not labels_path.exists():
        raise FileNotFoundError(
            "Required fingerprint or label files missing. "
            "Ensure T017 (fingerprints) and T012 (filter) are completed."
        )

    morgan_fps = pd.read_csv(morgan_path)
    maccs_fps = pd.read_csv(maccs_path)
    labels_df = pd.read_csv(labels_path)

    # Extract toxicity labels (assuming columns like 'NR-AR', 'NR-AR-LBD', etc.)
    # We will iterate over all toxicity endpoint columns
    label_cols = [col for col in labels_df.columns if col not in ['SMILES', 'Mol_Wt']]
    if not label_cols:
        raise ValueError("No toxicity endpoint columns found in labels file.")

    logger.info(f"Found {len(label_cols)} toxicity endpoints to model.")

    return morgan_fps, maccs_fps, labels_df, label_cols


def train_single_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    n_estimators: int = 100,
    max_depth: int = 15,
    random_state: int = 42
) -> RandomForestClassifier:
    """
    Train a single Random Forest model.

    Args:
        X_train: Training features.
        y_train: Training labels.
        n_estimators: Number of trees.
        max_depth: Maximum tree depth.
        random_state: Random seed.

    Returns:
        Trained RandomForestClassifier.
    """
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=1,  # Force single thread per model to avoid oversubscription
        verbose=0
    )
    model.fit(X_train, y_train)
    return model


def evaluate_model(
    model: RandomForestClassifier,
    X_test: np.ndarray,
    y_test: np.ndarray,
    fold_idx: int,
    endpoint_name: str,
    fingerprint_type: str
) -> Dict[str, float]:
    """
    Evaluate a trained model and return metrics.

    Args:
        model: Trained model.
        X_test: Test features.
        y_test: Test labels.
        fold_idx: Fold index.
        endpoint_name: Name of the toxicity endpoint.
        fingerprint_type: 'Morgan' or 'MACCS'.

    Returns:
        Dictionary of metrics (ROC-AUC, PR-AUC, Balanced Accuracy).
    """
    try:
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)
    except NotFittedError:
        logger.error(f"Model not fitted for fold {fold_idx}, endpoint {endpoint_name}")
        return {}

    # Handle case where only one class is present (common in toxicology)
    if len(np.unique(y_test)) < 2:
        logger.warning(f"Only one class present in test set for {endpoint_name}. Skipping AUC metrics.")
        return {
            "fold": fold_idx,
            "endpoint": endpoint_name,
            "fingerprint": fingerprint_type,
            "roc_auc": np.nan,
            "pr_auc": np.nan,
            "balanced_accuracy": balanced_accuracy_score(y_test, y_pred)
        }

    roc_auc = roc_auc_score(y_test, y_pred_proba)
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    pr_auc = auc(recall, precision)
    bal_acc = balanced_accuracy_score(y_test, y_pred)

    logger.info(
        f"Fold {fold_idx} | {endpoint_name} | {fingerprint_type} | "
        f"ROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f} | BalAcc: {bal_acc:.4f}"
    )

    return {
        "fold": fold_idx,
        "endpoint": endpoint_name,
        "fingerprint": fingerprint_type,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "balanced_accuracy": bal_acc
    }


def train_all_models(
    morgan_fps: pd.DataFrame,
    maccs_fps: pd.DataFrame,
    labels_df: pd.DataFrame,
    splits: List[Dict[str, np.ndarray]],
    output_dir: Path
) -> List[Dict[str, Any]]:
    """
    Train models for all folds, endpoints, and fingerprint types.

    Args:
        morgan_fps: Morgan fingerprint dataframe.
        maccs_fps: MACCS fingerprint dataframe.
        labels_df: Labels dataframe.
        splits: List of split configurations.
        output_dir: Directory to save models and metrics.

    Returns:
        List of evaluation results.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir = output_dir / "models"
    model_dir.mkdir(exist_ok=True)

    results = []
    label_cols = [col for col in labels_df.columns if col not in ['SMILES', 'Mol_Wt']]

    logger.info(f"Starting training for {len(splits)} folds and {len(label_cols)} endpoints.")

    for fold_idx, split_data in enumerate(splits):
        train_idx = split_data["train_indices"]
        test_idx = split_data["test_indices"]

        logger.info(f"Processing Fold {fold_idx}: Train={len(train_idx)}, Test={len(test_idx)}")

        # Prepare data for this fold
        X_morgan_train = morgan_fps.iloc[train_idx].values
        X_morgan_test = morgan_fps.iloc[test_idx].values
        X_maccs_train = maccs_fps.iloc[train_idx].values
        X_maccs_test = maccs_fps.iloc[test_idx].values

        for endpoint in label_cols:
            y_train = labels_df.iloc[train_idx][endpoint].values
            y_test = labels_df.iloc[test_idx][endpoint].values

            # Handle missing values in labels
            valid_train_mask = ~np.isnan(y_train)
            valid_test_mask = ~np.isnan(y_test)
            
            if not np.any(valid_train_mask) or not np.any(valid_test_mask):
                logger.warning(f"Skipping {endpoint} in Fold {fold_idx} due to missing labels.")
                continue

            # Align indices for valid data
            valid_train_indices = np.where(valid_train_mask)[0]
            valid_test_indices = np.where(valid_test_mask)[0]

            # Map back to original indices if necessary, but here we just slice the arrays
            # Note: train_idx/test_idx are indices into the full dataframe.
            # We need to map valid_train_indices (0..len-1 relative to train set) back to train_idx
            actual_train_idx = train_idx[valid_train_mask]
            actual_test_idx = test_idx[valid_test_mask]

            y_train_clean = y_train[valid_train_mask]
            y_test_clean = y_test[valid_test_mask]

            X_morgan_train_clean = morgan_fps.iloc[actual_train_idx].values
            X_morgan_test_clean = morgan_fps.iloc[actual_test_idx].values
            X_maccs_train_clean = maccs_fps.iloc[actual_train_idx].values
            X_maccs_test_clean = maccs_fps.iloc[actual_test_idx].values

            # Train Morgan Model
            logger.info(f"  Training Morgan model for {endpoint}...")
            morgan_model = train_single_model(X_morgan_train_clean, y_train_clean)
            
            # Save Morgan Model
            morgan_model_path = model_dir / f"morgan_fold_{fold_idx}_{endpoint}.pkl"
            with open(morgan_model_path, "wb") as f:
                pickle.dump(morgan_model, f)
            
            # Evaluate Morgan Model
            morgan_metrics = evaluate_model(
                morgan_model, X_morgan_test_clean, y_test_clean,
                fold_idx, endpoint, "Morgan"
            )
            results.append(morgan_metrics)

            # Train MACCS Model
            logger.info(f"  Training MACCS model for {endpoint}...")
            maccs_model = train_single_model(X_maccs_train_clean, y_train_clean)

            # Save MACCS Model
            maccs_model_path = model_dir / f"maccs_fold_{fold_idx}_{endpoint}.pkl"
            with open(maccs_model_path, "wb") as f:
                pickle.dump(maccs_model, f)

            # Evaluate MACCS Model
            maccs_metrics = evaluate_model(
                maccs_model, X_maccs_test_clean, y_test_clean,
                fold_idx, endpoint, "MACCS"
            )
            results.append(maccs_metrics)

    # Save results to CSV
    results_df = pd.DataFrame(results)
    results_path = output_dir / "training_metrics.csv"
    results_df.to_csv(results_path, index=False)
    logger.info(f"Saved training metrics to {results_path}")

    return results


def main():
    """Main entry point for training."""
    init_random_seed(42)
    
    # Paths
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data" / "processed"
    output_dir = base_dir / "data" / "processed"
    split_dir = base_dir / "data" / "processed" / "splits"

    logger.info("Starting model training pipeline.")

    try:
        # Load data
        splits = load_split_indices(split_dir)
        morgan_fps, maccs_fps, labels_df, _ = load_fingerprint_data(data_dir)

        # Train all models
        train_all_models(morgan_fps, maccs_fps, labels_df, splits, output_dir)

        logger.info("Training pipeline completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise


if __name__ == "__main__":
    main()