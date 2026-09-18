import os
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from code.logging_config import setup_logging
from code.config import DATA_PATH
from code.sensitivity_analysis import run_sensitivity_analysis
from code.model_training import train_models, run_cross_validation

logger = logging.getLogger(__name__)

def load_sensitivity_analysis(path: str) -> Optional[Dict[str, Any]]:
    """Load sensitivity analysis results if they exist."""
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None

def prepare_data_and_split(data_path: str):
    """Load processed data and perform scaffold split."""
    # Import locally to avoid circular imports if necessary
    from code.scaffold_split import scaffold_split
    from code.data_loader import load_processed_data
    
    df = load_processed_data(data_path)
    if df is None or df.empty:
        raise ValueError(f"Failed to load data from {data_path}")
    
    # Assuming the target column is 'conductivity' or similar, handled in training
    # We need to separate features (X) and target (y)
    # The target variable name is defined in config
    from code.config import TARGET_VAR
    
    if TARGET_VAR not in df.columns:
        # Fallback to common names if config target is missing
        possible_targets = ['conductivity', 'log_conductivity', 'HOMO_LUMO_gap', 'charge_carrier_mobility']
        target_col = None
        for t in possible_targets:
            if t in df.columns:
                target_col = t
                break
        if not target_col:
            raise ValueError(f"Target variable '{TARGET_VAR}' not found in data. Available columns: {df.columns.tolist()}")
    else:
        target_col = TARGET_VAR

    # Drop rows with NaN in target or features
    # Identify feature columns (exclude target and non-feature columns like 'smiles' if present)
    non_feature_cols = [target_col]
    if 'smiles' in df.columns:
        non_feature_cols.append('smiles')
    if 'valid' in df.columns:
        non_feature_cols.append('valid')
    
    feature_cols = [c for c in df.columns if c not in non_feature_cols]
    
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Perform scaffold split
    # We need the SMILES column for splitting
    if 'smiles' in df.columns:
        smiles = df['smiles'].values
        train_idx, test_idx = scaffold_split(smiles, test_size=0.2, random_state=42)
    else:
        # Fallback to random split if no SMILES
        logger.warning("No SMILES column found. Using random split.")
        rng = np.random.RandomState(42)
        indices = np.arange(len(df))
        rng.shuffle(indices)
        split_point = int(len(df) * 0.8)
        train_idx = indices[:split_point]
        test_idx = indices[split_point:]
        
    return X, y, train_idx, test_idx, feature_cols

def train_models_and_get_r2(X, y, train_idx, test_idx, feature_cols):
    """Train RF and GB models and return R2 scores."""
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    
    # Train models
    rf_model, gb_model = train_models(X_train, y_train)
    
    # Evaluate
    rf_r2 = rf_model.score(X_test, y_test)
    gb_r2 = gb_model.score(X_test, y_test)
    
    # Cross validation
    rf_cv = run_cross_validation(rf_model, X_train, y_train)
    gb_cv = run_cross_validation(gb_model, X_train, y_train)
    
    return {
        'rf_r2': float(rf_r2),
        'gb_r2': float(gb_r2),
        'rf_cv_mean': float(np.mean(rf_cv)),
        'rf_cv_std': float(np.std(rf_cv)),
        'gb_cv_mean': float(np.mean(gb_cv)),
        'gb_cv_std': float(np.std(gb_cv)),
        'feature_cols': feature_cols
    }

def save_results_to_json(results: Dict[str, Any], output_path: str):
    """Save model results to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved model results to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Train models and save results.")
    parser.add_argument('--data', type=str, default='data/processed/descriptors.csv',
                        help='Path to processed data CSV')
    parser.add_argument('--output', type=str, default='data/processed/model_results.json',
                        help='Path to save model results JSON')
    parser.add_argument('--sensitivity', type=str, default='data/processed/sensitivity_analysis.json',
                        help='Path to sensitivity analysis JSON (optional)')
    
    args = parser.parse_args()
    
    setup_logging()
    
    # Initialize results structure
    results = {
        'rf_r2': None,
        'gb_r2': None,
        'cv_scores': {
            'rf': {'mean': None, 'std': None},
            'gb': {'mean': None, 'std': None}
        },
        'sensitivity_analysis': None,
        'vif_scores': None
    }
    
    try:
        # 1. Try to load sensitivity analysis if it exists
        sens_data = load_sensitivity_analysis(args.sensitivity)
        if sens_data:
            results['sensitivity_analysis'] = sens_data
            logger.info("Loaded existing sensitivity analysis.")
        else:
            logger.warning("No sensitivity analysis found. Skipping sensitivity data in results.")
        
        # 2. Prepare data and split
        logger.info(f"Loading and splitting data from {args.data}")
        X, y, train_idx, test_idx, feature_cols = prepare_data_and_split(args.data)
        
        # 3. Train and evaluate
        logger.info("Training models...")
        model_metrics = train_models_and_get_r2(X, y, train_idx, test_idx, feature_cols)
        
        # 4. Update results
        results['rf_r2'] = model_metrics['rf_r2']
        results['gb_r2'] = model_metrics['gb_r2']
        results['cv_scores']['rf'] = {
            'mean': model_metrics['rf_cv_mean'],
            'std': model_metrics['rf_cv_std']
        }
        results['cv_scores']['gb'] = {
            'mean': model_metrics['gb_cv_mean'],
            'std': model_metrics['gb_cv_std']
        }
        
        # 5. Save results
        save_results_to_json(results, args.output)
        
    except Exception as e:
        logger.error(f"Error during model training and results saving: {e}")
        # Even if training fails, save the initialized structure if possible, 
        # but for this task, we ensure the file is created with valid JSON.
        # If we are here, we try to save what we have (even if nulls)
        try:
            save_results_to_json(results, args.output)
        except:
            pass
        raise

if __name__ == '__main__':
    main()
