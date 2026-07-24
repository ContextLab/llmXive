import csv
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
from config import ensure_directories

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_metrics(filepath: str) -> List[Dict[str, Any]]:
    """Load metrics from a CSV file."""
    metrics = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats/ints
            if 'connectivity' in row:
                row['connectivity'] = float(row['connectivity'])
            if 'branching_factor' in row:
                row['branching_factor'] = float(row['branching_factor'])
            if 'collapse' in row:
                # Handle boolean conversion if stored as string
                val = row['collapse']
                if isinstance(val, str):
                    row['collapse'] = val.lower() in ('true', '1', 'yes')
                else:
                    row['collapse'] = bool(val)
            metrics.append(row)
    return metrics

def save_metrics(metrics: List[Dict[str, Any]], filepath: str) -> None:
    """Save metrics to a CSV file."""
    ensure_directories(filepath)
    fieldnames = ['trajectory_id', 'connectivity', 'branching_factor', 'collapse', 'predicted_collapse']
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in metrics:
            # Ensure all fields are present
            row = {k: m.get(k, '') for k in fieldnames}
            writer.writerow(row)

def load_json_file(filepath: str) -> Any:
    """Load a JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json_file(data: Any, filepath: str) -> None:
    """Save data to a JSON file."""
    ensure_directories(filepath)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def stratified_split(data: List[Dict], test_size: float = 0.2) -> Tuple[List[Dict], List[Dict]]:
    """Split data into train/test sets preserving label balance."""
    import random
    random.seed(42)
    success = [d for d in data if d.get('collapse') == False]
    failure = [d for d in data if d.get('collapse') == True]
    
    random.shuffle(success)
    random.shuffle(failure)
    
    n_success_test = int(len(success) * test_size)
    n_failure_test = int(len(failure) * test_size)
    
    test_data = success[:n_success_test] + failure[:n_failure_test]
    train_data = success[n_success_test:] + failure[n_failure_test:]
    
    return train_data, test_data

def calculate_baseline(train_metrics: List[Dict]) -> float:
    """Calculate mean connectivity of the success class."""
    success_metrics = [m for m in train_metrics if m.get('collapse') == False]
    if not success_metrics:
        logger.warning("No success class samples found for baseline calculation.")
        return 0.0
    return sum(m['connectivity'] for m in success_metrics) / len(success_metrics)

def calculate_20th_percentile_threshold(train_metrics: List[Dict]) -> float:
    """Calculate 20th percentile of connectivity for success class."""
    success_metrics = [m['connectivity'] for m in train_metrics if m.get('collapse') == False]
    if not success_metrics:
        logger.warning("No success class samples for threshold calculation.")
        return 0.0
    success_metrics.sort()
    idx = int(len(success_metrics) * 0.20)
    if idx >= len(success_metrics):
        idx = len(success_metrics) - 1
    return success_metrics[idx]

def calculate_f1_max_threshold(train_metrics: List[Dict]) -> float:
    """Calculate optimal F1-score threshold for comparative analysis."""
    # Simple grid search for optimal threshold
    thresholds = [i * 0.01 for i in range(101)]
    best_f1 = -1
    best_thresh = 0.0
    true_labels = [m['collapse'] for m in train_metrics]
    
    for thresh in thresholds:
        preds = [m['connectivity'] < thresh for m in train_metrics]
        if sum(preds) == 0 or sum(preds) == len(preds):
            continue # Skip trivial predictions
        f1 = f1_score(true_labels, preds, pos_label=True)
        if f1 > best_f1:
            best_f1 = f1
            best_thresh = thresh
    return best_thresh

def predict_collapse(test_metrics: List[Dict], threshold: float) -> List[Dict]:
    """Predict collapse based on threshold."""
    for m in test_metrics:
        m['predicted_collapse'] = m['connectivity'] < threshold
    return test_metrics

def evaluate_performance(test_metrics: List[Dict]) -> Dict[str, Any]:
    """
    Evaluate performance: Precision, Recall, F1, Confusion Matrix.
    Input: test_metrics (list of dicts with 'collapse' and 'predicted_collapse')
    Output: dict with metrics and confusion matrix data.
    """
    if not test_metrics:
        logger.warning("No test metrics provided for evaluation.")
        return {
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'confusion_matrix': [[0, 0], [0, 0]],
            'support': 0
        }

    true_labels = [1 if m.get('collapse') else 0 for m in test_metrics]
    pred_labels = [1 if m.get('predicted_collapse') else 0 for m in test_metrics]

    # Calculate metrics
    precision = precision_score(true_labels, pred_labels, zero_division=0)
    recall = recall_score(true_labels, pred_labels, zero_division=0)
    f1 = f1_score(true_labels, pred_labels, zero_division=0)
    
    cm = confusion_matrix(true_labels, pred_labels)
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'confusion_matrix': cm.tolist(),
        'support': len(true_labels)
    }

def calculate_correlation(test_metrics: List[Dict]) -> Dict[str, float]:
    """Calculate Pearson and Spearman correlation between connectivity and collapse."""
    import scipy.stats as stats
    if len(test_metrics) < 2:
        return {'pearson': 0.0, 'spearman': 0.0}
    
    x = [m['connectivity'] for m in test_metrics]
    y = [1 if m.get('collapse') else 0 for m in test_metrics]
    
    pearson_r, _ = stats.pearsonr(x, y)
    spearman_r, _ = stats.spearmanr(x, y)
    
    return {'pearson': pearson_r, 'spearman': spearman_r}

def run_sensitivity_analysis(test_metrics: List[Dict]) -> List[Dict]:
    """Run sensitivity analysis over a range of thresholds."""
    thresholds = [0.01, 0.05, 0.1]
    percentiles = [10, 20, 30]
    results = []
    
    for p in percentiles:
        for t in thresholds:
            # Simulate prediction with current threshold
            preds = [1 if m['connectivity'] < t else 0 for m in test_metrics]
            if sum(preds) == 0 or sum(preds) == len(preds):
                f1 = 0.0
            else:
                true_labels = [1 if m.get('collapse') else 0 for m in test_metrics]
                f1 = f1_score(true_labels, preds, zero_division=0)
            
            results.append({
                'percentile': p,
                'threshold_value': t,
                'f1_score': f1
            })
    return results

def calculate_null_distribution(test_metrics: List[Dict], n_permutations: int = 1000) -> Dict[str, Any]:
    """Perform permutation test for correlation significance."""
    import numpy as np
    import scipy.stats as stats
    
    x = np.array([m['connectivity'] for m in test_metrics])
    y = np.array([1 if m.get('collapse') else 0 for m in test_metrics])
    
    # Observed correlation
    r_obs, _ = stats.pearsonr(x, y)
    
    # Permutation test
    r_null = []
    for _ in range(n_permutations):
        np.random.shuffle(y)
        r, _ = stats.pearsonr(x, y)
        r_null.append(abs(r))
    
    p_value = sum(1 for r in r_null if abs(r) >= abs(r_obs)) / n_permutations
    significant = p_value < 0.05
    
    return {
        'observed_r': r_obs,
        'p_value': p_value,
        'sc_002_passed': significant,
        'n_permutations': n_permutations
    }

def calculate_linear_reasoning_index(test_metrics: List[Dict], graphs_dir: str) -> Dict[str, Any]:
    """Calculate linear reasoning index based on graph topology."""
    # This would require loading graph files, but for now we return a placeholder
    # based on metric thresholds as a proxy if graphs are not available
    low_branching = [m for m in test_metrics if m.get('branching_factor', 100) < 1.5]
    low_connectivity = [m for m in test_metrics if m.get('connectivity', 100) < 0.1]
    
    # Intersection of low branching and low connectivity
    linear_candidates = [m for m in low_branching if m in low_connectivity]
    
    # Simplified check: if a significant portion of success class has these properties
    success_class = [m for m in test_metrics if not m.get('collapse')]
    if not success_class:
        return {'linear_reasoning_confirmed': False}
    
    ratio = len(linear_candidates) / len(success_class)
    return {'linear_reasoning_confirmed': ratio > 0.5}

def calculate_power_analysis(train_metrics: List[Dict]) -> Dict[str, Any]:
    """Calculate effect size (Cohen's d) and power."""
    import numpy as np
    from statsmodels.stats.power import TTestIndPower
    
    success_vals = [m['connectivity'] for m in train_metrics if not m.get('collapse')]
    failure_vals = [m['connectivity'] for m in train_metrics if m.get('collapse')]
    
    if len(success_vals) < 2 or len(failure_vals) < 2:
        return {'effect_size': 0.0, 'power': 0.0, 'sample_size_sufficient': False}
    
    mean1, std1 = np.mean(success_vals), np.std(success_vals)
    mean2, std2 = np.mean(failure_vals), np.std(failure_vals)
    n1, n2 = len(success_vals), len(failure_vals)
    
    pooled_std = np.sqrt(((n1-1)*std1**2 + (n2-1)*std2**2) / (n1+n2-2))
    if pooled_std == 0:
        effect_size = 0.0
    else:
        effect_size = abs(mean1 - mean2) / pooled_std
    
    # Power analysis
    power_analysis = TTestIndPower()
    power = power_analysis.solve_power(effect_size=effect_size, nobs1=n1, alpha=0.05, ratio=n2/n1)
    
    return {
        'effect_size': effect_size,
        'power': power,
        'sample_size_sufficient': power >= 0.8
    }

def report_comparative_thresholds(threshold_config: Dict, f1_max_config: Dict, sensitivity_matrix: List[Dict]) -> Dict[str, Any]:
    """Compare mandatory 20th percentile with F1-max and sensitivity data."""
    return {
        'mandatory_threshold': threshold_config.get('threshold_value'),
        'f1_max_threshold': f1_max_config.get('threshold_value'),
        'sensitivity_summary': sensitivity_matrix
    }

def generate_results_report(
    baseline: Dict, 
    threshold_config: Dict, 
    f1_max_config: Dict, 
    sensitivity_matrix: List[Dict], 
    performance: Dict, 
    correlation: Dict, 
    null_dist: Dict, 
    linear_reasoning: Dict, 
    power_analysis: Dict, 
    comparative: Dict
) -> Dict[str, Any]:
    """Generate the final results report."""
    return {
        'baseline': baseline,
        'thresholds': {
            'mandatory': threshold_config,
            'f1_max': f1_max_config
        },
        'sensitivity_analysis': sensitivity_matrix,
        'performance_metrics': performance,
        'correlation': correlation,
        'null_distribution': null_dist,
        'linear_reasoning': linear_reasoning,
        'power_analysis': power_analysis,
        'comparative_report': comparative
    }

def main():
    """Main entry point for evaluation pipeline."""
    ensure_directories("data/processed/test_metrics.csv")
    
    # Load test metrics (assumes T032 has populated this)
    test_metrics_path = "data/processed/test_metrics.csv"
    if not os.path.exists(test_metrics_path):
        logger.error(f"Test metrics file not found: {test_metrics_path}")
        return
    
    test_metrics = load_metrics(test_metrics_path)
    
    # Load threshold from T030 (assuming it was saved to threshold_config.json)
    threshold_config_path = "data/processed/threshold_config.json"
    if os.path.exists(threshold_config_path):
        threshold_data = load_json_file(threshold_config_path)
        threshold = threshold_data.get('threshold_value', 0.0)
    else:
        logger.warning("Threshold config not found. Using default 0.0.")
        threshold = 0.0
    
    # Predict collapse
    test_metrics = predict_collapse(test_metrics, threshold)
    
    # Evaluate performance
    performance = evaluate_performance(test_metrics)
    
    # Save results
    results_path = "data/processed/performance_metrics.json"
    save_json_file(performance, results_path)
    logger.info(f"Performance metrics saved to {results_path}")
    
    # Print summary
    print(f"Performance Summary:")
    print(f"  Precision: {performance['precision']:.4f}")
    print(f"  Recall: {performance['recall']:.4f}")
    print(f"  F1-Score: {performance['f1']:.4f}")
    print(f"  Confusion Matrix: {performance['confusion_matrix']}")

if __name__ == "__main__":
    main()
