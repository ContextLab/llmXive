import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from scipy import stats
import csv
from pathlib import Path

# Imports from existing project structure
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class StatisticalTestResult:
    test_name: str
    statistic: float
    p_value: float
    significant: bool
    effect_size: Optional[float] = None

@dataclass
class StatisticalReport:
    tests: List[StatisticalTestResult] = field(default_factory=list)
    percentage_difference: Optional[float] = None
    sensitivity_results: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

def load_evaluation_results_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Load evaluation results from a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Evaluation results file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Handle both single result and list of results
    if isinstance(data, dict):
        return [data]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected data format in {file_path}")

def filter_converged_seeds(results: List[Dict[str, Any]], threshold: float = 0.01) -> List[Dict[str, Any]]:
    """Filter out seeds that did not converge (confidence loss > threshold)."""
    converged = []
    for result in results:
        confidence_loss = result.get('confidence_loss', 1.0)
        if confidence_loss <= threshold:
            converged.append(result)
        else:
            logger.debug(f"Seed {result.get('seed', 'unknown')} excluded: confidence_loss={confidence_loss}")
    return converged

def calculate_percentage_difference(recursive_metrics: List[float], baseline_metrics: List[float]) -> float:
    """Calculate percentage difference between recursive and baseline metrics."""
    if not recursive_metrics or not baseline_metrics:
        return 0.0
    
    avg_recursive = np.mean(recursive_metrics)
    avg_baseline = np.mean(baseline_metrics)
    
    if avg_baseline == 0:
        return 0.0
    
    return ((avg_recursive - avg_baseline) / avg_baseline) * 100

def run_paired_ttest(recursive_values: List[float], baseline_values: List[float]) -> StatisticalTestResult:
    """Perform paired t-test between recursive and baseline models."""
    if len(recursive_values) != len(baseline_values) or len(recursive_values) == 0:
        raise ValueError("Input lists must be of equal non-zero length")
    
    statistic, p_value = stats.ttest_rel(recursive_values, baseline_values)
    significant = p_value < 0.05
    
    return StatisticalTestResult(
        test_name="paired_ttest",
        statistic=statistic,
        p_value=p_value,
        significant=significant
    )

def calculate_cohen_d(group1: List[float], group2: List[float]) -> float:
    """Calculate Cohen's d effect size."""
    if not group1 or not group2:
        return 0.0
    
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)
    
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def calculate_confidence_interval(data: List[float], confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate confidence interval for a dataset."""
    if not data:
        return (0.0, 0.0)
    
    n = len(data)
    mean = np.mean(data)
    std_err = stats.sem(data)
    h = std_err * stats.t.ppf((1 + confidence) / 2., n - 1)
    
    return (mean - h, mean + h)

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[Tuple[float, bool]]:
    """Apply Bonferroni correction to multiple p-values."""
    n = len(p_values)
    if n == 0:
        return []
    
    corrected_alpha = alpha / n
    results = []
    
    for p in p_values:
        significant = p < corrected_alpha
        results.append((p, significant))
    
    return results

def generate_statistical_report(
    recursive_results: List[Dict[str, Any]],
    baseline_results: List[Dict[str, Any]],
    metric_name: str = "self_consistency"
) -> StatisticalReport:
    """Generate a comprehensive statistical report."""
    # Filter converged seeds
    recursive_converged = filter_converged_seeds(recursive_results)
    baseline_converged = filter_converged_seeds(baseline_results)
    
    if not recursive_converged or not baseline_converged:
        logger.warning("Insufficient converged seeds for statistical analysis")
        return StatisticalReport()
    
    # Extract metric values
    recursive_values = [r.get(metric_name, 0.0) for r in recursive_converged]
    baseline_values = [r.get(metric_name, 0.0) for r in baseline_converged]
    
    # Perform statistical tests
    ttest_result = run_paired_ttest(recursive_values, baseline_values)
    cohens_d = calculate_cohen_d(recursive_values, baseline_values)
    ci = calculate_confidence_interval(recursive_values)
    
    # Update ttest result with effect size
    ttest_result.effect_size = cohens_d
    
    # Calculate percentage difference
    pct_diff = calculate_percentage_difference(recursive_values, baseline_values)
    
    return StatisticalReport(
        tests=[ttest_result],
        percentage_difference=pct_diff,
        metadata={
            "metric_name": metric_name,
            "recursive_n": len(recursive_values),
            "baseline_n": len(baseline_values),
            "confidence_interval": ci,
            "cohens_d": cohens_d
        }
    )

def save_statistical_report(report: StatisticalReport, output_path: str) -> None:
    """Save statistical report to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    report_dict = {
        "tests": [
            {
                "test_name": t.test_name,
                "statistic": t.statistic,
                "p_value": t.p_value,
                "significant": t.significant,
                "effect_size": t.effect_size
            }
            for t in report.tests
        ],
        "percentage_difference": report.percentage_difference,
        "sensitivity_results": report.sensitivity_results,
        "metadata": report.metadata
    }
    
    with open(output_path, 'w') as f:
        json.dump(report_dict, f, indent=2)

def run_sensitivity_analysis(
    evaluation_results: List[Dict[str, Any]],
    thresholds: List[float] = [0.4, 0.5, 0.6],
    output_path: str = "artifacts/results/sensitivity_analysis.csv"
) -> None:
    """
    Perform sensitivity analysis for confidence thresholds.
    
    Computes false positive rate and false negative rate for each threshold
    based on the model's confidence predictions and actual correctness.
    
    Args:
        evaluation_results: List of evaluation result dictionaries containing
                            'confidence' and 'is_correct' fields.
        thresholds: List of confidence thresholds to sweep.
        output_path: Path to save the CSV output.
    """
    logger.info(f"Starting sensitivity analysis with thresholds: {thresholds}")
    
    if not evaluation_results:
        logger.warning("No evaluation results provided for sensitivity analysis")
        # Create empty CSV with headers
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['threshold', 'false_positive_rate', 'false_negative_rate'])
        return
    
    results = []
    
    for threshold in thresholds:
        # Classify predictions based on threshold
        # True Positive: confidence >= threshold AND is_correct
        # False Positive: confidence >= threshold AND NOT is_correct
        # True Negative: confidence < threshold AND NOT is_correct
        # False Negative: confidence < threshold AND is_correct
        
        tp, fp, tn, fn = 0, 0, 0, 0
        
        for result in evaluation_results:
            confidence = result.get('confidence', 0.0)
            is_correct = result.get('is_correct', False)
            
            if confidence >= threshold:
                if is_correct:
                    tp += 1
                else:
                    fp += 1
            else:
                if is_correct:
                    fn += 1
                else:
                    tn += 1
        
        # Calculate rates
        # False Positive Rate = FP / (FP + TN)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        
        # False Negative Rate = FN / (FN + TP)
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        results.append({
            'threshold': threshold,
            'false_positive_rate': fpr,
            'false_negative_rate': fnr,
            'tp': tp,
            'fp': fp,
            'tn': tn,
            'fn': fn
        })
        
        logger.debug(f"Threshold {threshold}: FP={fp}, FN={fn}, FPR={fpr:.4f}, FNR={fnr:.4f}")
    
    # Write to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['threshold', 'false_positive_rate', 'false_negative_rate'])
        
        for res in results:
            writer.writerow([
                res['threshold'],
                f"{res['false_positive_rate']:.6f}",
                f"{res['false_negative_rate']:.6f}"
            ])
    
    logger.info(f"Sensitivity analysis complete. Results saved to {output_path}")

def main():
    """Main entry point for statistical analysis module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Statistical Analysis for Consciousness Bootstrapping")
    parser.add_argument("--input", type=str, help="Path to evaluation results JSON")
    parser.add_argument("--output-report", type=str, default="artifacts/results/statistical_report.json",
                      help="Path for statistical report output")
    parser.add_argument("--output-sensitivity", type=str, default="artifacts/results/sensitivity_analysis.csv",
                      help="Path for sensitivity analysis CSV output")
    parser.add_argument("--thresholds", type=str, default="0.4,0.5,0.6",
                      help="Comma-separated list of confidence thresholds")
    
    args = parser.parse_args()
    
    if not args.input:
        logger.error("Input file path is required")
        parser.print_help()
        return
    
    # Load evaluation results
    try:
        results = load_evaluation_results_from_json(args.input)
        logger.info(f"Loaded {len(results)} evaluation results")
    except Exception as e:
        logger.error(f"Failed to load evaluation results: {e}")
        return
    
    # Parse thresholds
    thresholds = [float(t.strip()) for t in args.thresholds.split(',')]
    
    # Run sensitivity analysis
    run_sensitivity_analysis(
        evaluation_results=results,
        thresholds=thresholds,
        output_path=args.output_sensitivity
    )
    
    # Generate statistical report (example with self_consistency metric)
    # Note: In a real scenario, we would have separate recursive and baseline results
    # For now, we demonstrate the structure
    report = generate_statistical_report(results, results, "self_consistency")
    report.sensitivity_results = {
        "thresholds": thresholds,
        "output_file": args.output_sensitivity
    }
    
    save_statistical_report(report, args.output_report)
    
    logger.info("Statistical analysis complete")

if __name__ == "__main__":
    main()
