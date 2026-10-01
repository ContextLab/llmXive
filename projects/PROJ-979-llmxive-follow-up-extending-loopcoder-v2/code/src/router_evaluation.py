import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import pickle
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# Import from project config
try:
    from src.config import load_config, get_config_value
except ImportError:
    def load_config():
        return {"RANDOM_SEED": 42}
    def get_config_value(key, default=None):
        config = load_config()
        return config.get(key, default)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_convergence_results(filepath: str) -> List[Dict[str, Any]]:
    """Load convergence results from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Convergence results not found at {filepath}")
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'task_id': row['task_id'],
                'k': int(row['k']),
                'is_correct': row['is_correct'].lower() == 'true',
                'first_correct_step': int(row['first_correct_step']) if row['first_correct_step'] != '' else None,
                'censored': row['censored'].lower() == 'true',
                'time_to_event': int(row['time_to_event'])
            })
    return data

def load_entropy_results(filepath: str) -> List[Dict[str, Any]]:
    """Load entropy results from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Entropy results not found at {filepath}")
    data = []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'task_id': row['task_id'],
                'entropy': float(row['entropy'])
            })
    return data

def load_baseline_pass1(filepath: str) -> Dict[str, Any]:
    """Load baseline pass@1 values."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline pass@1 not found at {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def align_data_for_router(entropy_data: List[Dict], convergence_data: List[Dict], baseline_data: Dict) -> pd.DataFrame:
    """Merge data for router training/prediction."""
    df_entropy = pd.DataFrame(entropy_data)
    df_conv = pd.DataFrame(convergence_data)
    # Keep only the row with the smallest k that is correct, or the censored row
    # We need the 'optimal_k' which is first_correct_step (or 3 if censored)
    df_conv = df_conv[df_conv['k'] == df_conv['first_correct_step']]
    # If no correct step found, we need the censored row
    missing = df_conv[df_conv['first_correct_step'].isna()]
    if len(missing) > 0:
        # Take the k=3 row for these
        missing_k3 = missing[missing['k'] == 3]
        df_conv = pd.concat([df_conv, missing_k3])
    
    # Merge
    df = pd.merge(df_entropy, df_conv, on='task_id', how='inner')
    # Add baseline pass1 (assume it's a constant or mapped by task_id if provided)
    if 'pass1' in baseline_data:
        df['baseline_pass1'] = baseline_data['pass1']
    else:
        # If not available, use a placeholder or mean
        df['baseline_pass1'] = 0.5 # Default placeholder if not in data
    
    # Derive target: optimal_k = first_correct_step if exists, else 3 (censored)
    df['optimal_k'] = df['first_correct_step'].fillna(3).astype(int)
    # Ensure optimal_k is within range [1, 3] for ordinal regression
    df['optimal_k'] = df['optimal_k'].clip(1, 3)
    
    return df

def train_ordinal_logistic_router(df: pd.DataFrame, n_folds: int = 5) -> tuple:
    """Train ordinal logistic regression with 5-fold CV."""
    features = df[['entropy', 'baseline_pass1']].values
    target = df['optimal_k'].values
    
    # Ensure target is ordinal (1, 2, 3)
    target = np.clip(target, 1, 3)
    
    kfold = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    fold_metrics = []
    
    model = None
    for fold_idx, (train_idx, test_idx) in enumerate(kfold.split(features, target)):
        X_train, y_train = features[train_idx], target[train_idx]
        X_test, y_test = features[test_idx], target[test_idx]
        
        try:
            # Fit model using statsmodels OrderedLogit
            X_train_sm = sm.add_constant(X_train)
            model_fold = sm.OrderedLogit(y_train, X_train_sm).fit(disp=0)
            
            # Predict on test
            y_pred = model_fold.predict(X_test).argmax(axis=1) + 1
            
            acc = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred, average='weighted')
            cm = confusion_matrix(y_test, y_pred)
            
            fold_metrics.append({
                'fold': fold_idx + 1,
                'accuracy': acc,
                'f1': f1,
                'confusion_matrix': cm.tolist()
            })
            
            if model is None:
                model = model_fold
        except Exception as e:
            logger.error(f"Fold {fold_idx} failed: {e}")
            continue
    
    # Retrain on full data for final model
    if model is None:
        X_full = sm.add_constant(features)
        model = sm.OrderedLogit(target, X_full).fit(disp=0)
    
    return model, fold_metrics

def save_cv_fold_metrics(fold_metrics: List[Dict], filepath: str):
    """Save CV fold metrics to JSON."""
    with open(filepath, 'w') as f:
        json.dump(fold_metrics, f, indent=2)

def evaluate_router(model, df: pd.DataFrame) -> Dict[str, Any]:
    """Evaluate router on the dataset."""
    X = sm.add_constant(df[['entropy', 'baseline_pass1']].values)
    y_true = df['optimal_k'].values
    
    y_pred = model.predict(X).argmax(axis=1) + 1
    
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average='weighted')
    cm = confusion_matrix(y_true, y_pred)
    
    return {
        'accuracy': acc,
        'f1': f1,
        'confusion_matrix': cm.tolist(),
        'n_samples': len(df)
    }

def main():
    """Main function to generate router predictions."""
    # Paths
    entropy_path = "data/processed/entropy_results.csv"
    convergence_path = "data/processed/convergence_results_core.csv"
    baseline_path = "data/processed/baseline_pass1.json"
    model_output_path = "data/processed/router_model.pkl"
    metrics_output_path = "data/processed/router_metrics.json"
    cv_metrics_path = "data/processed/router_cv_folds.json"
    predictions_output_path = "data/processed/router_results.csv"

    # Load data
    logger.info("Loading entropy results...")
    entropy_data = load_entropy_results(entropy_path)
    logger.info("Loading convergence results...")
    convergence_data = load_convergence_results(convergence_path)
    logger.info("Loading baseline pass@1...")
    baseline_data = load_baseline_pass1(baseline_path)

    # Align data
    logger.info("Aligning data for router...")
    df = align_data_for_router(entropy_data, convergence_data, baseline_data)
    
    if df.empty:
        logger.error("No data to process after alignment.")
        return

    # Train model
    logger.info("Training ordinal logistic router with 5-fold CV...")
    model, fold_metrics = train_ordinal_logistic_router(df)
    
    # Save CV metrics
    logger.info(f"Saving CV metrics to {cv_metrics_path}...")
    save_cv_fold_metrics(fold_metrics, cv_metrics_path)

    # Evaluate on full data
    logger.info("Evaluating router...")
    metrics = evaluate_router(model, df)
    
    # Save model and metrics
    logger.info(f"Saving model to {model_output_path}...")
    with open(model_output_path, 'wb') as f:
        pickle.dump(model, f)
    
    logger.info(f"Saving metrics to {metrics_output_path}...")
    with open(metrics_output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    # Generate predictions for the task output
    X = sm.add_constant(df[['entropy', 'baseline_pass1']].values)
    y_true = df['optimal_k'].values
    y_pred = model.predict(X).argmax(axis=1) + 1

    # Reconstruct is_censored from original convergence data
    conv_df = pd.DataFrame(convergence_data)
    conv_k3 = conv_df[conv_df['k'] == 3][['task_id', 'censored']]
    df_result = pd.DataFrame({
        'task_id': df['task_id'],
        'predicted_k': y_pred,
        'actual_k': y_true,
        'is_censored': df['task_id'].map(conv_k3.set_index('task_id')['censored']).fillna(False)
    })
    
    df_result['accuracy'] = (df_result['predicted_k'] == df_result['actual_k']).astype(int)

    # Save to CSV
    logger.info(f"Saving router predictions to {predictions_output_path}...")
    df_result.to_csv(predictions_output_path, index=False)

    logger.info("Router prediction generation completed successfully.")

if __name__ == "__main__":
    main()
