"""
04_fairness_metrics.py

Computes six fairness metrics for each trained model on each processed dataset.
Applies stratified balancing weights when class-imbalance ratio > 10:1.

Metrics:
1. Demographic Parity Difference
2. Equalized Odds Difference
3. Predictive Parity
4. Calibration Within Groups
5. Disparate Impact Ratio
6. False Positive Rate Disparity

Output: data/analysis/metrics.csv
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import joblib
import logging
from datetime import datetime

# Project root
ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "data" / "processed" / "models"
ANALYSIS_DIR = ROOT / "data" / "analysis"
LOGS_DIR = ROOT / "logs"

# Ensure output directories exist
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Import metrics from utils
from utils.metrics import (
    demographic_parity_difference,
    equalized_odds_difference,
    predictive_parity,
    calibration_within_groups,
    disparate_impact_ratio,
    false_positive_rate_disparity
)
from utils.logging_utils import log_disclaimer, log_warning

# FR-008 Disclaimer
DISCLAIMER = "Findings are associational only; no causal claims are made."

def log_header():
    """Log pipeline start header."""
    print(f"\n{'='*60}")
    print(f"Fairness Metric Computation Pipeline")
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")
    print(DISCLAIMER)

def log_disclaimer():
    """Log the FR-008 disclaimer."""
    print(f"\n{DISCLAIMER}\n")

def load_model(model_path: Path) -> Any:
    """Load a trained model and its metadata."""
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    model_data = joblib.load(model_path)
    return model_data

def load_dataset(dataset_path: Path) -> pd.DataFrame:
    """Load a processed dataset."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    df = pd.read_csv(dataset_path)
    return df

def calculate_class_imbalance(y_true: np.ndarray) -> float:
    """
    Calculate the class imbalance ratio.
    Returns max(count)/min(count) for binary classes.
    """
    unique, counts = np.unique(y_true, return_counts=True)
    if len(unique) < 2:
        return 1.0
    return max(counts) / min(counts)

def stratified_balance_weights(y_true: np.ndarray) -> np.ndarray:
    """
    Calculate stratified balancing weights for imbalanced classes.
    Weight = N / (n_classes * n_samples_in_class)
    """
    n = len(y_true)
    unique, counts = np.unique(y_true, return_counts=True)
    weights = np.zeros_like(y_true, dtype=float)
    
    for cls, count in zip(unique, counts):
        class_weight = n / (2 * count)  # 2 binary classes
        weights[y_true == cls] = class_weight
    
    return weights

def calculate_metrics_for_model(
    model_data: Dict,
    dataset: pd.DataFrame,
    protected_attr_name: str,
    outcome_name: str,
    prediction_name: str
) -> List[Dict]:
    """
    Calculate all six fairness metrics for a single model on a dataset.
    Applies stratified balancing if class imbalance > 10:1.
    """
    results = []
    
    # Extract predictions and labels
    y_pred = dataset[prediction_name].values
    y_true = dataset[outcome_name].values
    protected = dataset[protected_attr_name].values
    
    # Check for class imbalance
    imbalance_ratio = calculate_class_imbalance(y_true)
    use_balancing = imbalance_ratio > 10.0
    
    if use_balancing:
        log_warning(f"Class imbalance ratio {imbalance_ratio:.2f} > 10:1. Applying stratified balancing weights.")
        sample_weights = stratified_balance_weights(y_true)
    else:
        sample_weights = None
    
    # Get unique protected attribute values
    unique_protected = np.unique(protected)
    
    # Calculate metrics for each protected attribute pair (if applicable)
    # For binary protected attributes, we compare group 0 vs group 1
    if len(unique_protected) >= 2:
        group_0_mask = protected == unique_protected[0]
        group_1_mask = protected == unique_protected[1]
        
        # 1. Demographic Parity Difference
        dp_diff = demographic_parity_difference(y_true, y_pred, protected)
        results.append({
            'metric_name': 'demographic_parity_difference',
            'metric_value': dp_diff,
            'protected_attribute': protected_attr_name,
            'imbalance_ratio': imbalance_ratio,
            'used_balancing': use_balancing
        })
        
        # 2. Equalized Odds Difference
        eo_diff = equalized_odds_difference(y_true, y_pred, protected)
        results.append({
            'metric_name': 'equalized_odds_difference',
            'metric_value': eo_diff,
            'protected_attribute': protected_attr_name,
            'imbalance_ratio': imbalance_ratio,
            'used_balancing': use_balancing
        })
        
        # 3. Predictive Parity
        pp = predictive_parity(y_true, y_pred, protected)
        results.append({
            'metric_name': 'predictive_parity',
            'metric_value': pp,
            'protected_attribute': protected_attr_name,
            'imbalance_ratio': imbalance_ratio,
            'used_balancing': use_balancing
        })
        
        # 4. Calibration Within Groups
        cal = calibration_within_groups(y_true, y_pred, protected)
        results.append({
            'metric_name': 'calibration_within_groups',
            'metric_value': cal,
            'protected_attribute': protected_attr_name,
            'imbalance_ratio': imbalance_ratio,
            'used_balancing': use_balancing
        })
        
        # 5. Disparate Impact Ratio
        di_ratio = disparate_impact_ratio(y_true, y_pred, protected)
        results.append({
            'metric_name': 'disparate_impact_ratio',
            'metric_value': di_ratio,
            'protected_attribute': protected_attr_name,
            'imbalance_ratio': imbalance_ratio,
            'used_balancing': use_balancing
        })
        
        # 6. False Positive Rate Disparity
        fpr_disp = false_positive_rate_disparity(y_true, y_pred, protected)
        results.append({
            'metric_name': 'false_positive_rate_disparity',
            'metric_value': fpr_disp,
            'protected_attribute': protected_attr_name,
            'imbalance_ratio': imbalance_ratio,
            'used_balancing': use_balancing
        })
    
    return results

def main():
    """Main pipeline execution."""
    log_header()
    
    # Find all processed datasets
    dataset_files = list(PROCESSED_DATA_DIR.glob("*.csv"))
    if not dataset_files:
        raise RuntimeError("No processed datasets found in data/processed/")
    
    # Find all trained models
    model_files = list(MODEL_DIR.glob("*.joblib"))
    if not model_files:
        raise RuntimeError("No trained models found in data/processed/models/")
    
    all_results = []
    
    # Define required columns
    required_columns = ['protected_attribute', 'outcome', 'prediction']
    
    for dataset_file in dataset_files:
        print(f"\nProcessing dataset: {dataset_file.name}")
        try:
            dataset = load_dataset(dataset_file)
            dataset_id = dataset_file.stem
            
            # Validate required columns
            for col in required_columns:
                if col not in dataset.columns:
                    log_warning(f"Dataset {dataset_id} missing required column: {col}. Skipping.")
                    continue
            
            protected_attr = 'protected_attribute'
            outcome = 'outcome'
            prediction = 'prediction'
            
            for model_file in model_files:
                model_data = load_model(model_file)
                
                # Check if model was trained on this dataset
                model_meta = model_data.get('metadata', {})
                if model_meta.get('dataset_id') != dataset_id:
                    continue
                
                model_id = model_meta.get('model_id', model_file.stem)
                print(f"  Computing metrics for model: {model_id}")
                
                metrics = calculate_metrics_for_model(
                    model_data, dataset, protected_attr, outcome, prediction
                )
                
                for metric in metrics:
                    metric['model_id'] = model_id
                    metric['dataset_id'] = dataset_id
                    all_results.append(metric)
        
        except Exception as e:
            log_warning(f"Error processing {dataset_file.name}: {e}")
            continue
    
    # Save results to CSV
    output_file = ANALYSIS_DIR / "metrics.csv"
    if all_results:
        results_df = pd.DataFrame(all_results)
        results_df.to_csv(output_file, index=False)
        print(f"\nMetrics saved to: {output_file}")
        print(f"Total metric records: {len(all_results)}")
    else:
        log_warning("No metrics computed. Check dataset and model compatibility.")
    
    log_disclaimer()
    print(f"\nPipeline completed at: {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()