import csv
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

# Ensure scipy is available for correlation calculations
try:
    from scipy.stats import pearsonr, spearmanr
except ImportError:
    raise ImportError("scipy is required for correlation calculations. Install with: pip install scipy")

from config import ensure_directories

DATA_PROCESSED = Path("data/processed")
TEST_METRICS_FILE = DATA_PROCESSED / "test_metrics.csv"


def load_metrics(filepath: Path) -> List[Dict[str, Any]]:
    """Load metrics from a CSV file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Metrics file not found: {filepath}")
    
    metrics = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats
            cleaned_row = {}
            for k, v in row.items():
                if v.lower() == 'nan' or v == '':
                    cleaned_row[k] = 0.0
                else:
                    try:
                        cleaned_row[k] = float(v)
                    except ValueError:
                        cleaned_row[k] = v
            metrics.append(cleaned_row)
    return metrics


def save_metrics(metrics: List[Dict[str, Any]], filepath: Path) -> None:
    """Save metrics to a CSV file."""
    if not metrics:
        return
    
    ensure_directories(filepath)
    fieldnames = list(metrics[0].keys())
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics)


def stratified_split(metrics: List[Dict[str, Any]], test_size: float = 0.2) -> Tuple[List[Dict], List[Dict]]:
    """
    Split metrics into train and test sets while preserving label balance.
    Assumes 'collapse' column exists with binary values (0 or 1).
    """
    if not metrics:
        return [], []
    
    # Separate by label
    success = [m for m in metrics if m.get('collapse', 0) == 1]
    failure = [m for m in metrics if m.get('collapse', 0) == 0]
    
    # Calculate split sizes
    n_success = max(1, int(len(success) * test_size))
    n_failure = max(1, int(len(failure) * test_size))
    
    # Shuffle deterministically
    np.random.seed(42)
    np.random.shuffle(success)
    np.random.shuffle(failure)
    
    # Split
    test_success = success[:n_success]
    train_success = success[n_success:]
    test_failure = failure[:n_failure]
    train_failure = failure[n_failure:]
    
    train_set = train_success + train_failure
    test_set = test_success + test_failure
    
    return train_set, test_set


def calculate_20th_percentile_threshold(train_metrics: List[Dict[str, Any]], metric_name: str = 'global_connectivity') -> float:
    """
    Calculate the 20th percentile threshold for the success class.
    Primary threshold per FR-004.
    """
    success_values = [m[metric_name] for m in train_metrics if m.get('collapse', 0) == 1]
    
    if not success_values:
        raise ValueError("No success class samples found in training data.")
    
    # Sort and get 20th percentile
    sorted_values = sorted(success_values)
    index = int(0.2 * len(sorted_values))
    # Clamp index to valid range
    index = min(index, len(sorted_values) - 1)
    
    return sorted_values[index]


def calculate_f1_max_threshold(train_metrics: List[Dict[str, Any]], metric_name: str = 'global_connectivity') -> float:
    """
    Calculate the optimal threshold for maximum F1-score on training data.
    Comparative analysis only.
    """
    # Get unique values to test as thresholds
    all_values = sorted(set(m[metric_name] for m in train_metrics))
    
    if not all_values:
        raise ValueError("No metrics found to calculate F1-max threshold.")
    
    best_f1 = -1.0
    best_threshold = all_values[0]
    
    for threshold in all_values:
        tp = fp = tn = fn = 0
        for m in train_metrics:
            val = m[metric_name]
            label = m.get('collapse', 0)
            # Predict collapse if metric < threshold (lower connectivity -> collapse)
            pred = 1 if val < threshold else 0
            
            if pred == 1 and label == 1:
                tp += 1
            elif pred == 1 and label == 0:
                fp += 1
            elif pred == 0 and label == 0:
                tn += 1
            else:
                fn += 1
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold
    
    return best_threshold


def predict_collapse(test_metrics: List[Dict[str, Any]], threshold: float, metric_name: str = 'global_connectivity') -> List[Dict[str, Any]]:
    """
    Predict collapse based on threshold.
    Assumes lower connectivity indicates collapse (pred=1 if val < threshold).
    """
    predictions = []
    for m in test_metrics:
        val = m[metric_name]
        pred = 1 if val < threshold else 0
        new_row = m.copy()
        new_row['predicted_collapse'] = pred
        predictions.append(new_row)
    return predictions


def evaluate_performance(predictions: List[Dict[str, Any]], metric_name: str = 'global_connectivity') -> Dict[str, Any]:
    """
    Calculate Precision, Recall, F1, and Confusion Matrix.
    """
    if not predictions:
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'confusion_matrix': {'tp': 0, 'fp': 0, 'tn': 0, 'fn': 0}
        }
    
    tp = fp = tn = fn = 0
    for m in predictions:
        label = m.get('collapse', 0)
        pred = m.get('predicted_collapse', 0)
        
        if pred == 1 and label == 1:
            tp += 1
        elif pred == 1 and label == 0:
            fp += 1
        elif pred == 0 and label == 0:
            tn += 1
        else:
            fn += 1
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'confusion_matrix': {'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn}
    }


def calculate_baseline(train_metrics: List[Dict[str, Any]], metric_name: str = 'global_connectivity') -> float:
    """
    Calculate mean connectivity of the success class (FR-007).
    """
    success_values = [m[metric_name] for m in train_metrics if m.get('collapse', 0) == 1]
    
    if not success_values:
        return 0.0
    
    return float(np.mean(success_values))


def calculate_correlation(test_metrics: List[Dict[str, Any]], metric_name: str = 'global_connectivity') -> Dict[str, float]:
    """
    Calculate Pearson and Spearman correlation coefficients between connectivity and collapse.
    Input: data/processed/test_metrics.csv
    Output: Dict with 'pearson_r', 'pearson_p', 'spearman_r', 'spearman_p'
    SC-002: Report correlation coefficient (r).
    """
    if not test_metrics:
        raise ValueError("No test metrics provided for correlation calculation.")
    
    # Extract vectors
    connectivity = np.array([m[metric_name] for m in test_metrics])
    collapse = np.array([m.get('collapse', 0) for m in test_metrics])
    
    # Validate data
    if len(connectivity) == 0 or len(collapse) == 0:
        raise ValueError("Connectivity or collapse vectors are empty.")
    
    # Calculate Pearson correlation
    pearson_r, pearson_p = pearsonr(connectivity, collapse)
    
    # Calculate Spearman correlation
    spearman_r, spearman_p = spearmanr(connectivity, collapse)
    
    return {
        'pearson_r': float(pearson_r),
        'pearson_p': float(pearson_p),
        'spearman_r': float(spearman_r),
        'spearman_p': float(spearman_p)
    }


def run_sensitivity_analysis(test_metrics: List[Dict[str, Any]], thresholds: List[float] = None, percentiles: List[int] = None) -> Dict[str, Any]:
    """
    Sweep thresholds over specific sets and report full matrix.
    """
    if thresholds is None:
        thresholds = [0.01, 0.05, 0.1]
    if percentiles is None:
        percentiles = [10, 15, 20, 25, 30]
    
    results = {
        'fixed_thresholds': {},
        'percentile_thresholds': {}
    }
    
    # Fixed thresholds
    for t in thresholds:
        preds = predict_collapse(test_metrics, t)
        metrics = evaluate_performance(preds)
        results['fixed_thresholds'][t] = metrics
    
    # Percentile thresholds (calculated on train would be better, but using test for analysis here)
    # Note: In a real pipeline, these would be calculated on train and applied to test.
    # For sensitivity analysis on test set, we simulate by calculating percentiles of the test set.
    for p in percentiles:
        all_vals = sorted([m['global_connectivity'] for m in test_metrics])
        idx = int((p / 100) * len(all_vals))
        idx = min(idx, len(all_vals) - 1)
        t = all_vals[idx]
        
        preds = predict_collapse(test_metrics, t)
        metrics = evaluate_performance(preds)
        results['percentile_thresholds'][p] = {
            'threshold': t,
            'metrics': metrics
        }
    
    return results


def calculate_null_distribution(test_metrics: List[Dict[str, Any]], n_permutations: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """
    Perform permutation test to establish null distribution for correlation.
    Input: data/processed/test_metrics.csv
    Output: Dict with 'null_distribution', 'observed_r', 'p_value', 'pass_fail'
    """
    np.random.seed(seed)
    
    connectivity = np.array([m['global_connectivity'] for m in test_metrics])
    collapse = np.array([m.get('collapse', 0) for m in test_metrics])
    
    if len(connectivity) == 0 or len(collapse) == 0:
        raise ValueError("Cannot calculate null distribution with empty data.")
    
    # Observed correlation
    obs_r, _ = pearsonr(connectivity, collapse)
    
    # Permutation test
    null_r = []
    for _ in range(n_permutations):
        permuted_collapse = collapse.copy()
        np.random.shuffle(permuted_collapse)
        r, _ = pearsonr(connectivity, permuted_collapse)
        null_r.append(r)
    
    null_r = np.array(null_r)
    
    # Calculate p-value (two-tailed)
    # Count how many permuted |r| >= |obs_r|
    extreme_count = np.sum(np.abs(null_r) >= np.abs(obs_r))
    p_value = extreme_count / n_permutations
    
    # Pass/Fail: Reject null if p < 0.05
    pass_fail = p_value < 0.05
    
    return {
        'null_distribution': null_r.tolist(),
        'observed_r': float(obs_r),
        'p_value': float(p_value),
        'pass_fail': pass_fail
    }


def generate_results_report(
    threshold_20th: float,
    threshold_f1_max: float,
    predictions: List[Dict[str, Any]],
    performance: Dict[str, Any],
    baseline: float,
    correlation: Dict[str, float],
    sensitivity: Dict[str, Any],
    null_dist: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate comprehensive results report.
    """
    return {
        'thresholds': {
            'primary_20th_percentile': threshold_20th,
            'comparative_f1_max': threshold_f1_max
        },
        'performance': performance,
        'baseline': {
            'mean_success_connectivity': baseline
        },
        'correlation': correlation,
        'sensitivity_analysis': sensitivity,
        'null_distribution_test': null_dist
    }


def calculate_linear_reasoning_index(test_metrics: List[Dict[str, Any]], graphs_dir: Path) -> Dict[str, Any]:
    """
    Calculate a chain-like topology metric (ratio of nodes with degree 2) for success class.
    Input: test_metrics.csv and graphs from T017.
    Output: data/processed/linear_reasoning_report.json
    """
    # This is a placeholder for the actual graph loading logic which would be complex
    # For now, we return a structure indicating the metric would be calculated
    return {
        'metric': 'linear_reasoning_index',
        'description': 'Ratio of nodes with degree 2 in success class graphs',
        'status': 'implementation_required',
        'note': 'Requires loading individual graph JSONs from data/processed/graphs/ and calculating degree distribution.'
    }


def main():
    """
    Main entry point for the evaluation pipeline.
    Orchestrates T030-T037b logic.
    """
    ensure_directories(TEST_METRICS_FILE)
    
    if not TEST_METRICS_FILE.exists():
        print(f"Error: {TEST_METRICS_FILE} not found. Run metrics pipeline first.")
        return
    
    # Load test metrics
    test_metrics = load_metrics(TEST_METRICS_FILE)
    print(f"Loaded {len(test_metrics)} test metrics.")
    
    # T030: Calculate primary threshold (20th percentile) on TRAIN data
    # Note: We assume train_metrics.csv exists from T029
    train_metrics_path = DATA_PROCESSED / "train_metrics.csv"
    if train_metrics_path.exists():
        train_metrics = load_metrics(train_metrics_path)
        threshold_20th = calculate_20th_percentile_threshold(train_metrics)
        threshold_f1_max = calculate_f1_max_threshold(train_metrics)
    else:
        print("Warning: train_metrics.csv not found. Using dummy thresholds for demonstration.")
        threshold_20th = 0.05
        threshold_f1_max = 0.05
        # Create dummy train metrics if needed for downstream logic
        train_metrics = []
    
    # T032: Predict collapse on test set
    predictions = predict_collapse(test_metrics, threshold_20th)
    
    # T033: Evaluate performance
    performance = evaluate_performance(predictions)
    
    # T034: Calculate baseline (mean connectivity of success class in train)
    baseline = calculate_baseline(train_metrics) if train_metrics else 0.0
    
    # T035: Calculate correlation (SC-002)
    correlation = calculate_correlation(test_metrics)
    print(f"Correlation (Pearson r): {correlation['pearson_r']:.4f} (p={correlation['pearson_p']:.4f})")
    print(f"Correlation (Spearman r): {correlation['spearman_r']:.4f} (p={correlation['spearman_p']:.4f})")
    
    # T036: Sensitivity analysis
    sensitivity = run_sensitivity_analysis(test_metrics)
    
    # T037a: Null distribution
    null_dist = calculate_null_distribution(test_metrics)
    print(f"Null distribution test p-value: {null_dist['p_value']:.4f} (Pass: {null_dist['pass_fail']})")
    
    # T037b: Generate report
    report = generate_results_report(
        threshold_20th, threshold_f1_max, predictions, performance,
        baseline, correlation, sensitivity, null_dist
    )
    
    # Save report
    report_path = DATA_PROCESSED / "results_report.json"
    ensure_directories(report_path)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print(f"Results report saved to {report_path}")
    
    # T038: Linear reasoning index
    graphs_dir = DATA_PROCESSED / "graphs"
    lri = calculate_linear_reasoning_index(test_metrics, graphs_dir)
    lri_path = DATA_PROCESSED / "linear_reasoning_report.json"
    with open(lri_path, 'w', encoding='utf-8') as f:
        json.dump(lri, f, indent=2)
    print(f"Linear reasoning report saved to {lri_path}")


if __name__ == "__main__":
    main()
