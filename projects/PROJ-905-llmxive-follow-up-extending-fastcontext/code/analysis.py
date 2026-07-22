import math
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from scipy import stats
from scipy.stats import ttest_rel, shapiro, wilcoxon

def run_ttest(
    lite_metrics: List[float],
    baseline_metrics: List[float],
    alpha: float = 0.05,
    power_threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Perform power analysis and select between paired t-test and Wilcoxon signed-rank test.
    
    1. Check normality of differences using Shapiro-Wilk test.
    2. If p < 0.05 (non-normal) OR sample size < 30, use Wilcoxon signed-rank test.
    3. Otherwise, use paired t-test.
    4. Perform power analysis (approximate) to ensure sufficient sample size.
    
    Args:
        lite_metrics: List of performance metrics from the Lite model.
        baseline_metrics: List of performance metrics from the Baseline model.
        alpha: Significance level for normality and hypothesis tests.
        power_threshold: Target statistical power (default 0.8).
        
    Returns:
        Dictionary containing:
            - 'test_type': 'ttest' or 'wilcoxon'
            - 'statistic': test statistic value
            - 'p_value': p-value from the test
            - 'is_significant': True if p < alpha
            - 'normality_p': p-value from Shapiro-Wilk test
            - 'sample_size': number of pairs
    """
    if len(lite_metrics) != len(baseline_metrics):
        raise ValueError("lite_metrics and baseline_metrics must have the same length")
    
    n = len(lite_metrics)
    if n < 2:
        raise ValueError("At least 2 paired observations are required for statistical testing")
    
    # Calculate differences
    differences = np.array(baseline_metrics) - np.array(lite_metrics)
    
    # 1. Normality check using Shapiro-Wilk
    normality_stat, normality_p = shapiro(differences)
    
    # 2. Select test based on normality and sample size
    # If non-normal (p < 0.05) or small sample (n < 30), use Wilcoxon
    use_wilcoxon = (normality_p < alpha) or (n < 30)
    
    if use_wilcoxon:
        test_type = "wilcoxon"
        stat, p_value = wilcoxon(baseline_metrics, lite_metrics)
    else:
        test_type = "ttest"
        stat, p_value = ttest_rel(baseline_metrics, lite_metrics)
    
    # 3. Power analysis (approximate for paired tests)
    # Calculate effect size (Cohen's d for paired samples)
    mean_diff = np.mean(differences)
    std_diff = np.std(differences, ddof=1)
    if std_diff == 0:
        cohens_d = 0.0
    else:
        cohens_d = mean_diff / std_diff
    
    # Approximate power calculation for paired t-test
    # Using the non-central t-distribution approximation
    if n > 1 and cohens_d != 0:
        # Effect size for power calculation
        effect_size = abs(cohens_d)
        # Approximate power using standard normal approximation
        # This is a simplified estimate; for rigorous power analysis, use statsmodels
        try:
            from statsmodels.stats.power import TTestPower
            power_analysis = TTestPower()
            calculated_power = power_analysis.solve_power(
                effect_size=effect_size,
                nobs1=n,
                alpha=alpha,
                alternative='two-sided'
            )
        except ImportError:
            # Fallback: simple approximation if statsmodels not available
            # Power increases with effect size and sample size
            calculated_power = min(1.0, (effect_size * math.sqrt(n)) / 2.0)
    else:
        calculated_power = 0.0
    
    return {
        'test_type': test_type,
        'statistic': float(stat),
        'p_value': float(p_value),
        'is_significant': bool(p_value < alpha),
        'normality_p': float(normality_p),
        'sample_size': n,
        'effect_size': float(cohens_d),
        'power': float(calculated_power),
        'power_threshold_met': calculated_power >= power_threshold
    }

def calc_degradation(baseline_value: float, lite_value: float) -> float:
    """
    Calculate performance degradation percentage.
    
    Degradation = ((Baseline - Lite) / Baseline) * 100
    Positive value indicates Lite performed worse (degradation).
    Negative value indicates Lite performed better (improvement).
    
    Args:
        baseline_value: Metric value from the baseline model.
        lite_value: Metric value from the Lite model.
        
    Returns:
        Float representing percentage degradation.
    """
    if baseline_value == 0:
        return 0.0 if lite_value == 0 else float('inf')
    
    return ((baseline_value - lite_value) / baseline_value) * 100.0

def find_threshold(
    scores: List[float],
    metrics: List[float],
    target_degradation: float = 5.0
) -> float:
    """
    Perform sensitivity analysis to find the regularity score threshold
    where performance degradation exceeds a target value.
    
    Args:
        scores: List of regularity scores.
        metrics: List of performance metrics (e.g., degradation percentages).
        target_degradation: Target degradation percentage to identify threshold.
        
    Returns:
        Float representing the threshold score.
    """
    if len(scores) != len(metrics) or len(scores) == 0:
        raise ValueError("Scores and metrics must be non-empty lists of equal length")
    
    # Sort by score
    sorted_pairs = sorted(zip(scores, metrics), key=lambda x: x[0])
    sorted_scores = [p[0] for p in sorted_pairs]
    sorted_metrics = [p[1] for p in sorted_pairs]
    
    # Find the first score where degradation exceeds target
    threshold = None
    for score, metric in zip(sorted_scores, sorted_metrics):
        if metric > target_degradation:
            threshold = score
            break
    
    # If no threshold found, return the max score or a default
    if threshold is None:
        threshold = max(sorted_scores) if sorted_scores else 0.0
    
    return float(threshold)

def calculate_effect_size(
    group1: List[float],
    group2: List[float]
) -> Dict[str, float]:
    """
    Calculate Cohen's d effect size for two groups.
    
    Args:
        group1: First group of values.
        group2: Second group of values.
        
    Returns:
        Dictionary with 'cohen_d' and 'interpretation'.
    """
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        return {'cohen_d': 0.0, 'interpretation': 'undefined'}
    
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        cohens_d = 0.0
    else:
        cohens_d = (mean1 - mean2) / pooled_std
    
    # Interpretation
    abs_d = abs(cohens_d)
    if abs_d < 0.2:
        interpretation = 'negligible'
    elif abs_d < 0.5:
        interpretation = 'small'
    elif abs_d < 0.8:
        interpretation = 'medium'
    else:
        interpretation = 'large'
    
    return {
        'cohen_d': float(cohens_d),
        'interpretation': interpretation
    }

def generate_statistical_summary(
    lite_metrics: List[float],
    baseline_metrics: List[float],
    regularity_scores: Optional[List[float]] = None,
    alpha: float = 0.05,
    power_threshold: float = 0.8,
    target_degradation: float = 5.0
) -> Dict[str, Any]:
    """
    Generate a comprehensive statistical summary including:
    - P-value from appropriate test (t-test or Wilcoxon)
    - Effect size (Cohen's d)
    - Performance degradation percentage
    - Boundary threshold for regularity score
    - Regression analysis (slope and R-squared)
    
    Args:
        lite_metrics: List of Lite model metrics.
        baseline_metrics: List of Baseline model metrics.
        regularity_scores: Optional list of regularity scores for regression analysis.
        alpha: Significance level.
        power_threshold: Target statistical power.
        target_degradation: Target degradation for threshold detection.
        
    Returns:
        Dictionary with statistical summary matching the required schema.
    """
    # Ensure equal lengths
    if len(lite_metrics) != len(baseline_metrics):
        raise ValueError("lite_metrics and baseline_metrics must have equal length")
    
    # 1. Run the appropriate statistical test
    test_result = run_ttest(lite_metrics, baseline_metrics, alpha, power_threshold)
    
    # 2. Calculate effect size
    effect_size_result = calculate_effect_size(baseline_metrics, lite_metrics)
    
    # 3. Calculate degradation percentage (mean of individual degradations)
    degradations = [
        calc_degradation(b, l) 
        for b, l in zip(baseline_metrics, lite_metrics)
    ]
    mean_degradation = float(np.mean(degradations))
    
    # 4. Boundary threshold detection
    if regularity_scores is not None and len(regularity_scores) == len(lite_metrics):
        threshold = find_threshold(regularity_scores, degradations, target_degradation)
        
        # 5. Regression analysis: regularity_score vs performance delta
        # Performance delta = baseline - lite (positive means baseline is better)
        deltas = [b - l for b, l in zip(baseline_metrics, lite_metrics)]
        
        # Linear regression
        slope, intercept, r_value, p_val, std_err = stats.linregress(
            regularity_scores, deltas
        )
        r_squared = float(r_value ** 2)
        slope_val = float(slope)
    else:
        # If no regularity scores, set defaults
        threshold = 0.0
        slope_val = 0.0
        r_squared = 0.0
    
    return {
        'p_value': float(test_result['p_value']),
        'effect_size': {
            'cohen_d': float(effect_size_result['cohen_d'])
        },
        'degradation_percent': float(mean_degradation),
        'boundary_threshold': float(threshold),
        'regression_slope': float(slope_val),
        'r_squared': float(r_squared),
        'test_type': test_result['test_type'],
        'normality_p': float(test_result['normality_p']),
        'power': float(test_result['power']),
        'sample_size': int(test_result['sample_size'])
    }

# Main entry point for testing
if __name__ == "__main__":
    # Example usage with mock data
    mock_lite = [0.85, 0.82, 0.88, 0.79, 0.81, 0.84, 0.86, 0.83, 0.80, 0.87]
    mock_baseline = [0.90, 0.89, 0.91, 0.88, 0.87, 0.90, 0.92, 0.89, 0.88, 0.91]
    mock_scores = [0.95, 0.92, 0.98, 0.85, 0.78, 0.94, 0.96, 0.91, 0.82, 0.93]
    
    summary = generate_statistical_summary(
        lite_metrics=mock_lite,
        baseline_metrics=mock_baseline,
        regularity_scores=mock_scores,
        alpha=0.05,
        power_threshold=0.8,
        target_degradation=5.0
    )
    
    import json
    print(json.dumps(summary, indent=2))