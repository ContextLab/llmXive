import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pickle
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from statsmodels.stats.multitest import multipletests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_convergence_results(filepath: str) -> pd.DataFrame:
    """Load convergence results from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Convergence results not found at {filepath}")
    df = pd.read_csv(filepath)
    # Ensure required columns exist
    required_cols = ['task_id', 'k', 'is_correct', 'first_correct_step', 'censored']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in convergence results: {missing}")
    return df

def load_entropy_results(filepath: str) -> pd.DataFrame:
    """Load entropy results from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Entropy results not found at {filepath}")
    df = pd.read_csv(filepath)
    required_cols = ['task_id', 'entropy']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in entropy results: {missing}")
    return df

def load_baseline_pass1(filepath: str) -> pd.DataFrame:
    """Load baseline pass@1 values from JSON."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline pass@1 not found at {filepath}")
    with open(filepath, 'r') as f:
        data = json.load(f)
    # Expecting a list of dicts or a dict with 'values' key
    if isinstance(data, list):
        return pd.DataFrame(data)
    elif isinstance(data, dict) and 'values' in data:
        return pd.DataFrame(data['values'])
    else:
        # Try to convert dict to DF
        return pd.DataFrame([data])

def align_data_for_router(entropy_df: pd.DataFrame, convergence_df: pd.DataFrame, baseline_df: pd.DataFrame) -> pd.DataFrame:
    """Merge entropy, convergence, and baseline data on task_id."""
    # Get first_correct_step per task_id (aggregating if multiple k rows exist)
    # For T019, we use the 'first_correct_step' as the target ordinal variable.
    # If a task is censored, first_correct_step is set to k_max (e.g., 3) as per T013a.
    # We take the row where k is max or the one that determined the step.
    # Simplified: take the row with max k for each task_id, or the one where censored=True if applicable.
    # Actually, T013a writes one row per k. We need the "optimal_k" which is first_correct_step.
    # We can group by task_id and take the first_correct_step value (should be consistent across k rows for the same task if logic holds,
    # but T013a writes multiple rows. We need the 'target' which is the first_correct_step determined by the loop.
    # Let's assume the 'first_correct_step' column is the same for all k rows of a task_id (it represents the convergence point).
    # If not, we take the minimum k where is_correct is True, or k_max if censored.
    
    # Strategy: Group by task_id, compute the 'optimal_k' (target) as:
    # min(k where is_correct==True) if exists, else k_max (3).
    # But T013a already computed 'first_correct_step' and 'censored'.
    # Let's just take the 'first_correct_step' from the row where k == first_correct_step (if exists) or the last row.
    
    # Robust approach:
    # 1. For each task_id, find the smallest k where is_correct is True.
    # 2. If none, use k_max (3).
    # This matches the definition of "optimal_k" in T019.
    
    convergence_df['is_correct_bool'] = convergence_df['is_correct'].astype(bool)
    def get_optimal_k(group):
        correct_k = group[group['is_correct_bool']]['k']
        if len(correct_k) > 0:
            return correct_k.min()
        else:
            # If censored, the task failed up to k_max. T013a sets first_correct_step = k_max in that case.
            # We use 3 as the fallback for k_max in this specific task context (k_range 1-3).
            return 3 
    
    # However, T013a says: "set first_correct_step = k_max if censored".
    # So we can just take the 'first_correct_step' from the last row of the task_id group (since it's updated sequentially).
    # Or simply take the max of first_correct_step? No, it's the same.
    # Let's take the first_correct_step from the row with the highest k (which should have the final determination).
    group_max_k = convergence_df.sort_values('k').groupby('task_id').last()
    group_max_k = group_max_k.reset_index()
    
    # Merge with entropy
    merged = pd.merge(group_max_k, entropy_df[['task_id', 'entropy']], on='task_id', how='inner')
    
    # Merge with baseline (assuming baseline has 'task_id' and 'pass1' or similar)
    # T004i says baseline_pass1.json. Let's assume it has 'task_id' and 'pass1'.
    if 'pass1' not in baseline_df.columns and 'baseline_pass1' in baseline_df.columns:
        baseline_df = baseline_df.rename(columns={'baseline_pass1': 'pass1'})
    if 'task_id' not in baseline_df.columns:
        # Fallback: assume index is task_id or first column is task_id
        if len(baseline_df.columns) > 0:
            baseline_df = baseline_df.rename(columns={baseline_df.columns[0]: 'task_id'})
    
    merged = pd.merge(merged, baseline_df[['task_id', 'pass1']], on='task_id', how='left')
    merged['pass1'] = merged['pass1'].fillna(0.0) # Default to 0 if missing
    
    # Define target variable: optimal_k (1, 2, or 3)
    # T019 says: "optimal_k = first_correct_step (or 3 if censored)"
    merged['optimal_k'] = merged['first_correct_step'].fillna(3).astype(int)
    
    # Ensure optimal_k is within 1-3 (if T013a logic was different)
    merged['optimal_k'] = merged['optimal_k'].clip(1, 3)
    
    return merged

def train_ordinal_logistic_router(X: np.ndarray, y: np.ndarray, cv_folds: int = 5, random_state: int = 42) -> Tuple[Any, Dict[str, Any]]:
    """
    Train an Ordinal Logistic Regression router using 5-fold StratifiedKFold.
    Returns the trained model (averaged or best) and a dict of fold metrics.
    Note: sklearn's LogisticRegression is not strictly ordinal by default, but we treat y as ordinal classes.
    For true ordinal logistic regression, one might use statsmodels or mlogit, but sklearn's Categorical/Ordinal handling
    with 'multinomial' or 'ovr' is often used as a proxy in such pipelines unless a specific ordinal package is available.
    Given the constraints and imports, we use LogisticRegression with 'multinomial' solver.
    """
    # Use StratifiedKFold for the target variable (optimal_k)
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    
    fold_metrics = []
    models = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Train model
        # Using LogisticRegression with multinomial solver for multi-class (ordinal)
        model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=1000, random_state=random_state)
        model.fit(X_train, y_train)
        models.append(model)
        
        # Predict
        y_pred = model.predict(X_test)
        
        # Metrics
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted') # weighted for ordinal classes
        cm = confusion_matrix(y_test, y_pred)
        
        fold_metrics.append({
            'fold': fold_idx + 1,
            'accuracy': acc,
            'f1_score': f1,
            'confusion_matrix': cm.tolist()
        })
        logger.info(f"Fold {fold_idx+1}: Accuracy={acc:.4f}, F1={f1:.4f}")
    
    # Aggregate metrics
    avg_acc = np.mean([m['accuracy'] for m in fold_metrics])
    avg_f1 = np.mean([m['f1_score'] for m in fold_metrics])
    
    # For the final model, we can use the one trained on the full data or an ensemble.
    # Here we retrain on full data for the final model artifact.
    final_model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=1000, random_state=random_state)
    final_model.fit(X, y)
    
    metrics_summary = {
        'cv_folds': cv_folds,
        'mean_accuracy': avg_acc,
        'mean_f1_score': avg_f1,
        'fold_details': fold_metrics
    }
    
    return final_model, metrics_summary

def save_cv_fold_metrics(metrics: Dict[str, Any], output_path: str):
    """Save the cross-validation fold metrics to JSON."""
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved CV fold metrics to {output_path}")

def evaluate_router(model, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
    """Evaluate the router on a test set."""
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average='weighted')
    cm = confusion_matrix(y_test, y_pred)
    return {
        'accuracy': acc,
        'f1_score': f1,
        'confusion_matrix': cm.tolist()
    }

def main():
    """
    Main function for T019c: Explicit 5-Fold CV Implementation.
    Loads data, trains router with StratifiedKFold, logs metrics per fold.
    """
    # Paths
    entropy_path = 'data/processed/entropy_results.csv'
    convergence_path = 'data/processed/convergence_results_core.csv'
    baseline_path = 'data/processed/baseline_pass1.json'
    output_model_path = 'data/processed/router_model.pkl'
    output_metrics_path = 'data/processed/router_metrics.json'
    output_cv_folds_path = 'data/processed/router_cv_folds.json'
    
    logger.info("Loading data...")
    try:
        entropy_df = load_entropy_results(entropy_path)
        convergence_df = load_convergence_results(convergence_path)
        baseline_df = load_baseline_pass1(baseline_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)
    
    logger.info("Aligning data...")
    try:
        merged_df = align_data_for_router(entropy_df, convergence_df, baseline_df)
    except Exception as e:
        logger.error(f"Failed to align data: {e}")
        sys.exit(1)
    
    if merged_df.empty:
        logger.error("Merged data is empty. Check input files.")
        sys.exit(1)
    
    # Prepare features and target
    # Features: entropy, pass1
    # Target: optimal_k (1, 2, 3)
    feature_cols = ['entropy', 'pass1']
    target_col = 'optimal_k'
    
    # Handle missing values
    merged_df[feature_cols] = merged_df[feature_cols].fillna(0)
    
    X = merged_df[feature_cols].values
    y = merged_df[target_col].values.astype(int)
    
    logger.info(f"Training router with {len(X)} samples. Classes: {np.unique(y)}")
    
    # Train with 5-fold CV
    try:
        model, metrics = train_ordinal_logistic_router(X, y, cv_folds=5, random_state=42)
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)
    
    # Save model
    with open(output_model_path, 'wb') as f:
        pickle.dump(model, f)
    logger.info(f"Saved model to {output_model_path}")
    
    # Save metrics
    with open(output_metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {output_metrics_path}")
    
    # Save CV fold details explicitly as required by T019c
    cv_folds_data = {
        'cv_config': {
            'n_splits': 5,
            'shuffle': True,
            'random_state': 42
        },
        'fold_metrics': metrics['fold_details']
    }
    save_cv_fold_metrics(cv_folds_data, output_cv_folds_path)
    
    logger.info("T019c completed successfully.")

if __name__ == '__main__':
    main()