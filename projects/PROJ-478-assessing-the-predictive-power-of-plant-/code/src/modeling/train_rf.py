"""
Train a Random Forest classifier for Species Distribution Modeling (climate-only).

This module implements the core training logic for User Story 1 (US1),
training a Random Forest model using climate variables only. It performs
5-fold cross-validation as per the Spec Constitution (SC-001) and calculates
AUC and TSS metrics (SC-002).

Requirements:
- Uses max_depth=10 and n_estimators=100 as per config constraints.
- Reads processed climate data and occurrence labels from data/processed/.
- Outputs model artifacts and metrics to results/.
"""

import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, confusion_matrix
from sklearn.preprocessing import StandardScaler

# Project imports
from src.utils.logging import get_logger, log_provenance, log_error
from src.utils.config import RANDOM_SEED, MAX_DEPTH, N_ESTIMATORS
from src.modeling.metrics import calculate_auc, calculate_tss

# Ensure project root is in path if running as script
if __name__ == "__main__" and "code" not in sys.path[0]:
    code_root = Path(__file__).resolve().parent.parent.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))

logger = get_logger(__name__)

# Constants for file paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def load_climate_features(species_name: str) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Load climate features and labels for a specific species from processed data.

    Expected file: data/processed/{species_name}_climate_features.csv
    Columns: [feature1, feature2, ..., 'label']

    Args:
        species_name: The scientific name of the species (e.g., 'Helianthus_annuus')

    Returns:
        X: Feature matrix (numpy array)
        y: Labels (numpy array)
        feature_names: List of feature column names
    """
    file_path = PROCESSED_DATA_DIR / f"{species_name}_climate_features.csv"

    if not file_path.exists():
        raise FileNotFoundError(f"Climate features file not found: {file_path}")

    logger.info(f"Loading climate features from {file_path}")
    df = pd.read_csv(file_path)

    if 'label' not in df.columns:
        raise ValueError(f"Column 'label' not found in {file_path}. Expected columns: {df.columns.tolist()}")

    feature_names = [col for col in df.columns if col != 'label']
    X = df[feature_names].values
    y = df['label'].values

    logger.info(f"Loaded {len(y)} samples with {len(feature_names)} features for {species_name}")
    return X, y, feature_names

def train_random_forest_cv(
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int = 5,
    random_state: int = RANDOM_SEED
) -> Dict[str, Any]:
    """
    Train a Random Forest classifier using 5-fold stratified cross-validation.

    This function adheres to the Spec Constitution (SC-001) by using 5-fold CV
    and calculating AUC and TSS (SC-002).

    Args:
        X: Feature matrix
        y: Target labels
        n_splits: Number of CV folds (default 5)
        random_state: Random seed for reproducibility

    Returns:
        Dictionary containing:
            - model: The trained RandomForestClassifier (fitted on full data)
            - cv_auc: Mean AUC score from cross-validation
            - cv_tss: Mean TSS score from cross-validation
            - cv_predictions: Predicted probabilities from CV
            - cv_labels: True labels from CV
            - feature_importance: Dict of feature names to importance scores
    """
    logger.info(f"Starting 5-fold stratified cross-validation (n_estimators={N_ESTIMATORS}, max_depth={MAX_DEPTH})")

    # Initialize the model with constrained hyperparameters
    rf_model = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        random_state=random_state,
        n_jobs=-1,
        class_weight='balanced'  # Handle potential class imbalance
    )

    # Setup CV strategy
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)

    # Get cross-validated predictions (probability of positive class)
    # This predicts on the held-out fold for each sample
    cv_proba = cross_val_predict(rf_model, X, y, cv=cv, method='predict_proba')[:, 1]

    # Calculate metrics on CV predictions
    auc_score = calculate_auc(y, cv_proba)
    tss_score = calculate_tss(y, cv_proba)

    logger.info(f"Cross-validation AUC: {auc_score:.4f}")
    logger.info(f"Cross-validation TSS: {tss_score:.4f}")

    # Train the final model on the full dataset for feature importance and deployment
    logger.info("Training final model on full dataset...")
    rf_model.fit(X, y)

    # Calculate feature importance
    feature_importance = dict(zip(
        [f"f{i}" for i in range(X.shape[1])],  # Placeholder names if not passed
        rf_model.feature_importances_
    ))

    return {
        'model': rf_model,
        'cv_auc': auc_score,
        'cv_tss': tss_score,
        'cv_predictions': cv_proba,
        'cv_labels': y,
        'feature_importance': feature_importance
    }

def save_results(
    species_name: str,
    results: Dict[str, Any],
    feature_names: List[str]
) -> None:
    """
    Save model results and metrics to JSON and pickle files.

    Outputs:
        - results/{species_name}_model_results.json
        - results/{species_name}_model.pkl
    """
    # Prepare metrics report
    metrics_report = {
        'species': species_name,
        'model_type': 'RandomForest',
        'hyperparameters': {
            'n_estimators': N_ESTIMATORS,
            'max_depth': MAX_DEPTH,
            'random_state': RANDOM_SEED
        },
        'cross_validation': {
            'n_splits': 5,
            'auc': results['cv_auc'],
            'tss': results['cv_tss']
        },
        'feature_importance': results['feature_importance']
    }

    # Save JSON report
    json_path = RESULTS_DIR / f"{species_name}_model_results.json"
    with open(json_path, 'w') as f:
        json.dump(metrics_report, f, indent=2)
    logger.info(f"Saved metrics report to {json_path}")

    # Save model pickle
    pkl_path = RESULTS_DIR / f"{species_name}_model.pkl"
    with open(pkl_path, 'wb') as f:
        pickle.dump(results['model'], f)
    logger.info(f"Saved model to {pkl_path}")

    # Save CV predictions for further analysis (optional but useful)
    pred_path = RESULTS_DIR / f"{species_name}_cv_predictions.csv"
    pred_df = pd.DataFrame({
        'true_label': results['cv_labels'],
        'predicted_proba': results['cv_predictions']
    })
    pred_df.to_csv(pred_path, index=False)
    logger.info(f"Saved CV predictions to {pred_path}")

def run_training_pipeline(species_name: str) -> Dict[str, Any]:
    """
    Main entry point for the training pipeline.

    Args:
        species_name: The scientific name of the species to model.

    Returns:
        Dictionary containing the full results of the training run.
    """
    logger.info(f"--- Starting Training Pipeline for {species_name} ---")

    try:
        # 1. Load Data
        X, y, feature_names = load_climate_features(species_name)

        # 2. Train Model with CV
        results = train_random_forest_cv(X, y)

        # 3. Update feature importance with real names
        results['feature_importance'] = dict(zip(feature_names, results['feature_importance']))

        # 4. Save Results
        save_results(species_name, results, feature_names)

        logger.info(f"--- Training Pipeline Complete for {species_name} ---")
        return results

    except FileNotFoundError as e:
        log_error(logger, str(e), "Data loading failed")
        raise
    except Exception as e:
        log_error(logger, str(e), "Training pipeline failed")
        raise

if __name__ == "__main__":
    # Example usage: python -m src.modeling.train_rf Helianthus_annuus
    # Or simply run without args if a default species is configured, but here we require an arg.
    if len(sys.argv) < 2:
        logger.error("Usage: python -m src.modeling.train_rf <species_name>")
        logger.error("Example: python -m src.modeling.train_rf Helianthus_annuus")
        sys.exit(1)

    species = sys.argv[1]
    setup_logging = True # Ensure logging is set up if running directly

    # Setup logging if not already done (usually handled by main entry point)
    from src.utils.logging import setup_logging as setup_log
    setup_log()

    run_training_pipeline(species)
