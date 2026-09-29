import numpy as np
from typing import Dict, Tuple, List, Optional
from scipy import stats
import json
from pathlib import Path

def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return np.mean(np.abs(y_true - y_pred))

def compute_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot)

def compute_metrics_per_property(y_true: Dict[str, np.ndarray], y_pred: Dict[str, np.ndarray]) -> Dict[str, Dict[str, float]]:
    results = {}
    for key in y_true:
        results[key] = {
            "mae": compute_mae(y_true[key], y_pred[key]),
            "r2": compute_r2(y_true[key], y_pred[key])
        }
    return results

def paired_ttest_mean_zero(errors: np.ndarray) -> Tuple[float, float]:
    """Paired t-test against zero mean."""
    t_stat, p_val = stats.ttest_1samp(errors, 0.0)
    return t_stat, p_val

def tost_equivalence_test(errors: np.ndarray, equivalence_margin: float = 0.1) -> Tuple[float, float]:
    """TOST for equivalence testing."""
    t1, p1 = stats.ttest_1samp(errors, equivalence_margin)
    t2, p2 = stats.ttest_1samp(errors, -equivalence_margin)
    return p1, p2

def hotellings_t2_test(errors: np.ndarray) -> float:
    """Hotelling's T-squared test for multivariate mean."""
    n = len(errors)
    mean_err = np.mean(errors)
    var_err = np.var(errors, ddof=1)
    t2 = (n * mean_err**2) / var_err
    return t2

def compute_all_statistics(y_true: Dict[str, np.ndarray], y_pred: Dict[str, np.ndarray]) -> Dict[str, Any]:
    metrics = compute_metrics_per_property(y_true, y_pred)
    stats_results = {}
    
    for key in y_true:
        errors = y_true[key] - y_pred[key]
        t_stat, p_val = paired_ttest_mean_zero(errors)
        stats_results[key] = {
            "t_stat": float(t_stat),
            "p_value": float(p_val)
        }
    
    return {"metrics": metrics, "statistical_tests": stats_results}

def main(y_true_path: str, y_pred_path: str, output_path: str):
    y_true = np.load(y_true_path)
    y_pred = np.load(y_pred_path)
    results = compute_all_statistics(y_true, y_pred)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    pass