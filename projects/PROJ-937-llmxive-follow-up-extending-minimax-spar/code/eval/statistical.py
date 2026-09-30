import numpy as np
from scipy import stats
from typing import List, Dict, Any, Tuple, Optional
import logging
import json
from pathlib import Path

from utils.logger import get_logger_for_task

logger = get_logger_for_task(__name__)

def run_paired_ttest(
    heuristic_scores: List[float],
    baseline_scores: List[float]
) -> Tuple[float, float]:
    """
    Run a paired t-test between heuristic and baseline scores.
    
    Returns:
        Tuple of (t_statistic, p_value)
    """
    if len(heuristic_scores) != len(baseline_scores):
        raise ValueError("Score lists must be of equal length for paired test")
    
    if len(heuristic_scores) < 2:
        logger.warning("Insufficient data for t-test (n < 2)")
        return 0.0, 1.0

    t_stat, p_val = stats.ttest_rel(heuristic_scores, baseline_scores)
    return float(t_stat), float(p_val)

def run_wilcoxon_test(
    heuristic_scores: List[float],
    baseline_scores: List[float]
) -> Tuple[float, float]:
    """
    Run a Wilcoxon signed-rank test between heuristic and baseline scores.
    
    Returns:
        Tuple of (statistic, p_value)
    """
    if len(heuristic_scores) != len(baseline_scores):
        raise ValueError("Score lists must be of equal length for Wilcoxon test")
    
    if len(heuristic_scores) < 2:
        logger.warning("Insufficient data for Wilcoxon test (n < 2)")
        return 0.0, 1.0

    # Filter out zero differences to avoid issues in scipy
    diffs = np.array(heuristic_scores) - np.array(baseline_scores)
    valid_mask = diffs != 0
    if np.sum(valid_mask) < 2:
        logger.warning("Insufficient non-zero differences for Wilcoxon test")
        return 0.0, 1.0

    w_stat, p_val = stats.wilcoxon(
        np.array(heuristic_scores)[valid_mask],
        np.array(baseline_scores)[valid_mask]
    )
    return float(w_stat), float(p_val)

def apply_holm_bonferroni(p_values: List[float]) -> List[float]:
    """
    Apply Holm-Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of uncorrected p-values.
        
    Returns:
        List of adjusted p-values.
    """
    if not p_values:
        return []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_pvals = np.array(p_values)[sorted_indices]
    
    adjusted = np.empty(n)
    for i, p in enumerate(sorted_pvals):
        # Holm-Bonferroni: p * (n - i)
        # Ensure it doesn't exceed 1.0
        adjusted[i] = min(1.0, p * (n - i))
    
    # Restore original order
    final_adjusted = np.empty(n)
    final_adjusted[sorted_indices] = adjusted
    
    return final_adjusted.tolist()

def calculate_false_positive_rate(
    heuristic_selections: List[int],
    baseline_selections: List[int]
) -> float:
    """
    Calculate the false positive rate during sensitivity analysis.
    
    A false positive is defined as a block selected by the heuristic
    that was NOT selected by the Dense Attention baseline.
    
    Args:
        heuristic_selections: List of block indices selected by the heuristic.
        baseline_selections: List of block indices selected by the Dense Attention baseline.
        
    Returns:
        False positive rate (float between 0 and 1).
    """
    if not heuristic_selections:
        return 0.0
    
    heuristic_set = set(heuristic_selections)
    baseline_set = set(baseline_selections)
    
    # False positives: Heuristic selected, Baseline did not
    false_positives = heuristic_set - baseline_set
    count_fp = len(false_positives)
    
    fp_rate = count_fp / len(heuristic_selections)
    return float(fp_rate)

def run_sensitivity_sweep(
    heuristic_name: str,
    threshold_values: List[float],
    heuristic_results_fn: callable,
    baseline_results_fn: callable
) -> List[Dict[str, Any]]:
    """
    Run a sensitivity sweep across a range of thresholds.
    
    Args:
        heuristic_name: Name of the heuristic being tested.
        threshold_values: List of threshold values to sweep.
        heuristic_results_fn: Function that takes (threshold) and returns (selections, accuracy).
        baseline_results_fn: Function that returns baseline selections.
        
    Returns:
        List of dictionaries containing sensitivity analysis results.
    """
    baseline_selections = baseline_results_fn()
    sensitivity_table = []
    
    for threshold in threshold_values:
        try:
            # Get heuristic selections and accuracy for this threshold
            heuristic_selections, accuracy = heuristic_results_fn(threshold)
            
            # Calculate false positive rate
            fp_rate = calculate_false_positive_rate(heuristic_selections, baseline_selections)
            
            sensitivity_table.append({
                "threshold": float(threshold),
                "accuracy": float(accuracy),
                "false_positive_rate": float(fp_rate)
            })
            
            logger.info(f"Heuristic {heuristic_name} at threshold {threshold}: "
                        f"Accuracy={accuracy:.4f}, FP Rate={fp_rate:.4f}")
            
        except Exception as e:
            logger.error(f"Error at threshold {threshold} for {heuristic_name}: {e}")
            sensitivity_table.append({
                "threshold": float(threshold),
                "accuracy": 0.0,
                "false_positive_rate": 0.0,
                "error": str(e)
            })
    
    return sensitivity_table

def generate_statistical_report(
    ttest_stat: float,
    ttest_p: float,
    wilcoxon_stat: float,
    wilcoxon_p: float,
    sensitivity_table: List[Dict[str, Any]],
    f1_score: float,
    false_positive_rate: float
) -> Dict[str, Any]:
    """
    Generate the final statistical report dictionary.
    
    Args:
        ttest_stat: T-test statistic.
        ttest_p: T-test p-value.
        wilcoxon_stat: Wilcoxon statistic.
        wilcoxon_p: Wilcoxon p-value.
        sensitivity_table: List of sensitivity analysis results.
        f1_score: Final F1 score.
        false_positive_rate: Final false positive rate.
        
    Returns:
        Dictionary containing the full report.
    """
    significance_statement = "p < 0.05" if ttest_p < 0.05 else "p >= 0.05"
    
    report = {
        "f1_score": float(f1_score),
        "p_value": float(ttest_p),
        "false_positive_rate": float(false_positive_rate),
        "sensitivity_table": sensitivity_table,
        "ttest_stat": float(ttest_stat),
        "wilcoxon_stat": float(wilcoxon_stat),
        "significance_statement": significance_statement
    }
    
    return report

def main():
    """
    Main entry point for testing statistical functions.
    """
    logger.info("Running statistical module self-test...")
    
    # Mock data for testing
    mock_heuristic = [0.8, 0.85, 0.75, 0.9, 0.82]
    mock_baseline = [0.82, 0.84, 0.78, 0.88, 0.80]
    
    t_stat, t_p = run_paired_ttest(mock_heuristic, mock_baseline)
    w_stat, w_p = run_wilcoxon_test(mock_heuristic, mock_baseline)
    
    logger.info(f"T-test: stat={t_stat:.4f}, p={t_p:.4f}")
    logger.info(f"Wilcoxon: stat={w_stat:.4f}, p={w_p:.4f}")
    
    # Test false positive rate
    h_sel = [1, 2, 3, 4, 5]
    b_sel = [2, 3, 4, 5, 6]
    fp_rate = calculate_false_positive_rate(h_sel, b_sel)
    logger.info(f"False Positive Rate: {fp_rate:.4f}")
    
    # Test sensitivity sweep
    def mock_heuristic_fn(th):
        # Mock: returns selections [1, 2, 3] and accuracy 0.85
        return [1, 2, 3], 0.85
    
    def mock_baseline_fn():
        return [2, 3, 4]
    
    sweep = run_sensitivity_sweep(
        "mock_heuristic",
        [0.01, 0.05, 0.1],
        mock_heuristic_fn,
        mock_baseline_fn
    )
    
    logger.info(f"Sensitivity sweep result: {sweep}")
    
    report = generate_statistical_report(
        t_stat, t_p, w_stat, w_p, sweep, 0.85, fp_rate
    )
    
    logger.info(f"Generated report: {json.dumps(report, indent=2)}")

if __name__ == "__main__":
    main()