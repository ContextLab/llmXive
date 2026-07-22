import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from scipy import stats
import warnings

from config import get_config
from utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class StatisticalTestResult:
    test_name: str
    statistic: float
    p_value: float
    significant: bool
    effect_size: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    sample_size: int = 0

@dataclass
class StatisticalReport:
    description: str
    tests: List[StatisticalTestResult] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    sensitivity_results: Optional[List[Dict[str, float]]] = None
    invalid_seeds_excluded: List[str] = field(default_factory=list)

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], float]:
    """Apply Bonferroni correction to a list of p-values."""
    n = len(p_values)
    if n == 0:
        return [], alpha
    corrected_alpha = alpha / n
    significant = [p < corrected_alpha for p in p_values]
    return significant, corrected_alpha

def run_paired_ttest(group1: np.ndarray, group2: np.ndarray) -> StatisticalTestResult:
    """Perform a paired t-test between two groups."""
    if len(group1) != len(group2):
        raise ValueError("Group sizes must match for paired t-test")
    if len(group1) < 2:
        raise ValueError("Need at least 2 samples for t-test")

    t_stat, p_val = stats.ttest_rel(group1, group2)
    significant = p_val < 0.05

    # Calculate effect size (Cohen's d for paired samples)
    diff = group1 - group2
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    if std_diff == 0:
        cohens_d = 0.0
    else:
        cohens_d = mean_diff / std_diff

    # Confidence interval for mean difference
    ci_low, ci_high = calculate_confidence_interval(diff, confidence=0.95)

    return StatisticalTestResult(
        test_name="paired_ttest",
        statistic=float(t_stat),
        p_value=float(p_val),
        significant=significant,
        effect_size=float(cohens_d),
        confidence_interval=(float(ci_low), float(ci_high)),
        sample_size=len(group1)
    )

def calculate_cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Calculate Cohen's d effect size for independent groups."""
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return (mean1 - mean2) / pooled_std

def calculate_confidence_interval(data: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate confidence interval for a sample."""
    n = len(data)
    if n < 2:
        return (float(np.mean(data)), float(np.mean(data)))
    mean = np.mean(data)
    std_err = stats.sem(data)
    h = std_err * stats.t.ppf((1 + confidence) / 2.0, n - 1)
    return (mean - h, mean + h)

def calculate_percentage_difference(group1: np.ndarray, group2: np.ndarray) -> float:
    """Calculate percentage difference between two groups."""
    mean1, mean2 = np.mean(group1), np.mean(group2)
    if mean2 == 0:
        return 0.0
    return ((mean1 - mean2) / mean2) * 100.0

def load_evaluation_results_from_json(directory: str) -> List[Dict[str, Any]]:
    """Load evaluation results from JSON files in a directory."""
    results = []
    if not os.path.exists(directory):
        logger.warning(f"Directory {directory} does not exist")
        return results

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    # Include filename for tracking
                    data['_source_file'] = filename
                    results.append(data)
            except Exception as e:
                logger.error(f"Error loading {filepath}: {e}")
    return results

def _is_seed_converged(evaluation_result: Dict[str, Any]) -> bool:
    """
    Determine if a seed's evaluation result indicates convergence.
    
    A seed is considered 'non-converged' if:
    1. The confidence loss metric is missing.
    2. The confidence loss is NaN or Inf.
    3. The confidence loss is extremely high (indicating failure to learn).
    
    We use a heuristic threshold based on typical cross-entropy scales.
    If confidence_loss > 10.0, we consider it non-converged.
    """
    metrics = evaluation_result.get('metrics', {})
    confidence_loss = metrics.get('confidence_loss')
    
    if confidence_loss is None:
        logger.warning(f"Seed {evaluation_result.get('seed', 'unknown')}: confidence_loss missing. Marking as non-converged.")
        return False
    
    if not isinstance(confidence_loss, (int, float)):
        logger.warning(f"Seed {evaluation_result.get('seed', 'unknown')}: confidence_loss is not numeric. Marking as non-converged.")
        return False
        
    if np.isnan(confidence_loss) or np.isinf(confidence_loss):
        logger.warning(f"Seed {evaluation_result.get('seed', 'unknown')}: confidence_loss is NaN or Inf. Marking as non-converged.")
        return False
        
    # Heuristic threshold: if loss is > 10, it likely failed to converge
    # (Cross entropy on typical tasks usually < 5 for converged models)
    if confidence_loss > 10.0:
        logger.warning(f"Seed {evaluation_result.get('seed', 'unknown')}: confidence_loss ({confidence_loss}) > 10.0. Marking as non-converged.")
        return False
        
    return True

def filter_converged_seeds(evaluation_results: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Filter out seeds that did not converge based on confidence loss.
    
    Returns:
        Tuple of (valid_results, list_of_excluded_seed_names)
    """
    valid_results = []
    excluded_seeds = []
    
    for result in evaluation_results:
        seed_name = result.get('seed', 'unknown')
        if _is_seed_converged(result):
            valid_results.append(result)
        else:
            excluded_seeds.append(str(seed_name))
            
    if excluded_seeds:
        logger.info(f"Excluding {len(excluded_seeds)} non-converged seeds: {excluded_seeds}")
    else:
        logger.info("All seeds passed convergence check.")
        
    return valid_results, excluded_seeds

def run_sensitivity_analysis(evaluation_results: List[Dict[str, Any]], thresholds: List[float] = [0.4, 0.5, 0.6]) -> List[Dict[str, float]]:
    """
    Run sensitivity analysis across different confidence thresholds.
    
    Args:
        evaluation_results: List of evaluation result dictionaries.
        thresholds: List of confidence thresholds to test.
        
    Returns:
        List of dictionaries containing threshold, FPR, FNR.
    """
    results = []
    
    # Aggregate all predictions and labels
    all_predictions = []
    all_labels = []
    
    for res in evaluation_results:
        metrics = res.get('metrics', {})
        # Assuming we have 'predictions' and 'labels' in the raw data or derived metrics
        # If stored differently, adjust extraction logic
        preds = metrics.get('predictions', [])
        labels = metrics.get('labels', [])
        
        if preds and labels:
            all_predictions.extend(preds)
            all_labels.extend(labels)
    
    if not all_predictions or not all_labels:
        logger.warning("No prediction/label data found for sensitivity analysis.")
        return results
        
    all_predictions = np.array(all_predictions)
    all_labels = np.array(all_labels)
    
    for thresh in thresholds:
        # Binary classification based on threshold
        binary_preds = (all_predictions >= thresh).astype(int)
        
        # Calculate FPR and FNR
        # True Positives, False Positives, True Negatives, False Negatives
        tp = np.sum((binary_preds == 1) & (all_labels == 1))
        fp = np.sum((binary_preds == 1) & (all_labels == 0))
        tn = np.sum((binary_preds == 0) & (all_labels == 0))
        fn = np.sum((binary_preds == 0) & (all_labels == 1))
        
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        results.append({
            'threshold': float(thresh),
            'false_positive_rate': float(fpr),
            'false_negative_rate': float(fnr)
        })
        
    return results

def save_sensitivity_analysis_csv(results: List[Dict[str, float]], output_path: str):
    """Save sensitivity analysis results to CSV."""
    import csv
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        if not results:
            f.write("threshold,false_positive_rate,false_negative_rate\n")
            return
            
        writer = csv.DictWriter(f, fieldnames=['threshold', 'false_positive_rate', 'false_negative_rate'])
        writer.writeheader()
        writer.writerows(results)
        
    logger.info(f"Sensitivity analysis saved to {output_path}")

def generate_statistical_report(
    baseline_scores: List[float], 
    recursive_scores: List[float],
    excluded_seeds: List[str],
    sensitivity_results: Optional[List[Dict[str, float]]] = None,
    description: str = "Statistical comparison of recursive vs baseline models"
) -> StatisticalReport:
    """
    Generate a comprehensive statistical report.
    
    Args:
        baseline_scores: List of metric scores for baseline model.
        recursive_scores: List of metric scores for recursive model.
        excluded_seeds: List of seed identifiers that were excluded.
        sensitivity_results: Optional sensitivity analysis results.
        description: Description of the report.
        
    Returns:
        StatisticalReport object.
    """
    if len(baseline_scores) != len(recursive_scores):
        raise ValueError("Baseline and recursive score lists must have the same length")
    
    if len(baseline_scores) < 2:
        raise ValueError("Need at least 2 samples for statistical comparison")
        
    baseline_arr = np.array(baseline_scores)
    recursive_arr = np.array(recursive_scores)
    
    # Run paired t-test
    ttest_result = run_paired_ttest(baseline_arr, recursive_arr)
    
    # Calculate percentage difference
    pct_diff = calculate_percentage_difference(recursive_arr, baseline_arr)
    
    # Build summary
    summary = {
        'baseline_mean': float(np.mean(baseline_arr)),
        'baseline_std': float(np.std(baseline_arr, ddof=1)),
        'recursive_mean': float(np.mean(recursive_arr)),
        'recursive_std': float(np.std(recursive_arr, ddof=1)),
        'percentage_difference': float(pct_diff),
        'seeds_excluded_count': len(excluded_seeds),
        'seeds_excluded': excluded_seeds
    }
    
    report = StatisticalReport(
        description=description,
        tests=[ttest_result],
        summary=summary,
        sensitivity_results=sensitivity_results,
        invalid_seeds_excluded=excluded_seeds
    )
    
    return report

def main():
    """Main entry point for statistical analysis."""
    config = get_config()
    results_dir = config.get('results_dir', 'artifacts/results')
    output_path = os.path.join(results_dir, 'statistical_report.json')
    
    logger.info(f"Loading evaluation results from {results_dir}")
    all_results = load_evaluation_results_from_json(results_dir)
    
    if not all_results:
        logger.error("No evaluation results found. Exiting.")
        return
        
    # Filter out non-converged seeds (T027 implementation)
    valid_results, excluded_seeds = filter_converged_seeds(all_results)
    
    if len(valid_results) < 2:
        logger.error(f"Insufficient valid results after filtering ({len(valid_results)}). Need at least 2.")
        logger.error(f"Excluded seeds: {excluded_seeds}")
        return

    # Separate by model type (assuming 'model_type' field exists in results)
    # If the structure is different, adjust accordingly
    baseline_scores = []
    recursive_scores = []
    
    for res in valid_results:
        model_type = res.get('model_type', 'unknown')
        # Assuming 'self_consistency' is the primary metric
        metric_val = res.get('metrics', {}).get('self_consistency')
        
        if metric_val is None:
            logger.warning(f"Skipping result without self_consistency metric: {res.get('_source_file')}")
            continue
            
        if model_type == 'baseline':
            baseline_scores.append(metric_val)
        elif model_type == 'recursive':
            recursive_scores.append(metric_val)
        else:
            logger.warning(f"Unknown model type: {model_type}")
            
    if len(baseline_scores) < 2 or len(recursive_scores) < 2:
        logger.error("Need at least 2 valid seeds for both baseline and recursive models.")
        logger.error(f"Baseline count: {len(baseline_scores)}, Recursive count: {len(recursive_scores)}")
        return
        
    # Run sensitivity analysis
    sensitivity_results = run_sensitivity_analysis(valid_results)
    save_sensitivity_analysis_csv(sensitivity_results, os.path.join(results_dir, 'sensitivity_analysis.csv'))
    
    # Generate report
    report = generate_statistical_report(
        baseline_scores=baseline_scores,
        recursive_scores=recursive_scores,
        excluded_seeds=excluded_seeds,
        sensitivity_results=sensitivity_results
    )
    
    # Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            'description': report.description,
            'tests': [
                {
                    'test_name': t.test_name,
                    'statistic': t.statistic,
                    'p_value': t.p_value,
                    'significant': t.significant,
                    'effect_size': t.effect_size,
                    'confidence_interval': t.confidence_interval,
                    'sample_size': t.sample_size
                } for t in report.tests
            ],
            'summary': report.summary,
            'sensitivity_results': report.sensitivity_results,
            'invalid_seeds_excluded': report.invalid_seeds_excluded
        }, f, indent=2)
        
    logger.info(f"Statistical report saved to {output_path}")
    logger.info(f"Excluded {len(excluded_seeds)} non-converged seeds: {excluded_seeds}")

if __name__ == '__main__':
    main()