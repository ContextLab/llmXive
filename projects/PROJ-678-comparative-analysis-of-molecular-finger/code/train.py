"""
Train Random Forest models for each fold of the 5-Fold Greedy Maximal Dissimilarity Split.

This script:
1. Checks data/processed/split_summary.json for validity.
2. If INVALID, exits immediately with code 0 (no training).
3. If VALID, loads fingerprint data and split indices.
4. Trains two Random Forest models (Morgan and MACCS) for EACH of the 5 folds.
5. Saves model artifacts to data/processed/models/.
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
import json

# Import utilities from the project's utils module
from utils import setup_logging, init_random_seed, get_logger

# Constants
RANDOM_SEED = 42
N_TREES = 100
MAX_DEPTH = 15
SPLIT_SUMMARY_PATH = "data/processed/split_summary.json"
SPLIT_DIR = "data/processed/splits"
MODEL_DIR = "data/processed/models"
FINGERPRINT_FILE = "data/processed/fingerprints.pkl"
LABELS_FILE = "data/processed/labels.pkl"

def load_split_indices(split_dir: str) -> Dict[int, Dict[str, List[int]]]:
    """
    Load split indices from individual fold files.
    
    Args:
        split_dir: Path to the directory containing split_fold_{i}.json files.
        
    Returns:
        Dictionary mapping fold index to a dict with 'train_indices' and 'test_indices'.
        
    Raises:
        FileNotFoundError: If any expected split file is missing.
    """
    split_dir_path = Path(split_dir)
    splits = {}
    
    for fold in range(5):
        split_file = split_dir_path / f"split_fold_{fold}.json"
        if not split_file.exists():
            raise FileNotFoundError(f"Split file not found: {split_file}")
        
        with open(split_file, 'r') as f:
            fold_data = json.load(f)
            splits[fold] = {
                'train_indices': fold_data['train_indices'],
                'test_indices': fold_data['test_indices']
            }
            
    return splits

def load_fingerprint_data(fingerprint_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load pre-computed Morgan and MACCS fingerprints.
    
    Args:
        fingerprint_path: Path to the fingerprints pickle file.
        
    Returns:
        Tuple of (morgan_fingerprints, maccs_fingerprints) as numpy arrays.
    """
    with open(fingerprint_path, 'rb') as f:
        data = pickle.load(f)
        
    morgan_fp = np.array(data['morgan'])
    maccs_fp = np.array(data['maccs'])
    
    return morgan_fp, maccs_fp

def load_labels(labels_path: str) -> pd.DataFrame:
    """
    Load toxicity labels.
    
    Args:
        labels_path: Path to the labels pickle file.
        
    Returns:
        DataFrame containing toxicity labels.
    """
    with open(labels_path, 'rb') as f:
        labels = pickle.load(f)
    return labels

def train_single_model(X_train: np.ndarray, y_train: np.ndarray, 
                       n_trees: int, max_depth: int, seed: int) -> RandomForestClassifier:
    """
    Train a single Random Forest model.
    
    Args:
        X_train: Training features.
        y_train: Training labels.
        n_trees: Number of trees in the forest.
        max_depth: Maximum depth of the tree.
        seed: Random seed for reproducibility.
        
    Returns:
        Trained RandomForestClassifier.
    """
    model = RandomForestClassifier(
        n_estimators=n_trees,
        max_depth=max_depth,
        random_state=seed,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    return model

def evaluate_model(model: RandomForestClassifier, X_test: np.ndarray, 
                   y_test: np.ndarray) -> Dict[str, float]:
    """
    Evaluate a model on test data.
    
    Args:
        model: Trained model.
        X_test: Test features.
        y_test: Test labels.
        
    Returns:
        Dictionary with ROC-AUC, PR-AUC, and Balanced Accuracy.
    """
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)
    
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
    pr_auc = auc(recall, precision)
    bal_acc = balanced_accuracy_score(y_test, y_pred)
    
    return {
        'roc_auc': roc_auc,
        'pr_auc': pr_auc,
        'balanced_acc': bal_acc
    }

def train_all_models(splits: Dict[int, Dict[str, List[int]]], 
                     morgan_fp: np.ndarray, 
                     maccs_fp: np.ndarray, 
                     labels: pd.DataFrame,
                     logger: logging.Logger) -> Dict[int, Dict[str, Dict[str, Any]]]:
    """
    Train models for all folds and save artifacts.
    
    Args:
        splits: Dictionary of split indices.
        morgan_fp: Morgan fingerprints array.
        maccs_fp: MACCS fingerprints array.
        labels: DataFrame of labels.
        logger: Logger instance.
        
    Returns:
        Dictionary of model metrics per fold.
    """
    # Ensure model directory exists
    model_path = Path(MODEL_DIR)
    model_path.mkdir(parents=True, exist_ok=True)
    
    all_metrics = {}
    
    for fold_idx, fold_data in splits.items():
        logger.info(f"Processing Fold {fold_idx}")
        
        train_idx = fold_data['train_indices']
        test_idx = fold_data['test_indices']
        
        # Prepare data for Morgan
        X_train_morgan = morgan_fp[train_idx]
        X_test_morgan = morgan_fp[test_idx]
        
        # Prepare data for MACCS
        X_train_maccs = maccs_fp[train_idx]
        X_test_maccs = maccs_fp[test_idx]
        
        # Get labels for all endpoints (assuming binary classification for now)
        # We will train one model per endpoint if multiple exist, or aggregate if single
        # For this implementation, we assume a single binary label column 'toxic' or similar
        # If multiple endpoints exist, we iterate. For simplicity in this task, we assume
        # the labels dataframe has a column 'label' or we pick the first non-ID column.
        
        # Identify the target column
        target_cols = [col for col in labels.columns if col not in ['SMILES', 'Compound_ID', 'id']]
        if not target_cols:
            logger.warning(f"No target columns found in labels for fold {fold_idx}. Skipping.")
            continue
            
        # For this task, we assume the first target column is the label.
        # In a real scenario, we might loop through all.
        target_col = target_cols[0]
        y_train = labels.loc[train_idx, target_col].values
        y_test = labels.loc[test_idx, target_col].values
        
        # Handle NaN or missing values if any
        if np.any(np.isnan(y_train)) or np.any(np.isnan(y_test)):
            logger.error(f"NaN values detected in labels for fold {fold_idx}. Skipping.")
            continue

        # Train Morgan Model
        logger.info(f"Training Morgan Model for Fold {fold_idx} on {target_col}")
        morgan_model = train_single_model(
            X_train_morgan, y_train, N_TREES, MAX_DEPTH, RANDOM_SEED
        )
        morgan_metrics = evaluate_model(morgan_model, X_test_morgan, y_test)
        
        # Save Morgan Model
        morgan_artifact_path = model_path / f"morgan_fold_{fold_idx}.pkl"
        with open(morgan_artifact_path, 'wb') as f:
            pickle.dump({
                'model': morgan_model,
                'metrics': morgan_metrics,
                'fold': fold_idx,
                'target': target_col
            }, f)
        logger.info(f"Saved Morgan model to {morgan_artifact_path}")
        
        # Train MACCS Model
        logger.info(f"Training MACCS Model for Fold {fold_idx} on {target_col}")
        maccs_model = train_single_model(
            X_train_maccs, y_train, N_TREES, MAX_DEPTH, RANDOM_SEED
        )
        maccs_metrics = evaluate_model(maccs_model, X_test_maccs, y_test)
        
        # Save MACCS Model
        maccs_artifact_path = model_path / f"maccs_fold_{fold_idx}.pkl"
        with open(maccs_artifact_path, 'wb') as f:
            pickle.dump({
                'model': maccs_model,
                'metrics': maccs_metrics,
                'fold': fold_idx,
                'target': target_col
            }, f)
        logger.info(f"Saved MACCS model to {maccs_artifact_path}")
        
        all_metrics[fold_idx] = {
            'morgan': morgan_metrics,
            'maccs': maccs_metrics
        }
        
    return all_metrics

def main():
    """Main entry point for training."""
    # Setup logging
    logger = setup_logging("code/train.py")
    init_random_seed(RANDOM_SEED)
    
    logger.info("Starting Training Pipeline")
    
    # 1. Check split_summary.json for validity
    summary_path = Path(SPLIT_SUMMARY_PATH)
    if not summary_path.exists():
        logger.error(f"Split summary file not found: {SPLIT_SUMMARY_PATH}")
        # If the summary doesn't exist, we cannot proceed safely.
        # However, the task says "if status is INVALID, exit 0".
        # If the file is missing, it's an error state.
        raise FileNotFoundError(f"Required file missing: {SPLIT_SUMMARY_PATH}")
    
    with open(summary_path, 'r') as f:
        summary = json.load(f)
        
    status = summary.get('status', 'UNKNOWN')
    logger.info(f"Split Summary Status: {status}")
    
    if status == "INVALID":
        logger.info("Status is INVALID. Exiting immediately with code 0 (no training).")
        # Exit cleanly as per requirement
        return 0
        
    if status != "VALID":
        logger.warning(f"Unknown status '{status}'. Proceeding with caution, but training might fail.")
        
    # 2. Load Data
    logger.info("Loading Split Indices...")
    try:
        splits = load_split_indices(SPLIT_DIR)
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
        
    logger.info("Loading Fingerprints...")
    if not Path(FINGERPRINT_FILE).exists():
        raise FileNotFoundError(f"Fingerprint file not found: {FINGERPRINT_FILE}")
    morgan_fp, maccs_fp = load_fingerprint_data(FINGERPRINT_FILE)
    
    logger.info("Loading Labels...")
    if not Path(LABELS_FILE).exists():
        raise FileNotFoundError(f"Labels file not found: {LABELS_FILE}")
    labels = load_labels(LABELS_FILE)
    
    # 3. Train Models
    logger.info(f"Training {N_TREES} trees, max_depth={MAX_DEPTH} for 5 folds...")
    metrics = train_all_models(splits, morgan_fp, maccs_fp, labels, logger)
    
    # 4. Save Summary Metrics
    metrics_path = Path("data/processed/training_metrics.json")
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Training metrics saved to {metrics_path}")
    
    logger.info("Training Pipeline Completed Successfully.")
    return 0

if __name__ == "__main__":
    exit(main())