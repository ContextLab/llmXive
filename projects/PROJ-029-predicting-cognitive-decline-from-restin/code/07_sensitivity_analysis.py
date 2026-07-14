"""
Sensitivity Analysis (Part 2): Label Definition Robustness (T030b)

Varies the decline-definition threshold by ±1 point on raw MMSE/MOCA scores.
MUST re-train the model for each variation to assess robustness of the label definition (FR-012).
Reports false-positive/false-negative rates.
"""
import os
import sys
import json
import argparse
import warnings
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Project imports based on API surface
from utils.logger import get_logger, log_feature_filtering
from utils.io import load_csv, save_json, ensure_dir
from utils.stats import check_collinearity, calculate_feature_variance, filter_low_variance_features
from config import get_config, ensure_dir as config_ensure_dir

# Suppress specific warnings for cleaner logs
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

logger = get_logger("sensitivity_analysis")

def get_logger_wrapper():
    return logger

def load_model_and_data(graph_metrics_path: str, decline_threshold: int = 3) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Loads graph metrics and prepares data for training with a specific decline threshold.
    Returns features (X), labels (y), and subject IDs.
    """
    logger.info(f"Loading graph metrics from {graph_metrics_path}")
    df = load_csv(graph_metrics_path)
    
    if df.empty:
        raise ValueError(f"Graph metrics file is empty: {graph_metrics_path}")
    
    # Ensure numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if 'subject_id' in df.columns:
        numeric_cols = [c for c in numeric_cols if c != 'subject_id']
    
    # Identify score columns (assuming 'mmse_baseline', 'mmse_followup' or similar)
    score_cols = [c for c in df.columns if 'mmse' in c.lower() or 'moca' in c.lower()]
    if len(score_cols) < 2:
        raise ValueError(f"Could not find sufficient score columns for decline calculation. Found: {score_cols}")
    
    # Sort to find baseline and followup (usually baseline is first or has 'baseline' in name)
    baseline_col = [c for c in score_cols if 'baseline' in c.lower()]
    followup_col = [c for c in score_cols if 'followup' in c.lower() or 'end' in c.lower()]
    
    if baseline_col and followup_col:
        b_col, f_col = baseline_col[0], followup_col[0]
    elif len(score_cols) >= 2:
        b_col, f_col = score_cols[0], score_cols[1] # Fallback to order
    else:
        raise ValueError("Cannot determine baseline and followup columns.")
    
    # Calculate decline
    df['decline_score'] = df[b_col] - df[f_col]
    
    # Define label based on threshold
    df['label'] = (df['decline_score'] >= decline_threshold).astype(int)
    
    # Filter out subjects with NaN scores
    valid_mask = df[b_col].notna() & df[f_col].notna() & df['decline_score'].notna()
    df = df[valid_mask].reset_index(drop=True)
    
    if df['label'].sum() == 0 or (len(df) - df['label'].sum()) == 0:
        raise ValueError(f"Imbalanced labels with threshold {decline_threshold}: {df['label'].value_counts().to_dict()}")
    
    # Prepare features
    feature_cols = [c for c in numeric_cols if c not in ['subject_id', 'decline_score', 'label']]
    if not feature_cols:
        raise ValueError("No feature columns found.")
    
    X = df[feature_cols].values
    y = df['label'].values
    subject_ids = df['subject_id'].values if 'subject_id' in df.columns else None
    
    logger.info(f"Data loaded: {len(X)} subjects, {sum(y)} positive, {len(X)-sum(y)} negative")
    return df, X, y, subject_ids, feature_cols, b_col, f_col

def calculate_fpr_fnr(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculates False Positive Rate and False Negative Rate.
    FPR = FP / (FP + TN)
    FNR = FN / (FN + TP)
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    return {'fpr': fpr, 'fnr': fnr, 'tp': tp, 'tn': tn, 'fp': fp, 'fn': fn}

def run_single_training(X: np.ndarray, y: np.ndarray, feature_cols: List[str], random_seed: int = 42) -> Dict[str, Any]:
    """
    Runs a simplified training pipeline (single split or simple CV) to generate predictions.
    Since full nested CV is too heavy for a sensitivity sweep of 3 models,
    we use a robust 5-fold stratified CV to estimate performance metrics.
    """
    logger.info("Running 5-fold Stratified CV for model estimation...")
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_seed)
    all_fpr = []
    all_fnr = []
    fold_metrics = []
    
    for fold_idx, (train_idx, test_idx) in enumerate(cv.split(X, y)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # Simple pipeline: Scaling + Random Forest
        # Using parameters from T023 (n_estimators=100, max_depth=None) as base
        model = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=random_seed, n_jobs=2)
        scaler = StandardScaler()
        
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        
        metrics = calculate_fpr_fnr(y_test, y_pred)
        metrics['fold'] = fold_idx
        fold_metrics.append(metrics)
        
        all_fpr.append(metrics['fpr'])
        all_fnr.append(metrics['fnr'])
    
    return {
        'mean_fpr': float(np.mean(all_fpr)),
        'std_fpr': float(np.std(all_fpr)),
        'mean_fnr': float(np.mean(all_fnr)),
        'std_fnr': float(np.std(all_fnr)),
        'fold_metrics': fold_metrics
    }

def run_sensitivity_analysis(
    graph_metrics_path: str,
    output_path: str,
    thresholds: List[int] = None
):
    """
    Main logic for T030b: Vary decline threshold, re-train, report FPR/FNR.
    """
    if thresholds is None:
        thresholds = [2, 3, 4] # ±1 point from default 3
    
    logger.info(f"Starting Sensitivity Analysis (Part 2) with thresholds: {thresholds}")
    ensure_dir(output_path)
    
    results = []
    
    for thresh in thresholds:
        logger.info(f"--- Processing Threshold: {thresh} ---")
        try:
            # 1. Load data with specific threshold
            df, X, y, subject_ids, feature_cols, b_col, f_col = load_model_and_data(
                graph_metrics_path, decline_threshold=thresh
            )
            
            # 2. Re-train model (simulated via CV)
            training_results = run_single_training(X, y, feature_cols)
            
            # 3. Compile results
            result_entry = {
                'threshold': thresh,
                'baseline_score_col': b_col,
                'followup_score_col': f_col,
                'n_subjects': int(len(X)),
                'n_positive': int(sum(y)),
                'n_negative': int(len(X) - sum(y)),
                'mean_fpr': training_results['mean_fpr'],
                'std_fpr': training_results['std_fpr'],
                'mean_fnr': training_results['mean_fnr'],
                'std_fnr': training_results['std_fnr'],
                'fold_metrics': training_results['fold_metrics']
            }
            results.append(result_entry)
            logger.info(f"Threshold {thresh}: FPR={result_entry['mean_fpr']:.3f}, FNR={result_entry['mean_fnr']:.3f}")
            
        except Exception as e:
            logger.error(f"Failed processing threshold {thresh}: {str(e)}")
            results.append({
                'threshold': thresh,
                'error': str(e),
                'mean_fpr': None,
                'mean_fnr': None
            })
    
    # Write output
    output_data = {
        'analysis_type': 'label_definition_robustness',
        'description': 'Variance in FPR/FNR when varying the cognitive decline threshold by ±1 point',
        'results': results
    }
    
    save_json(output_data, output_path)
    logger.info(f"Sensitivity analysis complete. Results written to {output_path}")
    return output_data

def write_outputs(results: Dict[str, Any], output_path: str):
    """Helper to ensure outputs are written (already done in run_sensitivity_analysis)."""
    pass

def main():
    parser = argparse.ArgumentParser(description="Sensitivity Analysis (Part 2): Label Definition Robustness")
    parser.add_argument(
        '--input', 
        type=str, 
        default='data/processed/graph_metrics.csv',
        help='Path to graph metrics CSV'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='data/processed/sensitivity_report.json',
        help='Path to output JSON report'
    )
    parser.add_argument(
        '--thresholds',
        type=int,
        nargs='+',
        default=[2, 3, 4],
        help='Decline thresholds to test (default: 2 3 4)'
    )
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        logger.error("Please run code/03_compute_graph_metrics.py and code/04_train_model.py first.")
        sys.exit(1)
    
    run_sensitivity_analysis(
        graph_metrics_path=args.input,
        output_path=args.output,
        thresholds=args.thresholds
    )

if __name__ == '__main__':
    main()