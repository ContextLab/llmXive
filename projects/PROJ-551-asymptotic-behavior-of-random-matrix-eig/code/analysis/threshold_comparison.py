"""
Compare critical thresholds (theta_c) across different sparsity patterns.

This module implements Task T023: Compare theta_c across different sparsity
patterns (diagonal vs. random sparse) and output statistical comparison.

It loads the fitted threshold parameters from the curve fitting step (T022)
for different sparsity patterns, performs statistical comparison, and outputs
the results to data/processed/threshold_comparison_results.json and a summary
report to data/processed/threshold_comparison_report.md.
"""
import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

# Import from existing project modules
from utils.config import get_project_paths, load_config
from utils.results_logger import append_to_aggregated_results
from analysis.threshold_fit import load_sweep_results, fit_critical_threshold

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_fitted_thresholds(config_path: str = None) -> Dict[str, Dict[str, Any]]:
    """
    Load fitted threshold parameters for different sparsity patterns.
    
    Args:
        config_path: Path to configuration file (optional)
        
    Returns:
        Dictionary mapping sparsity pattern names to their fitted parameters
    """
    paths = get_project_paths(config_path)
    fit_params_path = paths["processed"] / "threshold_fit_params.json"
    
    if not fit_params_path.exists():
        raise FileNotFoundError(
            f"Fitted parameters file not found at {fit_params_path}. "
            "Run threshold fitting (T022) first."
        )
    
    with open(fit_params_path, 'r') as f:
        fit_data = json.load(f)
    
    # Extract results by sparsity pattern
    results_by_pattern = {}
    for pattern_name, pattern_data in fit_data.get("results", {}).items():
        if "theta_c" in pattern_data:
            results_by_pattern[pattern_name] = {
                "theta_c": pattern_data["theta_c"],
                "theta_c_std": pattern_data.get("theta_c_std", 0.0),
                "r_squared": pattern_data.get("r_squared", 0.0),
                "n_samples": pattern_data.get("n_samples", 0),
                "fit_params": pattern_data.get("fit_params", {}),
                "confidence_interval_95": pattern_data.get("confidence_interval_95", [None, None])
            }
    
    if not results_by_pattern:
        raise ValueError(
            "No fitted threshold results found. Ensure T022 has been run "
            "with multiple sparsity patterns."
        )
    
    logger.info(f"Loaded {len(results_by_pattern)} sparsity pattern results")
    return results_by_pattern

def compare_thresholds(
    results: Dict[str, Dict[str, Any]],
    reference_pattern: str = "diagonal"
) -> Dict[str, Any]:
    """
    Compare theta_c across sparsity patterns with statistical tests.
    
    Args:
        results: Dictionary of fitted results by sparsity pattern
        reference_pattern: Pattern to use as reference for comparison
        
    Returns:
        Dictionary containing comparison statistics
    """
    patterns = list(results.keys())
    if len(patterns) < 2:
        raise ValueError("Need at least 2 sparsity patterns to compare")
    
    if reference_pattern not in results:
        raise ValueError(f"Reference pattern '{reference_pattern}' not found in results")
    
    reference_theta_c = results[reference_pattern]["theta_c"]
    reference_std = results[reference_pattern].get("theta_c_std", 0.0)
    
    comparisons = []
    for pattern in patterns:
        if pattern == reference_pattern:
            continue
        
        theta_c = results[pattern]["theta_c"]
        std = results[pattern].get("theta_c_std", 0.0)
        
        # Calculate difference and relative shift
        diff = theta_c - reference_theta_c
        rel_shift = (diff / reference_theta_c) * 100 if reference_theta_c != 0 else 0.0
        
        # Simple z-score approximation (assuming independent estimates)
        if reference_std > 0 or std > 0:
            combined_std = np.sqrt(reference_std**2 + std**2)
            z_score = diff / combined_std if combined_std > 0 else 0.0
            # Approximate p-value for two-tailed test
            from scipy.stats import norm
            p_value = 2 * (1 - norm.cdf(abs(z_score)))
        else:
            z_score = 0.0
            p_value = 1.0
        
        comparisons.append({
            "pattern": pattern,
            "theta_c": theta_c,
            "theta_c_std": std,
            "reference_pattern": reference_pattern,
            "reference_theta_c": reference_theta_c,
            "difference": diff,
            "relative_shift_pct": rel_shift,
            "z_score": z_score,
            "p_value": p_value,
            "significant_at_0.05": p_value < 0.05,
            "significant_at_0.01": p_value < 0.01
        })
    
    # Overall statistics
    all_theta_c = [results[p]["theta_c"] for p in patterns]
    overall_mean = np.mean(all_theta_c)
    overall_std = np.std(all_theta_c, ddof=1) if len(patterns) > 1 else 0.0
    overall_range = max(all_theta_c) - min(all_theta_c)
    
    comparison_summary = {
        "reference_pattern": reference_pattern,
        "reference_theta_c": reference_theta_c,
        "n_patterns_compared": len(patterns) - 1,
        "patterns": patterns,
        "comparisons": comparisons,
        "overall_statistics": {
            "mean_theta_c": overall_mean,
            "std_theta_c": overall_std,
            "range_theta_c": overall_range,
            "min_theta_c": min(all_theta_c),
            "max_theta_c": max(all_theta_c)
        },
        "analysis_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return comparison_summary

def generate_comparison_report(comparison: Dict[str, Any]) -> str:
    """
    Generate a markdown report of the threshold comparison.
    
    Args:
        comparison: Comparison results dictionary
        
    Returns:
        Markdown formatted report string
    """
    lines = [
        "# Threshold Comparison Report: Sparsity Patterns",
        "",
        f"**Generated:** {comparison['analysis_timestamp']}",
        "",
        "## Summary",
        "",
        f"This report compares the critical threshold (θ_c) across {comparison['n_patterns_compared'] + 1} sparsity patterns.",
        f"Reference pattern: **{comparison['reference_pattern']}** (θ_c = {comparison['reference_theta_c']:.4f})",
        "",
        "## Overall Statistics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Mean θ_c across patterns | {comparison['overall_statistics']['mean_theta_c']:.4f} |",
        f"| Std θ_c | {comparison['overall_statistics']['std_theta_c']:.4f} |",
        f"| Range | {comparison['overall_statistics']['range_theta_c']:.4f} |",
        f"| Min θ_c | {comparison['overall_statistics']['min_theta_c']:.4f} |",
        f"| Max θ_c | {comparison['overall_statistics']['max_theta_c']:.4f} |",
        "",
        "## Pairwise Comparisons",
        "",
        f"Comparing each pattern to the reference (**{comparison['reference_pattern']}**):",
        "",
        "| Pattern | θ_c | Std | Difference | Rel. Shift (%) | Z-score | P-value | Significant (α=0.05) |",
        "|---------|-----|-----|------------|----------------|---------|---------|----------------------|"
    ]
    
    for comp in comparison["comparisons"]:
        sig_marker = "Yes" if comp["significant_at_0.05"] else "No"
        lines.append(
            f"| {comp['pattern']} | {comp['theta_c']:.4f} | {comp['theta_c_std']:.4f} | "
            f"{comp['difference']:.4f} | {comp['relative_shift_pct']:.2f}% | "
            f"{comp['z_score']:.3f} | {comp['p_value']:.4f} | {sig_marker} |"
        )
    
    lines.extend([
        "",
        "## Key Findings",
        "",
    ])
    
    # Identify significant shifts
    significant_shifts = [c for c in comparison["comparisons"] if c["significant_at_0.05"]]
    large_shifts = [c for c in comparison["comparisons"] if abs(c["relative_shift_pct"]) > 5.0]
    
    if significant_shifts:
        lines.append(f"- **{len(significant_shifts)}** pattern(s) show statistically significant differences (p < 0.05) from the reference.")
        for comp in significant_shifts:
            lines.append(f"  - {comp['pattern']}: θ_c = {comp['theta_c']:.4f} (p = {comp['p_value']:.4f})")
    else:
        lines.append("- No statistically significant differences found at α = 0.05 level.")
    
    if large_shifts:
        lines.append(f"- **{len(large_shifts)}** pattern(s) show >5% relative shift in θ_c:")
        for comp in large_shifts:
            direction = "higher" if comp["relative_shift_pct"] > 0 else "lower"
            lines.append(f"  - {comp['pattern']}: {abs(comp['relative_shift_pct']):.2f}% {direction}")
    else:
        lines.append("- All patterns show <5% relative shift in θ_c, indicating robustness to sparsity pattern choice.")
    
    lines.extend([
        "",
        "## Methodology",
        "",
        "Critical thresholds (θ_c) were estimated by fitting a sigmoid function to the",
        "probability of outlier emergence vs. perturbation strength (θ) for each sparsity",
        "pattern. Statistical comparisons use a z-test approximation based on the fitted",
        "standard errors.",
        "",
        "## Limitations",
        "",
        "- Comparisons assume independent estimates across patterns.",
        "- Confidence intervals are approximate (95% CI based on fitted standard errors).",
        "- Results are specific to the matrix sizes and perturbation ranks used in the sweep.",
        "",
        "---",
        f"*Report generated by T023: Threshold Comparison Analysis*",
    ])
    
    return "\n".join(lines)

def main(config_path: Optional[str] = None):
    """
    Main entry point for threshold comparison analysis.
    
    Loads fitted thresholds, performs statistical comparison, and outputs results.
    """
    logger.info("Starting threshold comparison analysis (T023)")
    
    try:
        # Load fitted results
        results = load_fitted_thresholds(config_path)
        logger.info(f"Loaded results for patterns: {list(results.keys())}")
        
        # Determine reference pattern (prefer 'diagonal' if available)
        reference = "diagonal" if "diagonal" in results else list(results.keys())[0]
        logger.info(f"Using '{reference}' as reference pattern")
        
        # Perform comparison
        comparison = compare_thresholds(results, reference_pattern=reference)
        logger.info(f"Completed comparison of {comparison['n_patterns_compared']} patterns")
        
        # Save JSON results
        paths = get_project_paths(config_path)
        output_json = paths["processed"] / "threshold_comparison_results.json"
        with open(output_json, 'w') as f:
            json.dump(comparison, f, indent=2)
        logger.info(f"Saved JSON results to {output_json}")
        
        # Generate and save report
        report = generate_comparison_report(comparison)
        output_report = paths["processed"] / "threshold_comparison_report.md"
        with open(output_report, 'w') as f:
            f.write(report)
        logger.info(f"Saved report to {output_report}")
        
        # Print summary to console
        print("\n" + "="*60)
        print("THRESHOLD COMPARISON SUMMARY")
        print("="*60)
        print(f"Reference pattern: {reference} (θ_c = {comparison['reference_theta_c']:.4f})")
        print(f"Patterns compared: {comparison['n_patterns_compared']}")
        print(f"Overall mean θ_c: {comparison['overall_statistics']['mean_theta_c']:.4f}")
        print(f"Overall std θ_c: {comparison['overall_statistics']['std_theta_c']:.4f}")
        print("-"*60)
        
        significant_count = sum(1 for c in comparison["comparisons"] if c["significant_at_0.05"])
        print(f"Significant differences (p < 0.05): {significant_count}")
        
        large_shift_count = sum(1 for c in comparison["comparisons"] if abs(c["relative_shift_pct"]) > 5.0)
        print(f"Patterns with >5% shift: {large_shift_count}")
        
        print("="*60)
        print(f"Full results: {output_json}")
        print(f"Report: {output_report}")
        print("="*60 + "\n")
        
        return comparison
        
    except FileNotFoundError as e:
        logger.error(f"Missing required data: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during comparison: {e}")
        raise

if __name__ == "__main__":
    main()
