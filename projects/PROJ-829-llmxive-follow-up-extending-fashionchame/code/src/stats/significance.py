"""
Statistical significance analysis module for the llmXive pipeline.
Implements ANOVA and Bonferroni correction as mandated by FR-005.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from scipy import stats
import numpy as np


# Constants for GarmentFeatureClass validation
VALID_FEATURE_CLASSES = {"Color", "Pattern", "Texture"}


def check_sample_sizes(scores_by_class: Dict[str, List[float]]) -> Dict[str, int]:
    """
    Check and return sample sizes for each class.
    """
    return {cls: len(scores) for cls, scores in scores_by_class.items()}


def has_low_sample_count(scores_by_class: Dict[str, List[float]], threshold: int = 10) -> bool:
    """
    Check if any class has fewer samples than the threshold.
    Returns True if any class is below the threshold.
    """
    for cls, scores in scores_by_class.items():
        if len(scores) < threshold:
            return True
    return False


def validate_stratification(scores_by_class: Dict[str, List[float]]) -> None:
    """
    Explicitly validate that input data is stratified by GarmentFeatureClass.
    Raises ValueError if:
    1. No classes found
    2. Unknown classes found (not in Color, Pattern, Texture)
    3. Missing any of the required classes
    """
    if not scores_by_class:
        raise ValueError("Input data is empty. No stratified classes found.")

    found_classes = set(scores_by_class.keys())

    # Check for unknown classes
    unknown_classes = found_classes - VALID_FEATURE_CLASSES
    if unknown_classes:
        raise ValueError(
            f"Unknown GarmentFeatureClass found in input: {unknown_classes}. "
            f"Valid classes are: {VALID_FEATURE_CLASSES}"
        )

    # Check for missing required classes
    missing_classes = VALID_FEATURE_CLASSES - found_classes
    if missing_classes:
        raise ValueError(
            f"Missing required GarmentFeatureClass in input: {missing_classes}. "
            f"Data must be stratified by {VALID_FEATURE_CLASSES}."
        )


def perform_anova(scores_by_class: Dict[str, List[float]]) -> Tuple[float, float]:
    """
    Perform One-Way ANOVA on fidelity scores across feature classes.
    Returns (F-statistic, p-value).
    Raises ValueError if stratification is invalid or sample sizes are insufficient.
    """
    # Validate stratification first
    validate_stratification(scores_by_class)

    # Extract arrays for ANOVA
    class_groups = [np.array(scores) for scores in scores_by_class.values()]

    # Check for minimum sample size per group for ANOVA validity
    # ANOVA requires at least 2 samples per group to calculate variance
    for i, group in enumerate(class_groups):
        if len(group) < 2:
            class_name = list(scores_by_class.keys())[i]
            raise ValueError(
                f"Insufficient samples for ANOVA in class '{class_name}'. "
                f"Requires at least 2 samples, got {len(group)}."
            )

    # Perform One-Way ANOVA
    f_stat, p_value = stats.f_oneway(*class_groups)

    return float(f_stat), float(p_value)


def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to p-values for multiple hypothesis testing.
    This is required for pairwise comparisons.
    
    Args:
        p_values: List of raw p-values from pairwise comparisons
        alpha: Significance level (default 0.05)
    
    Returns:
        Dictionary containing corrected p-values and significance decisions
    """
    if not p_values:
        return {
            "corrected_p_values": [],
            "significance_decisions": [],
            "alpha_adjusted": alpha,
            "num_tests": 0
        }

    num_tests = len(p_values)
    alpha_adjusted = alpha / num_tests if num_tests > 0 else alpha

    corrected_p_values = [min(p * num_tests, 1.0) for p in p_values]
    significance_decisions = [p < alpha_adjusted for p in corrected_p_values]

    return {
        "corrected_p_values": corrected_p_values,
        "significance_decisions": significance_decisions,
        "alpha_adjusted": alpha_adjusted,
        "num_tests": num_tests,
        "original_alpha": alpha
    }


def analyze_significance(
    scores_by_class: Dict[str, List[float]],
    pairwise_p_values: Optional[List[float]] = None,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Complete significance analysis pipeline:
    1. Validate stratification
    2. Check sample sizes
    3. Perform ANOVA
    4. Apply Bonferroni correction (if pairwise p-values provided)
    5. Generate comprehensive report
    
    Args:
        scores_by_class: Dictionary mapping GarmentFeatureClass to list of scores
        pairwise_p_values: Optional list of p-values from pairwise t-tests
        alpha: Significance threshold
    
    Returns:
        Comprehensive analysis report dictionary
    """
    # Step 1: Validate stratification
    validate_stratification(scores_by_class)
    
    # Step 2: Check sample sizes
    sample_sizes = check_sample_sizes(scores_by_class)
    low_power_warning = has_low_sample_count(scores_by_class, threshold=30)
    critical_low_count = has_low_sample_count(scores_by_class, threshold=10)
    
    if critical_low_count:
        raise ValueError(
            "Insufficient samples for statistical analysis. "
            "At least 10 samples per class are required."
        )

    # Step 3: Perform ANOVA
    f_stat, p_value = perform_anova(scores_by_class)
    anova_significant = p_value < alpha

    # Step 4: Bonferroni correction if pairwise p-values provided
    bonferroni_result = None
    if pairwise_p_values is not None and len(pairwise_p_values) > 0:
        bonferroni_result = bonferroni_correction(pairwise_p_values, alpha)

    # Step 5: Compile report
    report = {
        "analysis_type": "One-Way ANOVA with Bonferroni Correction",
        "stratification_valid": True,
        "classes_analyzed": list(scores_by_class.keys()),
        "sample_sizes": sample_sizes,
        "low_power_warning": low_power_warning,
        "anova_results": {
            "f_statistic": f_stat,
            "p_value": p_value,
            "is_significant": anova_significant,
            "alpha": alpha
        },
        "bonferroni_correction": bonferroni_result,
        "conclusion": "Significant differences detected" if anova_significant else "No significant differences detected"
    }

    if low_power_warning:
        report["limitation"] = "Low statistical power due to sample size < 30 per class"

    return report


def run_pipeline(
    input_path: str,
    output_path: str,
    alpha: float = 0.05,
    pairwise_p_values: Optional[List[float]] = None
) -> None:
    """
    Main pipeline function to run significance analysis on fidelity scores.
    
    Args:
        input_path: Path to JSON file containing fidelity scores stratified by class
        output_path: Path to output JSON report
        alpha: Significance threshold
        pairwise_p_values: Optional list of pairwise comparison p-values
    """
    # Load input data
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Extract scores by class
    # Expected format: {"per_class": {"Color": {"mean_lpips": ..., "scores": [...]}, ...}}
    if "per_class" not in data:
        # Try alternative format: {"Color": [...], "Pattern": [...], ...}
        scores_by_class = data
    else:
        scores_by_class = {}
        for cls_name, cls_data in data["per_class"].items():
            if "scores" in cls_data:
                scores_by_class[cls_name] = cls_data["scores"]
            elif "mean_lpips" in cls_data:
                # If only mean is provided, we can't do ANOVA, but we'll handle gracefully
                # For now, assume this is an error in data format
                raise ValueError(
                    f"Class '{cls_name}' missing 'scores' array. "
                    "ANOVA requires individual sample scores, not just means."
                )
            else:
                raise ValueError(f"Class '{cls_name}' has invalid data format")
    
    # Run analysis
    report = analyze_significance(scores_by_class, pairwise_p_values, alpha)
    
    # Write output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Significance analysis report written to: {output_path}")


def main() -> None:
    """Command-line interface for significance analysis."""
    parser = argparse.ArgumentParser(description="Run statistical significance analysis on fidelity scores")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input JSON file with fidelity scores stratified by class"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to output JSON report"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance threshold (default: 0.05)"
    )
    parser.add_argument(
        "--pairwise-pvalues",
        type=str,
        default=None,
        help="Optional JSON string of pairwise p-values for Bonferroni correction"
    )
    
    args = parser.parse_args()
    
    pairwise_pvals = None
    if args.pairwise_pvalues:
        try:
            pairwise_pvals = json.loads(args.pairwise_pvalues)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format for --pairwise-pvalues")
    
    run_pipeline(
        input_path=args.input,
        output_path=args.output,
        alpha=args.alpha,
        pairwise_p_values=pairwise_pvals
    )


if __name__ == "__main__":
    main()
