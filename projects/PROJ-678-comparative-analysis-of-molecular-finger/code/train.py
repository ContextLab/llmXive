import os
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd

from utils import setup_logging, init_random_seed, get_logger
from fingerprints import generate_fingerprints_batch
from constants import MORGAN_RADIUS, MORGAN_BITS, MACCS_BITS, N_FOLDS

def load_split_indices(split_dir: str) -> Dict[int, Dict[str, List[int]]]:
    """Load split indices from disk."""
    logger = get_logger(__name__)
    split_path = Path(split_dir)
    splits = {}

    for i in range(N_FOLDS):
        file_path = split_path / f"split_fold_{i}.pkl"
        if not file_path.exists():
            raise FileNotFoundError(f"Split file not found: {file_path}")
        with open(file_path, 'rb') as f:
            splits[i] = pickle.load(f)

    return splits

def load_fingerprint_data(csv_path: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load SMILES and labels, generate Morgan fingerprints.
    Returns: (fingerprints_array, labels_array, endpoint_names)
    """
    logger = get_logger(__name__)
    df = pd.read_csv(csv_path)
    
    # Ensure 'smiles' column exists
    if 'smiles' not in df.columns:
        raise ValueError(f"CSV must contain 'smiles' column. Found: {df.columns.tolist()}")
    
    smiles_list = df['smiles'].tolist()
    
    # Identify label columns (exclude 'smiles' and 'mol' if present)
    exclude_cols = ['smiles', 'mol']
    label_cols = [c for c in df.columns if c not in exclude_cols]
    
    if not label_cols:
        raise ValueError("No label columns found in CSV after excluding 'smiles' and 'mol'.")
    
    logger.info(f"Found {len(label_cols)} toxicity endpoints: {label_cols}")
    
    # Generate Morgan fingerprints (radius=2, 2048 bits)
    logger.info(f"Generating Morgan fingerprints (radius={MORGAN_RADIUS}, bits={MORGAN_BITS})...")
    fps, _ = generate_fingerprints_batch(smiles_list, fp_type="morgan")
    
    # Extract labels for all endpoints
    labels_df = df[label_cols]
    # Convert to numpy array: shape (n_samples, n_endpoints)
    labels_array = labels_df.to_numpy()
    
    logger.info(f"Loaded {len(smiles_list)} compounds with {len(label_cols)} endpoints.")
    
    return fps, labels_array, label_cols

def train_single_model(X_train, y_train, random_state=42):
    """Train a Random Forest model."""
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=random_state, n_jobs=1)
    model.fit(X_train, y_train)
    return model

def evaluate_model(model, X_test, y_test):
    """Evaluate model and return metrics."""
    from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, balanced_accuracy_score
    
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Ensure y_test is binary and has both classes
    if len(np.unique(y_test)) < 2:
        return None, None, None

    try:
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        precision, recall, _ = precision_recall_curve(y_test, y_pred_proba)
        pr_auc = auc(recall, precision)
        bal_acc = balanced_accuracy_score(y_test, model.predict(X_test))
        return roc_auc, pr_auc, bal_acc
    except Exception as e:
        logging.warning(f"Error evaluating model: {e}")
        return None, None, None

def train_all_models(fps: np.ndarray, labels: np.ndarray, labels_names: List[str], splits: Dict[int, Dict[str, List[int]]], output_dir: str):
    """Train models for all folds and both fingerprint types."""
    logger = get_logger(__name__)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # We need to generate MACCS fingerprints as well for the second model
    logger.info("Generating MACCS fingerprints for all compounds...")
    smiles_list = pd.read_csv("data/processed/organophosphates_filtered.csv")['smiles'].tolist()
    maccs_fps, _ = generate_fingerprints_batch(smiles_list, fp_type="maccs")

    n_endpoints = len(labels_names)

    for fold_idx in range(N_FOLDS):
        logger.info(f"Processing fold {fold_idx}...")
        if fold_idx not in splits:
            logger.error(f"Fold {fold_idx} missing from splits.")
            continue
        
        indices = splits[fold_idx]
        train_idx = indices['train']
        test_idx = indices['test']

        # Morgan Model
        logger.info(f"Fold {fold_idx}: Training Morgan Random Forest...")
        X_train_morgan = fps[train_idx]
        X_test_morgan = fps[test_idx]
        
        morgan_models = {}
        for ep_idx, ep_name in enumerate(labels_names):
            y_train = labels[train_idx, ep_idx]
            model = train_single_model(X_train_morgan, y_train)
            morgan_models[ep_name] = model
        
        # Save Morgan models
        morgan_save_path = output_path / f"morgan_fold_{fold_idx}.pkl"
        with open(morgan_save_path, 'wb') as f:
            pickle.dump(morgan_models, f)
        logger.info(f"Saved Morgan models to {morgan_save_path}")

        # MACCS Model
        logger.info(f"Fold {fold_idx}: Training MACCS Random Forest...")
        X_train_maccs = maccs_fps[train_idx]
        X_test_maccs = maccs_fps[test_idx]
        
        maccs_models = {}
        for ep_idx, ep_name in enumerate(labels_names):
            y_train = labels[train_idx, ep_idx]
            model = train_single_model(X_train_maccs, y_train)
            maccs_models[ep_name] = model
        
        # Save MACCS models
        maccs_save_path = output_path / f"maccs_fold_{fold_idx}.pkl"
        with open(maccs_save_path, 'wb') as f:
            pickle.dump(maccs_models, f)
        logger.info(f"Saved MACCS models to {maccs_save_path}")

    logger.info("All models trained and saved.")

def main():
    """Main entry point for training."""
    setup_logging()
    init_random_seed()
    logger = get_logger(__name__)

    split_dir = Path("data/processed/splits")
    data_file = Path("data/processed/organophosphates_filtered.csv")
    model_dir = Path("data/processed/models")

    # Check dependencies
    if not split_dir.exists():
        logger.error(f"Split directory not found: {split_dir}")
        raise FileNotFoundError(f"Split directory not found: {split_dir}")

    if not data_file.exists():
        logger.error(f"Data file not found: {data_file}")
        raise FileNotFoundError(f"Data file not found: {data_file}")

    logger.info("Loading splits...")
    splits = load_split_indices(str(split_dir))

    logger.info("Loading fingerprint data...")
    fps, labels, labels_names = load_fingerprint_data(str(data_file))

    logger.info("Training models...")
    train_all_models(fps, labels, labels_names, splits, str(model_dir))

    logger.info("Training complete.")

if __name__ == "__main__":
    main()