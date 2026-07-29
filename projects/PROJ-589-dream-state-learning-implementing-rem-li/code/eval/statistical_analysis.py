"""
Statistical analysis module for Dream-State Learning project.

Implements comparative analysis between experimental (Dream-State) and baseline
models using Wilcoxon signed-rank test as per Plan Constitution Principle VII.
"""
from typing import List, Tuple, Dict, Any
import numpy as np
from scipy.stats import wilcoxon
from utils.logger import get_logger
import json
from pathlib import Path

logger = get_logger(__name__)


def compute_accuracy_difference(
    experimental_accuracies: List[float],
    baseline_accuracies: List[float]
) -> float:
    """
    Compute the mean accuracy difference between experimental and baseline models.
    
    Args:
        experimental_accuracies: List of accuracy floats from experimental runs (5 seeds)
        baseline_accuracies: List of accuracy floats from baseline runs (5 seeds)
    
    Returns:
        Mean difference (experimental - baseline)
    
    Raises:
        ValueError: If input lists are not of equal length or have fewer than 2 elements
    """
    if len(experimental_accuracies) != len(baseline_accuracies):
        raise ValueError(
            f"Accuracy lists must have equal length. "
            f"Got {len(experimental_accuracies)} and {len(baseline_accuracies)}"
        )
    
    if len(experimental_accuracies) < 2:
        raise ValueError(
            f"Need at least 2 accuracy values for statistical comparison. "
            f"Got {len(experimental_accuracies)}"
        )
    
    experimental_arr = np.array(experimental_accuracies)
    baseline_arr = np.array(baseline_accuracies)
    
    difference = np.mean(experimental_arr) - np.mean(baseline_arr)
    logger.info(
        f"Mean experimental accuracy: {np.mean(experimental_arr):.4f}, "
        f"Mean baseline accuracy: {np.mean(baseline_arr):.4f}, "
        f"Difference: {difference:.4f}"
    )
    
    return float(difference)


def run_wilcoxon_test(
    experimental_accuracies: List[float],
    baseline_accuracies: List[float],
    alpha: float = 0.05
) -> Tuple[float, float, bool]:
    """
    Perform Wilcoxon signed-rank test to compare experimental and baseline models.
    
    This test is appropriate for paired, non-normally distributed data and is
    mandated by Plan Constitution Principle VII due to potential unequal variance.
    
    Args:
        experimental_accuracies: List of accuracy floats from experimental runs (5 seeds)
        baseline_accuracies: List of accuracy floats from baseline runs (5 seeds)
        alpha: Significance level (default 0.05)
    
    Returns:
        Tuple of (statistic, p_value, is_significant)
        - statistic: Wilcoxon test statistic
        - p_value: Two-sided p-value from the test
        - is_significant: True if p_value < alpha
    
    Raises:
        ValueError: If input lists are invalid for statistical testing
    """
    if len(experimental_accuracies) != len(baseline_accuracies):
        raise ValueError(
            f"Accuracy lists must have equal length for paired test. "
            f"Got {len(experimental_accuracies)} and {len(baseline_accuracies)}"
        )
    
    if len(experimental_accuracies) < 2:
        raise ValueError(
            f"Wilcoxon test requires at least 2 paired observations. "
            f"Got {len(experimental_accuracies)}"
        )
    
    experimental_arr = np.array(experimental_accuracies)
    baseline_arr = np.array(baseline_accuracies)
    
    logger.info(
        f"Running Wilcoxon signed-rank test with alpha={alpha} on "
        f"{len(experimental_accuracies)} paired samples"
    )
    
    # Perform Wilcoxon signed-rank test
    statistic, p_value = wilcoxon(experimental_arr, baseline_arr)
    
    is_significant = p_value < alpha
    
    logger.info(
        f"Wilcoxon test results: statistic={statistic:.4f}, "
        f"p_value={p_value:.6f}, significant={is_significant}"
    )
    
    return float(statistic), float(p_value), is_significant


def analyze_model_performance(
    experimental_accuracies: List[float],
    baseline_accuracies: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Complete statistical analysis comparing experimental and baseline models.
    
    This function orchestrates the full analysis pipeline:
    1. Validates input data
    2. Computes accuracy differences
    3. Performs Wilcoxon signed-rank test
    4. Returns comprehensive results dictionary
    
    Args:
        experimental_accuracies: List of 5 accuracy floats from experimental runs
        baseline_accuracies: List of 5 accuracy floats from baseline runs
        alpha: Significance level (default 0.05)
    
    Returns:
        Dictionary containing:
        - experimental_mean: Mean accuracy of experimental model
        - baseline_mean: Mean accuracy of baseline model
        - accuracy_difference: Mean difference (experimental - baseline)
        - wilcoxon_statistic: Test statistic from Wilcoxon test
        - p_value: P-value from Wilcoxon test
        - is_significant: Whether the difference is statistically significant
        - alpha: Significance level used
        - n_samples: Number of paired samples
        - experimental_accuracies: Original experimental accuracies
        - baseline_accuracies: Original baseline accuracies
    """
    # Validate inputs
    if len(experimental_accuracies) != 5:
        logger.warning(
            f"Expected 5 experimental accuracies (one per seed), got {len(experimental_accuracies)}. "
            f"This may affect statistical power."
        )
    
    if len(baseline_accuracies) != 5:
        logger.warning(
            f"Expected 5 baseline accuracies (one per seed), got {len(baseline_accuracies)}. "
            f"This may affect statistical power."
        )
    
    # Compute statistics
    experimental_arr = np.array(experimental_accuracies)
    baseline_arr = np.array(baseline_accuracies)
    
    experimental_mean = float(np.mean(experimental_arr))
    baseline_mean = float(np.mean(baseline_arr))
    accuracy_difference = compute_accuracy_difference(experimental_accuracies, baseline_accuracies)
    
    # Run Wilcoxon test
    statistic, p_value, is_significant = run_wilcoxon_test(
        experimental_accuracies, baseline_accuracies, alpha
    )
    
    results = {
        "experimental_mean": experimental_mean,
        "baseline_mean": baseline_mean,
        "accuracy_difference": accuracy_difference,
        "wilcoxon_statistic": statistic,
        "p_value": p_value,
        "is_significant": is_significant,
        "alpha": alpha,
        "n_samples": len(experimental_accuracies),
        "experimental_accuracies": experimental_accuracies,
        "baseline_accuracies": baseline_accuracies,
        "interpretation": (
            f"{'Statistically significant' if is_significant else 'Not statistically significant'} "
            f"difference at α={alpha} level. "
            f"Experimental model {'outperforms' if accuracy_difference > 0 else 'underperforms'} "
            f"baseline by {abs(accuracy_difference)*100:.2f}% accuracy points."
        )
    }
    
    logger.info(f"Analysis complete: {results['interpretation']}")
    
    return results


def save_analysis_report(
    results: Dict[str, Any],
    output_path: str = "data/results/statistical_analysis.json"
) -> Path:
    """
    Save statistical analysis results to a JSON file.
    
    Args:
        results: Dictionary from analyze_model_performance()
        output_path: Path to save the JSON report
    
    Returns:
        Path object of the saved file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis report saved to {output_file}")
    return output_file


def load_accuracy_results(
    experimental_path: str,
    baseline_path: str
) -> Tuple[List[float], List[float]]:
    """
    Load accuracy results from JSON files generated by training runs.
    
    Args:
        experimental_path: Path to JSON file with experimental accuracies
        baseline_path: Path to JSON file with baseline accuracies
    
    Returns:
        Tuple of (experimental_accuracies, baseline_accuracies)
    
    Raises:
        FileNotFoundError: If the specified files don't exist
        ValueError: If the files don't contain valid accuracy data
    """
    def load_from_json(path: str) -> List[float]:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'accuracies' not in data:
            raise ValueError(f"No 'accuracies' key found in {path}")
        
        accuracies = data['accuracies']
        
        if not all(isinstance(x, (int, float)) for x in accuracies):
            raise ValueError(f"All accuracies must be numeric in {path}")
        
        return [float(x) for x in accuracies]
    
    experimental = load_from_json(experimental_path)
    baseline = load_from_json(baseline_path)
    
    logger.info(
        f"Loaded {len(experimental)} experimental and {len(baseline)} baseline accuracies"
    )
    
    return experimental, baseline