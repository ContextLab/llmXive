import csv
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
import numpy as np
from config import ensure_directories

logger = logging.getLogger(__name__)

def load_metrics(filepath: str) -> pd.DataFrame:
    """Load metrics from a CSV file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Metrics file not found: {filepath}")
    return pd.read_csv(filepath)

def save_metrics(df: pd.DataFrame, filepath: str) -> None:
    """Save metrics DataFrame to a CSV file."""
    ensure_directories(filepath)
    df.to_csv(filepath, index=False)
    logger.info(f"Saved metrics to {filepath}")

def load_json_file(filepath: str) -> Any:
    """Load JSON from a file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"JSON file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json_file(data: Any, filepath: str) -> None:
    """Save data to a JSON file."""
    ensure_directories(filepath)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved JSON to {filepath}")

def stratified_split(df: pd.DataFrame, test_size: float = 0.2, seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the DataFrame into train and test sets while preserving label balance.
    Assumes the 'collapse' column exists as the target label.
    """
    if 'collapse' not in df.columns:
        raise ValueError("DataFrame must contain a 'collapse' column for stratified split.")
    
    train_df, test_df = train_test_split(
        df, 
        test_size=test_size, 
        stratify=df['collapse'], 
        random_state=seed
    )
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)

def calculate_baseline(train_df: pd.DataFrame) -> float:
    """
    Calculate the mean connectivity of the 'success' class (collapse=0).
    FR-007 Requirement.
    """
    success_df = train_df[train_df['collapse'] == 0]
    if success_df.empty:
        logger.warning("No success class found in training data.")
        return 0.0
    return float(success_df['connectivity'].mean())

def calculate_20th_percentile_threshold(train_df: pd.DataFrame) -> float:
    """
    Calculate the 20th percentile of the connectivity column for the success class.
    PRIMARY THRESHOLD per FR-004.
    
    Args:
        train_df: DataFrame containing the training split.
        
    Returns:
        The 20th percentile threshold value (float).
    """
    if 'connectivity' not in train_df.columns or 'collapse' not in train_df.columns:
        raise ValueError("DataFrame must contain 'connectivity' and 'collapse' columns.")
    
    success_df = train_df[train_df['collapse'] == 0]
    if success_df.empty:
        raise ValueError("No success class samples found to calculate percentile.")
    
    threshold = float(success_df['connectivity'].quantile(0.20))
    logger.info(f"Calculated 20th percentile threshold (Success Class): {threshold}")
    return threshold

def calculate_f1_max_threshold(train_df: pd.DataFrame) -> float:
    """
    Calculate the optimal F1-score threshold for comparative analysis only.
    This threshold MUST NOT be used for primary prediction.
    
    Args:
        train_df: DataFrame containing the training split.
        
    Returns:
        The threshold value that maximizes F1 on the training set.
    """
    # Simple grid search for F1 max on training set
    connectivity_values = train_df['connectivity'].unique()
    best_f1 = -1
    best_threshold = 0.0
    
    # Sort unique values to iterate thresholds
    thresholds = sorted(connectivity_values)
    
    for thresh in thresholds:
        # Predict collapse=1 if connectivity < thresh (assuming lower connectivity = collapse)
        # Note: The direction of the relationship should be verified by domain logic.
        # Based on typical "collapse" logic in deep research, low connectivity often implies failure.
        preds = (train_df['connectivity'] < thresh).astype(int)
        actuals = train_df['collapse'].values
        
        tp = ((preds == 1) & (actuals == 1)).sum()
        fp = ((preds == 1) & (actuals == 0)).sum()
        fn = ((preds == 0) & (actuals == 1)).sum()
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = thresh
            
    logger.info(f"Calculated F1-max threshold: {best_threshold} (F1={best_f1:.4f})")
    return best_threshold

def predict_collapse(test_df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """
    Predict collapse based on the provided threshold.
    Assumes: connectivity < threshold => collapse (1), else success (0).
    
    Args:
        test_df: DataFrame containing the test split.
        threshold: The threshold value to apply.
        
    Returns:
        DataFrame with an added 'predicted_collapse' column.
    """
    df = test_df.copy()
    df['predicted_collapse'] = (df['connectivity'] < threshold).astype(int)
    return df

def evaluate_performance(test_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Evaluate performance metrics (Precision, Recall, F1, Confusion Matrix).
    
    Args:
        test_df: DataFrame with 'collapse' (actual) and 'predicted_collapse' columns.
        
    Returns:
        Dictionary containing metrics.
    """
    actuals = test_df['collapse'].values
    preds = test_df['predicted_collapse'].values
    
    tp = ((preds == 1) & (actuals == 1)).sum()
    tn = ((preds == 0) & (actuals == 0)).sum()
    fp = ((preds == 1) & (actuals == 0)).sum()
    fn = ((preds == 0) & (actuals == 1)).sum()
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0
    
    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "accuracy": float(accuracy),
        "confusion_matrix": {
            "tp": int(tp),
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn)
        }
    }

def calculate_correlation(test_df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Pearson and Spearman correlation coefficients between connectivity and collapse.
    
    Args:
        test_df: DataFrame with 'connectivity' and 'collapse' columns.
        
    Returns:
        Dictionary with correlation coefficients.
    """
    pearson_r, _ = scipy.stats.pearsonr(test_df['connectivity'], test_df['collapse'])
    spearman_r, _ = scipy.stats.spearmanr(test_df['connectivity'], test_df['collapse'])
    
    return {
        "pearson_r": float(pearson_r),
        "spearman_r": float(spearman_r)
    }

def run_sensitivity_analysis_threshold(test_df: pd.DataFrame, thresholds: List[float]) -> List[Dict[str, Any]]:
    """
    Run sensitivity analysis over a list of thresholds.
    
    Args:
        test_df: DataFrame with 'collapse' and 'connectivity' columns.
        thresholds: List of threshold values to test.
        
    Returns:
        List of dictionaries containing metrics for each threshold.
    """
    results = []
    for thresh in thresholds:
        df = test_df.copy()
        df['predicted_collapse'] = (df['connectivity'] < thresh).astype(int)
        metrics = evaluate_performance(df)
        metrics['threshold'] = thresh
        results.append(metrics)
    return results

def run_sensitivity_analysis_percentile(test_df: pd.DataFrame, percentiles: List[float]) -> List[Dict[str, Any]]:
    """
    Run sensitivity analysis over a list of percentiles (calculated on test set for analysis).
    
    Args:
        test_df: DataFrame with 'collapse' and 'connectivity' columns.
        percentiles: List of percentile values (0.0 to 1.0) to test.
        
    Returns:
        List of dictionaries containing metrics for each percentile.
    """
    results = []
    # Note: In a real scenario, percentiles should be calculated on a validation set,
    # but for this analysis, we calculate on the test set to sweep the range.
    for p in percentiles:
        thresh = test_df['connectivity'].quantile(p)
        df = test_df.copy()
        df['predicted_collapse'] = (df['connectivity'] < thresh).astype(int)
        metrics = evaluate_performance(df)
        metrics['percentile'] = p
        metrics['threshold_value'] = thresh
        results.append(metrics)
    return results

def calculate_null_distribution(test_df: pd.DataFrame, n_permutations: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """
    Perform permutation test to establish null distribution.
    
    Args:
        test_df: DataFrame with 'connectivity' and 'collapse' columns.
        n_permutations: Number of permutations.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing null distribution stats and p-value.
    """
    np.random.seed(seed)
    actual_corr = scipy.stats.spearmanr(test_df['connectivity'], test_df['collapse'])[0]
    
    null_corrs = []
    for _ in range(n_permutations):
        shuffled_labels = np.random.permutation(test_df['collapse'].values)
        corr, _ = scipy.stats.spearmanr(test_df['connectivity'], shuffled_labels)
        null_corrs.append(corr)
        
    null_corrs = np.array(null_corrs)
    p_value = (np.abs(null_corrs) >= np.abs(actual_corr)).mean()
    sc_002_passed = p_value < 0.05
    
    return {
        "actual_r": float(actual_corr),
        "null_mean": float(null_corrs.mean()),
        "null_std": float(null_corrs.std()),
        "p_value": float(p_value),
        "sc_002_passed": sc_002_passed
    }

def calculate_linear_reasoning_index(graphs_dir: str, train_metrics: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate linear reasoning index based on graph topology and metrics.
    This is a placeholder for the logic defined in T037b.
    """
    # Implementation would load graphs and calculate chain-like topology metrics
    # For now, return a default structure
    return {
        "linear_reasoning_confirmed": False,
        "threshold_used": 0.0
    }

def calculate_power_analysis(train_df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate effect size (Cohen's d) and perform post-hoc power analysis.
    """
    success = train_df[train_df['collapse'] == 0]['connectivity']
    collapse = train_df[train_df['collapse'] == 1]['connectivity']
    
    if len(success) == 0 or len(collapse) == 0:
        return {"cohens_d": 0.0, "power": 0.0, "power_sufficient": False}
        
    mean_diff = success.mean() - collapse.mean()
    pooled_std = np.sqrt(((success.std()**2 * (len(success)-1)) + (collapse.std()**2 * (len(collapse)-1))) / (len(success) + len(collapse) - 2))
    
    cohens_d = mean_diff / pooled_std if pooled_std != 0 else 0.0
    
    # Simplified power calculation (using normal approximation)
    # In practice, use statsmodels.stats.power.TTestIndPower
    n_per_group = min(len(success), len(collapse))
    power = 1 - scipy.stats.norm.cdf(scipy.stats.norm.ppf(0.95) - abs(cohens_d) * np.sqrt(n_per_group / 2))
    
    return {
        "cohens_d": float(cohens_d),
        "power": float(power),
        "power_sufficient": power >= 0.8
    }

def report_comparative_thresholds(threshold_20: float, threshold_f1: float, sensitivity_thresholds: List[Dict], sensitivity_percentiles: List[Dict]) -> Dict[str, Any]:
    """
    Generate a comparative report of thresholds.
    """
    return {
        "primary_threshold_20th_percentile": threshold_20,
        "comparative_threshold_f1_max": threshold_f1,
        "sensitivity_threshold_matrix": sensitivity_thresholds,
        "sensitivity_percentile_matrix": sensitivity_percentiles,
        "difference": abs(threshold_20 - threshold_f1)
    }

def generate_results_report(
    threshold_20: float, 
    threshold_f1: float, 
    predictions_df: pd.DataFrame, 
    baseline: float,
    correlation: Dict,
    null_dist: Dict,
    linear_reasoning: Dict,
    power: Dict,
    comparative: Dict,
    sensitivity_thresh: List,
    sensitivity_pct: List
) -> Dict[str, Any]:
    """
    Generate the final results report aggregating all metrics.
    """
    performance = evaluate_performance(predictions_df)
    
    return {
        "thresholds": {
            "primary_20th_percentile": threshold_20,
            "comparative_f1_max": threshold_f1
        },
        "baseline": {
            "mean_connectivity_success": baseline
        },
        "performance": performance,
        "correlation": correlation,
        "null_distribution": null_dist,
        "linear_reasoning": linear_reasoning,
        "power_analysis": power,
        "comparative_report": comparative,
        "sensitivity_analysis": {
            "thresholds": sensitivity_thresh,
            "percentiles": sensitivity_pct
        }
    }

def main():
    """
    Main entry point for the evaluator module.
    Orchestrates the calculation of thresholds, predictions, and reports.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Ensure directories exist
    ensure_directories("data/processed/threshold_config.json")
    
    # Load metrics
    try:
        metrics_df = load_metrics("data/processed/metrics.csv")
    except FileNotFoundError as e:
        logger.error(f"Failed to load metrics: {e}")
        return
        
    # Split data
    train_df, test_df = stratified_split(metrics_df)
    save_metrics(train_df, "data/processed/train_metrics.csv")
    save_metrics(test_df, "data/processed/test_metrics.csv")
    
    # Calculate Baseline
    baseline = calculate_baseline(train_df)
    save_json_file({"baseline_mean_connectivity": baseline}, "data/processed/baseline_report.json")
    
    # Calculate Primary Threshold (20th Percentile)
    threshold_20 = calculate_20th_percentile_threshold(train_df)
    save_json_file({"threshold_20th_percentile": threshold_20}, "data/processed/threshold_config.json")
    
    # Calculate Comparative Threshold (F1 Max)
    threshold_f1 = calculate_f1_max_threshold(train_df)
    save_json_file({"threshold_f1_max": threshold_f1}, "data/processed/f1_max_threshold.json")
    
    # Predict Collapse on Test Set
    test_df_pred = predict_collapse(test_df, threshold_20)
    
    # Evaluate Performance
    performance = evaluate_performance(test_df_pred)
    
    # Correlation
    correlation = calculate_correlation(test_df_pred)
    
    # Null Distribution
    null_dist = calculate_null_distribution(test_df_pred)
    
    # Sensitivity Analysis (Thresholds from config)
    from config import sensitivity_thresholds, sensitivity_percentiles
    sensitivity_thresh_results = run_sensitivity_analysis_threshold(test_df_pred, sensitivity_thresholds)
    sensitivity_pct_results = run_sensitivity_analysis_percentile(test_df_pred, [p/100.0 for p in sensitivity_percentiles])
    
    save_json_file({"sensitivity_threshold_matrix": sensitivity_thresh_results}, "data/processed/sensitivity_threshold_matrix.json")
    save_json_file({"sensitivity_percentile_matrix": sensitivity_pct_results}, "data/processed/sensitivity_percentile_matrix.json")
    
    # Comparative Report
    comparative = report_comparative_thresholds(threshold_20, threshold_f1, sensitivity_thresh_results, sensitivity_pct_results)
    save_json_file(comparative, "data/processed/comparative_report.json")
    
    # Linear Reasoning (Placeholder)
    linear_reasoning = calculate_linear_reasoning_index("data/processed/graphs/", train_df)
    save_json_file(linear_reasoning, "data/processed/linear_reasoning_report.json")
    
    # Power Analysis
    power = calculate_power_analysis(train_df)
    save_json_file(power, "data/processed/power_analysis.json")
    
    # Final Report
    final_report = generate_results_report(
        threshold_20, threshold_f1, test_df_pred, baseline,
        correlation, null_dist, linear_reasoning, power,
        comparative, sensitivity_thresh_results, sensitivity_pct_results
    )
    save_json_file(final_report, "data/processed/results_report.json")
    
    logger.info("Evaluator pipeline completed successfully.")

if __name__ == "__main__":
    main()
