"""
Statistical significance analysis module for fidelity benchmarking.

Implements ANOVA testing, Bonferroni correction, and edge case handling
for low sample power scenarios.
"""
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import warnings

import numpy as np
from scipy import stats

# Minimum sample size threshold for reliable statistical testing
MIN_SAMPLE_SIZE_FOR_POWER = 30
MIN_SAMPLE_SIZE_FOR_WARNING = 10

def check_sample_sizes(scores_by_class: Dict[str, List[float]]) -> Dict[str, int]:
    """
    Check and report sample sizes for each garment feature class.
    
    Args:
        scores_by_class: Dictionary mapping class names to lists of scores
        
    Returns:
        Dictionary mapping class names to their sample counts
    """
    sample_counts = {class_name: len(scores) for class_name, scores in scores_by_class.items()}
    return sample_counts

def has_low_sample_count(scores_by_class: Dict[str, List[float]], threshold: int = MIN_SAMPLE_SIZE_FOR_POWER) -> Tuple[bool, Dict[str, bool]]:
    """
    Determine if any class has insufficient sample size for reliable statistical testing.
    
    Args:
        scores_by_class: Dictionary mapping class names to lists of scores
        threshold: Minimum sample size required (default: 30)
        
    Returns:
        Tuple of (any_low_power: bool, low_power_classes: Dict[class_name, bool])
    """
    sample_counts = check_sample_sizes(scores_by_class)
    low_power_classes = {
        class_name: count < threshold 
        for class_name, count in sample_counts.items()
    }
    any_low = any(low_power_classes.values())
    return any_low, low_power_classes

def perform_anova(scores_by_class: Dict[str, List[float]]) -> Tuple[float, float]:
    """
    Perform one-way ANOVA test on fidelity scores across feature classes.
    
    Args:
        scores_by_class: Dictionary mapping class names to lists of scores
        
    Returns:
        Tuple of (f_statistic, p_value)
        
    Raises:
        ValueError: If insufficient data for ANOVA
    """
    # Extract score lists for each class
    score_lists = list(scores_by_class.values())
    
    # Filter out empty lists
    score_lists = [scores for scores in score_lists if len(scores) > 0]
    
    if len(score_lists) < 2:
        raise ValueError("Insufficient classes with data for ANOVA test (need at least 2)")
    
    # Perform one-way ANOVA
    f_stat, p_val = stats.f_oneway(*score_lists)
    return f_stat, p_val

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction for multiple hypothesis testing.
    
    Args:
        p_values: List of raw p-values from pairwise tests
        alpha: Significance level (default: 0.05)
        
    Returns:
        Tuple of (corrected_p_values, significant_results)
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return [], []
    
    # Bonferroni correction: multiply p-values by number of tests
    corrected_p_values = [min(p * n_tests, 1.0) for p in p_values]
    
    # Determine significance
    significant_results = [p < alpha for p in corrected_p_values]
    
    return corrected_p_values, significant_results

def analyze_significance(scores_by_class: Dict[str, List[float]], 
                         alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform complete significance analysis with edge case handling.
    
    Args:
        scores_by_class: Dictionary mapping class names to lists of scores
        alpha: Significance level for hypothesis tests
        
    Returns:
        Dictionary containing analysis results and warnings
    """
    result = {
        "analysis_complete": False,
        "sample_sizes": {},
        "low_power_warning": False,
        "low_power_classes": {},
        "anova_results": None,
        "bonferroni_results": None,
        "warnings": []
    }
    
    # Check sample sizes
    result["sample_sizes"] = check_sample_sizes(scores_by_class)
    any_low, low_power_classes = has_low_sample_count(scores_by_class, MIN_SAMPLE_SIZE_FOR_POWER)
    
    if any_low:
        result["low_power_warning"] = True
        result["low_power_classes"] = {k: v for k, v in low_power_classes.items() if v}
        
        # Collect warnings for classes with low power
        for class_name, is_low in low_power_classes.items():
            if is_low:
                count = result["sample_sizes"][class_name]
                if count < MIN_SAMPLE_SIZE_FOR_WARNING:
                    warning_msg = (
                        f"CRITICAL: Class '{class_name}' has only {count} samples "
                        f"(< {MIN_SAMPLE_SIZE_FOR_WARNING}). Statistical tests may be unreliable."
                    )
                    result["warnings"].append(warning_msg)
                else:
                    warning_msg = (
                        f"WARNING: Class '{class_name}' has {count} samples "
                        f"(< {MIN_SAMPLE_SIZE_FOR_POWER}). Reduced statistical power."
                    )
                    result["warnings"].append(warning_msg)
    
    # Attempt ANOVA only if we have sufficient data
    try:
        f_stat, p_val = perform_anova(scores_by_class)
        result["anova_results"] = {
            "f_statistic": float(f_stat),
            "p_value": float(p_val),
            "is_significant": p_val < alpha,
            "alpha": alpha
        }
        
        # If ANOVA is significant, perform pairwise comparisons with Bonferroni
        if p_val < alpha:
            # Perform pairwise t-tests
            class_names = list(scores_by_class.keys())
            p_values = []
            comparisons = []
            
            for i in range(len(class_names)):
                for j in range(i + 1, len(class_names)):
                    group1 = scores_by_class[class_names[i]]
                    group2 = scores_by_class[class_names[j]]
                    
                    if len(group1) > 0 and len(group2) > 0:
                        _, p = stats.ttest_ind(group1, group2, equal_var=False)
                        p_values.append(p)
                        comparisons.append(f"{class_names[i]} vs {class_names[j]}")
            
            if len(p_values) > 0:
                corrected_p, significant = bonferroni_correction(p_values, alpha)
                result["bonferroni_results"] = {
                    "comparisons": comparisons,
                    "raw_p_values": [float(p) for p in p_values],
                    "corrected_p_values": corrected_p,
                    "significant": significant,
                    "alpha": alpha
                }
        
        result["analysis_complete"] = True
        
    except ValueError as e:
        warning_msg = f"ANOVA test failed: {str(e)}"
        result["warnings"].append(warning_msg)
        result["analysis_complete"] = False
    
    return result

def run_pipeline(input_path: str, output_path: str, alpha: float = 0.05) -> None:
    """
    Run the significance analysis pipeline on fidelity scores.
    
    Args:
        input_path: Path to JSON file containing raw fidelity scores by class
        output_path: Path to write the analysis results
        alpha: Significance level for hypothesis tests
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load raw scores
    with open(input_file, 'r') as f:
        raw_scores = json.load(f)
    
    # Organize scores by garment feature class
    scores_by_class = defaultdict(list)
    for record in raw_scores.get("scores", []):
        class_name = record.get("garment_feature_class")
        lpips_score = record.get("lpips")
        
        if class_name and lpips_score is not None:
            scores_by_class[class_name].append(lpips_score)
    
    if not scores_by_class:
        raise ValueError("No valid scores found in input file")
    
    # Perform analysis
    analysis_results = analyze_significance(dict(scores_by_class), alpha)
    
    # Add metadata
    analysis_results["input_file"] = str(input_file)
    analysis_results["total_samples"] = sum(analysis_results["sample_sizes"].values())
    analysis_results["classes_analyzed"] = list(scores_by_class.keys())
    
    # Write results
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(analysis_results, f, indent=2)
    
    # Print summary to stdout
    print(f"Analysis complete. Results written to: {output_path}")
    print(f"Total samples: {analysis_results['total_samples']}")
    print(f"Classes analyzed: {', '.join(analysis_results['classes_analyzed'])}")
    
    if analysis_results["low_power_warning"]:
        print("\n⚠️  LOW SAMPLE POWER DETECTED:")
        for warning in analysis_results["warnings"]:
            if "CRITICAL" in warning or "WARNING" in warning:
                print(f"  - {warning}")
    
    if analysis_results["anova_results"]:
        anova = analysis_results["anova_results"]
        print(f"\nANOVA Results: F={anova['f_statistic']:.4f}, p={anova['p_value']:.6f}")
        print(f"Significant difference found: {anova['is_significant']}")
    
    if analysis_results.get("bonferroni_results"):
        bonf = analysis_results["bonferroni_results"]
        print(f"\nPairwise Comparisons (Bonferroni corrected):")
        for i, comp in enumerate(bonf["comparisons"]):
            sig_str = "✓" if bonf["significant"][i] else "✗"
            print(f"  {sig_str} {comp}: p={bonf['corrected_p_values'][i]:.6f}")

def main():
    """Main entry point for command-line execution."""
    parser = argparse.ArgumentParser(
        description="Perform statistical significance analysis on fidelity scores"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to JSON file containing raw fidelity scores"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to write analysis results"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for hypothesis tests (default: 0.05)"
    )
    
    args = parser.parse_args()
    
    try:
        run_pipeline(args.input, args.output, args.alpha)
    except Exception as e:
        print(f"Error during analysis: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
