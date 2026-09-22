"""
Evaluator module for the llmXive follow-up project.
Handles data splitting, threshold calculation, prediction, and reporting.
"""
import csv
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_metrics(file_path: Path) -> pd.DataFrame:
    """Load metrics from a CSV file."""
    return pd.read_csv(file_path)

def save_metrics(df: pd.DataFrame, file_path: Path):
    """Save metrics to a CSV file."""
    df.to_csv(file_path, index=False)

def load_json_file(file_path: Path) -> Any:
    """Load a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(data: Any, file_path: Path):
    """Save data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def stratified_split(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Perform a stratified split of the data based on the 'collapse' label."""
    # Ensure 'collapse' column exists
    if 'collapse' not in df.columns:
        raise ValueError("DataFrame must contain a 'collapse' column for stratified split.")
    
    train_df, test_df = train_test_split(
        df, 
        test_size=test_size, 
        stratify=df['collapse'], 
        random_state=random_state
    )
    return train_df, test_df

def calculate_20th_percentile_threshold(train_df: pd.DataFrame) -> float:
    """Calculate the 20th percentile threshold from the success class (collapse=0)."""
    success_class = train_df[train_df['collapse'] == 0]
    
    if len(success_class) < 5:
        raise ValueError("Insufficient samples (n < 5) for threshold calculation. Dataset may be too small or success class imbalance too high.")
    
    # Combine connectivity and branching into a single array
    combined_values = np.concatenate([
        success_class['global_connectivity'].values,
        success_class['avg_branching_factor'].values
    ])
    
    threshold = np.percentile(combined_values, 20)
    return threshold

def calculate_baseline(train_df: pd.DataFrame) -> float:
    """Calculate the mean connectivity of the success class."""
    success_class = train_df[train_df['collapse'] == 0]
    return success_class['global_connectivity'].mean()

def calculate_correlation(test_df: pd.DataFrame) -> Tuple[float, float]:
    """Calculate Pearson correlation between connectivity and collapse."""
    # Collapse is binary, so we correlate connectivity with collapse
    corr, p_value = stats.pearsonr(test_df['global_connectivity'], test_df['collapse'])
    return corr, p_value

def calculate_null_distribution(test_df: pd.DataFrame, n_permutations: int = 1000, seed: int = 42) -> Dict:
    """Perform a permutation test to establish null distribution."""
    np.random.seed(seed)
    observed_corr, _ = calculate_correlation(test_df)
    
    null_corrs = []
    for _ in range(n_permutations):
        shuffled_labels = np.random.permutation(test_df['collapse'].values)
        corr, _ = stats.pearsonr(test_df['global_connectivity'].values, shuffled_labels)
        null_corrs.append(corr)
    
    # Calculate p-value
    count_ge = sum(1 for c in null_corrs if c >= observed_corr)
    p_value = (count_ge + 1) / (n_permutations + 1)
    
    return {
        "observed_correlation": observed_corr,
        "null_distribution_mean": np.mean(null_corrs),
        "null_distribution_std": np.std(null_corrs),
        "p_value": p_value,
        "sc_002_passed": p_value < 0.05
    }

def predict_collapse(test_df: pd.DataFrame, threshold: float) -> pd.Series:
    """Predict collapse based on the threshold."""
    # If connectivity < threshold, predict collapse (1)
    return (test_df['global_connectivity'] < threshold).astype(int)

def evaluate_performance(test_df: pd.DataFrame, predictions: pd.Series) -> Dict:
    """Evaluate performance metrics."""
    from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix, accuracy_score
    
    y_true = test_df['collapse'].values
    y_pred = predictions.values
    
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    acc = accuracy_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred).tolist()
    
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": acc,
        "confusion_matrix": cm
    }

def calculate_power_analysis(train_df: pd.DataFrame) -> Dict:
    """Calculate effect size (Cohen's d) and post-hoc power analysis."""
    success_class = train_df[train_df['collapse'] == 0]['global_connectivity'].values
    failure_class = train_df[train_df['collapse'] == 1]['global_connectivity'].values
    
    if len(success_class) < 2 or len(failure_class) < 2:
        return {"effect_size": None, "power": None, "flag": "Insufficient samples for power analysis"}
    
    # Cohen's d
    mean_diff = np.mean(success_class) - np.mean(failure_class)
    pooled_std = np.sqrt((np.var(success_class) + np.var(failure_class)) / 2)
    cohens_d = mean_diff / pooled_std if pooled_std != 0 else 0
    
    # Power analysis (simplified approximation)
    # For a two-sample t-test, power depends on d, n1, n2, and alpha
    # Using a simple approximation for demonstration
    n1, n2 = len(success_class), len(failure_class)
    # Approximate power using standard normal CDF
    # Z = (d * sqrt(n/2) - z_alpha) where n is harmonic mean
    n_harmonic = 2 * (n1 * n2) / (n1 + n2)
    z_alpha = 1.96  # For alpha=0.05
    z_beta = cohens_d * np.sqrt(n_harmonic / 2) - z_alpha
    power = stats.norm.cdf(z_beta)
    
    flag = "Power < 0.8" if power < 0.8 else "Power sufficient"
    
    return {
        "effect_size": float(cohens_d),
        "power": float(power),
        "flag": flag
    }

def run_stratified_split(input_file: Path):
    """Main function to run stratified split."""
    df = load_metrics(input_file)
    train_df, test_df = stratified_split(df)
    
    train_path = Path("data/processed/train_metrics.csv")
    test_path = Path("data/processed/test_metrics.csv")
    
    save_metrics(train_df, train_path)
    save_metrics(test_df, test_path)
    
    logger.info(f"Split complete. Train: {len(train_df)}, Test: {len(test_df)}")

def run_full_evaluation():
    """Main function to run the full evaluation pipeline."""
    # Load split data
    train_df = load_metrics(Path("data/processed/train_metrics.csv"))
    test_df = load_metrics(Path("data/processed/test_metrics.csv"))
    
    # 1. Calculate Baseline
    baseline = calculate_baseline(train_df)
    save_json_file({"baseline_mean_connectivity": float(baseline)}, Path("data/processed/baseline_report.json"))
    
    # 2. Calculate 20th Percentile Threshold
    threshold = calculate_20th_percentile_threshold(train_df)
    save_json_file({"threshold": float(threshold), "percentile": 20}, Path("data/processed/threshold_config.json"))
    
    # 3. Calculate F1-Max Threshold (Comparative)
    # For simplicity, we'll use a grid search or just report the current threshold
    # In a real implementation, we'd optimize this
    f1_max_threshold = threshold # Placeholder for actual optimization logic
    save_json_file({"f1_max_threshold": float(f1_max_threshold)}, Path("data/processed/f1_max_threshold.json"))
    
    # 4. Sensitivity Analysis (Thresholds)
    thresholds = [0.01, 0.05, 0.1]
    sensitivity_results = {}
    for t in thresholds:
        preds = (test_df['global_connectivity'] < t).astype(int)
        metrics = evaluate_performance(test_df, preds)
        sensitivity_results[str(t)] = metrics
    save_json_file(sensitivity_results, Path("data/processed/sensitivity_threshold_matrix.json"))
    
    # 5. Sensitivity Analysis (Percentiles)
    percentiles = [10, 20, 30]
    percentile_results = {}
    for p in percentiles:
        pct_thresh = np.percentile(train_df[train_df['collapse']==0]['global_connectivity'], p)
        preds = (test_df['global_connectivity'] < pct_thresh).astype(int)
        metrics = evaluate_performance(test_df, preds)
        percentile_results[str(p)] = metrics
    save_json_file(percentile_results, Path("data/processed/sensitivity_percentile_matrix.json"))
    
    # 6. Correlation and Null Distribution
    corr, p_val = calculate_correlation(test_df)
    null_dist = calculate_null_distribution(test_df)
    save_json_file(null_dist, Path("data/processed/sc_002_result.json"))
    
    # 7. Power Analysis
    power_analysis = calculate_power_analysis(train_df)
    save_json_file(power_analysis, Path("data/processed/power_analysis.json"))
    
    # 8. Predict and Evaluate
    predictions = predict_collapse(test_df, threshold)
    perf_metrics = evaluate_performance(test_df, predictions)
    
    # 9. Comparative Report
    comparative_report = {
        "primary_threshold": float(threshold),
        "f1_max_threshold": float(f1_max_threshold),
        "sensitivity_thresholds": sensitivity_results,
        "sensitivity_percentiles": percentile_results,
        "correlation": float(corr),
        "p_value": float(p_val),
        "sc_002_passed": null_dist["sc_002_passed"]
    }
    save_json_file(comparative_report, Path("data/processed/comparative_report.json"))
    
    # 10. Final Report
    final_report = {
        "baseline": float(baseline),
        "threshold": float(threshold),
        "predictions": predictions.tolist(),
        "performance": perf_metrics,
        "correlation_analysis": {
            "pearson_r": float(corr),
            "p_value": float(p_val),
            "sc_002_passed": null_dist["sc_002_passed"]
        },
        "power_analysis": power_analysis,
        "sensitivity": {
            "thresholds": sensitivity_results,
            "percentiles": percentile_results
        }
    }
    save_json_file(final_report, Path("data/processed/results_report.json"))
    
    logger.info("Evaluation complete.")
