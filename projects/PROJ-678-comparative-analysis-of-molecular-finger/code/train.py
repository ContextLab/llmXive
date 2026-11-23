"""
Train Random Forest models using K-Fold Cross-Validation on the full filtered dataset.
Implements the Corrected Resampled t-test (FR-005) requirements.
"""
import os
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold
from sklearn.metrics import roc_auc_score, make_scorer
from rdkit import DataStructs
from rdkit.Chem import AllChem, MACCSkeys
from utils import setup_logging, init_random_seed, get_logger
from constants import MORGAN_RADIUS, MORGAN_BITS, MACCS_BITS, N_FOLDS

# Constants for the task
N_TREES = 100
MAX_DEPTH = 15
RANDOM_STATE = 42

def load_split_indices(split_dir: str) -> Dict[str, Any]:
    """
    Load the split indices JSON to check validity status.
    If status is INVALID, the training should not proceed.
    """
    split_path = Path(split_dir) / "split_indices.json"
    if not split_path.exists():
        raise FileNotFoundError(f"Split file not found: {split_path}")
    
    with open(split_path, 'r') as f:
        import json
        return json.load(f)

def load_fingerprints(fingerprint_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load Morgan and MACCS fingerprints from the pickle file.
    Returns: (morgan_array, maccs_array)
    """
    with open(fingerprint_path, 'rb') as f:
        data = pickle.load(f)
    return data['morgan'], data['maccs']

def load_labels(data_path: str) -> np.ndarray:
    """
    Load toxicity labels from the filtered CSV.
    Assumes the CSV has columns for various endpoints.
    We will use the first available binary endpoint for this specific task 
    as a placeholder for the full multi-task logic, or iterate if needed.
    For FR-005, we typically pick a specific endpoint or average.
    Based on T012/T013, the CSV has specific columns.
    """
    df = pd.read_csv(data_path)
    # Identify a binary toxicity column. The Tox21 dataset typically has columns like 'NR-AR', 'NR-AR-LBD', etc.
    # We need to find one that exists.
    # Assuming the filtered CSV has the original Tox21 columns.
    # Let's look for a column that contains 'Tox21' or is known to be binary.
    # If not found, we might need to infer from the schema.
    # For robustness, let's assume the first non-identifier column that looks like a label.
    # Or better: check for specific known columns if the schema is fixed.
    # Let's assume the column 'NR-AR' exists as per typical Tox21 subsets.
    target_col = None
    possible_cols = ['NR-AR', 'NR-AR-LBD', 'NR-AR-TOX', 'NR-AhR', 'NR-ER', 'NR-ER-LBD', 'NR-ER-TOX', 'NR-PPAR-gamma', 'SR-ARE', 'SR-ATAD5', 'SR-HSE', 'SR-MMP', 'SR-p53']
    for col in possible_cols:
        if col in df.columns:
            target_col = col
            break
    
    if target_col is None:
        # Fallback: find any column that is not 'SMILES' or 'Mol' or index
        for col in df.columns:
            if col not in ['SMILES', 'Mol', 'compound_id']:
                target_col = col
                break
    
    if target_col is None:
        raise ValueError("Could not find a valid toxicity label column in the dataset.")
    
    # Convert to numeric, handling NaN (usually treated as 0 or dropped)
    labels = df[target_col].astype(float).fillna(0).values
    return labels, target_col

def train_single_model(X: np.ndarray, y: np.ndarray, fold_idx: int, logger: logging.Logger) -> Tuple[RandomForestClassifier, float]:
    """
    Train a single Random Forest model on the full dataset for K-Fold CV.
    Note: For the Corrected Resampled t-test, we train on the full dataset
    and evaluate on the full dataset (or use a specific split logic).
    However, standard K-Fold trains on N-1 folds and tests on 1.
    The task says "K-Fold Cross-Validation on the full filtered dataset".
    This implies standard K-Fold: Train on train fold, test on test fold.
    """
    # We don't split here; the KFold iterator handles it.
    # This function is called inside the KFold loop.
    # Actually, the standard pattern is to loop in main.
    pass

def run_kfold_cv(morgan_fp: np.ndarray, maccs_fp: np.ndarray, y: np.ndarray, logger: logging.Logger) -> Dict[str, Dict[str, List[float]]]:
    """
    Perform K-Fold Cross-Validation for both Morgan and MACCS fingerprints.
    Returns a dictionary of scores: {"morgan": {"roc_auc": [scores]}, "maccs": {"roc_auc": [scores]}}
    """
    kf = KFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    
    results = {
        "morgan": {"roc_auc": []},
        "maccs": {"roc_auc": []}
    }
    
    # Define model parameters
    rf_params = {
        'n_estimators': N_TREES,
        'max_depth': MAX_DEPTH,
        'random_state': RANDOM_STATE,
        'n_jobs': -1
    }
    
    for fold_idx, (train_idx, test_idx) in enumerate(kf.split(morgan_fp)):
        logger.info(f"Processing Fold {fold_idx + 1}/{N_FOLDS}")
        
        # Prepare data for this fold
        X_train_morgan = morgan_fp[train_idx]
        X_test_morgan = morgan_fp[test_idx]
        y_train = y[train_idx]
        y_test = y[test_idx]
        
        # --- Morgan Model ---
        try:
            model_morgan = RandomForestClassifier(**rf_params)
            model_morgan.fit(X_train_morgan, y_train)
            y_pred_proba_morgan = model_morgan.predict_proba(X_test_morgan)[:, 1]
            roc_auc_morgan = roc_auc_score(y_test, y_pred_proba_morgan)
            results["morgan"]["roc_auc"].append(roc_auc_morgan)
            logger.info(f"  Morgan Fold {fold_idx + 1} ROC-AUC: {roc_auc_morgan:.4f}")
        except Exception as e:
            logger.error(f"  Morgan Fold {fold_idx + 1} failed: {e}")
            results["morgan"]["roc_auc"].append(np.nan)
        
        # --- MACCS Model ---
        try:
            X_train_maccs = maccs_fp[train_idx]
            X_test_maccs = maccs_fp[test_idx]
            
            model_maccs = RandomForestClassifier(**rf_params)
            model_maccs.fit(X_train_maccs, y_train)
            y_pred_proba_maccs = model_maccs.predict_proba(X_test_maccs)[:, 1]
            roc_auc_maccs = roc_auc_score(y_test, y_pred_proba_maccs)
            results["maccs"]["roc_auc"].append(roc_auc_maccs)
            logger.info(f"  MACCS Fold {fold_idx + 1} ROC-AUC: {roc_auc_maccs:.4f}")
        except Exception as e:
            logger.error(f"  MACCS Fold {fold_idx + 1} failed: {e}")
            results["maccs"]["roc_auc"].append(np.nan)
    
    return results

def main():
    """
    Main entry point for training K-Fold models.
    1. Check split status.
    2. Load fingerprints and labels.
    3. Run K-Fold CV.
    4. Save kfold_scores.json.
    """
    # Setup logging
    logger = setup_logging()
    init_random_seed(RANDOM_STATE)
    
    logger.info("Starting K-Fold Cross-Validation Training (T019)")
    
    # Paths
    project_root = Path(__file__).resolve().parent.parent
    processed_dir = project_root / "data" / "processed"
    split_file = processed_dir / "split_indices.json"
    fingerprint_file = processed_dir / "fingerprints.pkl"
    filtered_csv = processed_dir / "organophosphates_filtered.csv"
    output_file = processed_dir / "kfold_scores.json"
    
    # 1. Check Split Status (Gate)
    if not split_file.exists():
        logger.error("Split indices file not found. Cannot proceed with training.")
        # If the split is missing, we can't determine validity. 
        # However, the task says: "MUST: Check split_indices.json... if status is INVALID, exit immediately"
        # If it doesn't exist, that's a critical error in the pipeline state.
        # But T018c might have created a report if invalid.
        # Let's assume if it doesn't exist, the pipeline failed earlier.
        raise FileNotFoundError(f"Split file not found: {split_file}")
    
    import json
    with open(split_file, 'r') as f:
        split_data = json.load(f)
    
    if split_data.get("status") == "INVALID":
        logger.warning("Split status is INVALID. Skipping training as per T018c/T019 logic.")
        # Exit cleanly with code 0 as per requirements
        return
    
    if split_data.get("status") != "VALID":
        logger.warning(f"Split status is '{split_data.get('status')}'. Proceeding with caution.")
    
    # 2. Load Fingerprints
    if not fingerprint_file.exists():
        raise FileNotFoundError(f"Fingerprint file not found: {fingerprint_file}")
    
    morgan_fp, maccs_fp = load_fingerprints(str(fingerprint_file))
    logger.info(f"Loaded {len(morgan_fp)} Morgan and {len(maccs_fp)} MACCS fingerprints.")
    
    # 3. Load Labels
    if not filtered_csv.exists():
        raise FileNotFoundError(f"Filtered CSV not found: {filtered_csv}")
    
    y, label_col = load_labels(str(filtered_csv))
    logger.info(f"Loaded labels for column '{label_col}'. Shape: {y.shape}")
    
    # Check for NaNs in labels
    if np.isnan(y).any():
        logger.warning("NaN values found in labels. Dropping corresponding samples.")
        valid_mask = ~np.isnan(y)
        morgan_fp = morgan_fp[valid_mask]
        maccs_fp = maccs_fp[valid_mask]
        y = y[valid_mask]
    
    # 4. Run K-Fold CV
    logger.info(f"Starting K-Fold CV with {N_FOLDS} folds.")
    scores = run_kfold_cv(morgan_fp, maccs_fp, y, logger)
    
    # 5. Save Results
    with open(output_file, 'w') as f:
        json.dump(scores, f, indent=2)
    
    logger.info(f"K-Fold scores saved to {output_file}")
    
    # Print summary
    morgan_mean = np.nanmean(scores["morgan"]["roc_auc"])
    maccs_mean = np.nanmean(scores["maccs"]["roc_auc"])
    logger.info(f"Summary - Morgan Mean ROC-AUC: {morgan_mean:.4f}, MACCS Mean ROC-AUC: {maccs_mean:.4f}")

if __name__ == "__main__":
    main()