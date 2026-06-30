import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from scipy import stats as scipy_stats

from src.lib.config import get_logger, set_seed

def calculate_mcnemar_p_value(
    fine_tuned_valid: int,
    fine_tuned_invalid: int,
    baseline_valid: int,
    baseline_invalid: int
) -> float:
    """
    Calculate McNemar's test p-value for binary validity scores.
    
    Args:
        fine_tuned_valid: Number of samples where fine-tuned model was valid but baseline was invalid (b)
        fine_tuned_invalid: Number of samples where fine-tuned model was invalid but baseline was valid (c)
        baseline_valid: Number of samples where both were valid (a) - not used in McNemar's
        baseline_invalid: Number of samples where both were invalid (d) - not used in McNemar's
        
    Returns:
        p-value from McNemar's test (chi-squared distribution with 1 degree of freedom)
    """
    # McNemar's test focuses on discordant pairs (b and c)
    # b = fine_tuned_valid (model valid, baseline invalid)
    # c = fine_tuned_invalid (model invalid, baseline valid)
    b = fine_tuned_valid
    c = fine_tuned_invalid
    
    # Handle edge cases
    if b + c == 0:
        # No discordant pairs, cannot compute test statistic
        logging.warning("No discordant pairs found. McNemar's test undefined.")
        return 1.0
    
    # Use exact binomial test for small samples or chi-squared for large samples
    # scipy.stats.mcnemar handles this internally
    try:
        result = scipy_stats.mcnemar([[0, b], [c, 0]], exact=True)
        return result.pvalue
    except Exception as e:
        logging.error(f"McNemar's test failed: {e}")
        return 1.0

def generate_statistical_report(
    validation_scores_path: Path,
    output_path: Path,
    confidence_level: float = 0.95
) -> Dict[str, Any]:
    """
    Generate statistical report comparing fine-tuned model vs baseline.
    
    Args:
        validation_scores_path: Path to JSON file containing validation scores
        output_path: Path to write the markdown report
        confidence_level: Confidence level for intervals (default 0.95)
        
    Returns:
        Dictionary containing statistical analysis results
    """
    logger = get_logger(__name__)
    logger.info(f"Loading validation scores from {validation_scores_path}")
    
    if not validation_scores_path.exists():
        raise FileNotFoundError(f"Validation scores file not found: {validation_scores_path}")
        
    with open(validation_scores_path, 'r') as f:
        scores_data = json.load(f)
    
    # Extract binary validity scores
    fine_tuned_scores = scores_data.get('fine_tuned', [])
    baseline_scores = scores_data.get('baseline', [])
    
    if len(fine_tuned_scores) != len(baseline_scores):
        raise ValueError("Fine-tuned and baseline scores must have the same length")
        
    if len(fine_tuned_scores) == 0:
        raise ValueError("No scores found in validation data")
    
    logger.info(f"Analyzing {len(fine_tuned_scores)} paired samples")
    
    # Calculate discordant pairs for McNemar's test
    # b: fine_tuned valid (1), baseline invalid (0)
    # c: fine_tuned invalid (0), baseline valid (1)
    b_count = 0
    c_count = 0
    a_count = 0  # both valid
    d_count = 0  # both invalid
    
    for ft, bl in zip(fine_tuned_scores, baseline_scores):
        ft_valid = 1 if ft.get('valid', False) else 0
        bl_valid = 1 if bl.get('valid', False) else 0
        
        if ft_valid == 1 and bl_valid == 0:
            b_count += 1
        elif ft_valid == 0 and bl_valid == 1:
            c_count += 1
        elif ft_valid == 1 and bl_valid == 1:
            a_count += 1
        else:
            d_count += 1
    
    logger.info(f"Discordant pairs: b={b_count}, c={c_count}")
    logger.info(f"Concordant pairs: both_valid={a_count}, both_invalid={d_count}")
    
    # Calculate McNemar's p-value
    p_value = calculate_mcnemar_p_value(b_count, c_count, a_count, d_count)
    
    # Calculate improvement metrics
    ft_validity_rate = sum(1 for s in fine_tuned_scores if s.get('valid', False)) / len(fine_tuned_scores)
    bl_validity_rate = sum(1 for s in baseline_scores if s.get('valid', False)) / len(baseline_scores)
    improvement = ft_validity_rate - bl_validity_rate
    
    # Calculate confidence interval for difference in proportions (Wald interval)
    n = len(fine_tuned_scores)
    p_diff = improvement
    se_diff = (
        (ft_validity_rate * (1 - ft_validity_rate) / n) +
        (bl_validity_rate * (1 - bl_validity_rate) / n)
    ) ** 0.5
    
    # Critical value for 95% confidence (z-score)
    z_score = 1.96 if confidence_level == 0.95 else 2.576  # 99%
    ci_lower = p_diff - z_score * se_diff
    ci_upper = p_diff + z_score * se_diff
    
    # Determine significance
    is_significant = p_value < (1 - confidence_level)
    
    # Prepare results
    results = {
        "total_samples": n,
        "fine_tuned_validity_rate": round(ft_validity_rate, 4),
        "baseline_validity_rate": round(bl_validity_rate, 4),
        "improvement": round(improvement, 4),
        "confidence_interval": {
            "lower": round(ci_lower, 4),
            "upper": round(ci_upper, 4),
            "level": confidence_level
        },
        "mcnemar_test": {
            "b_count": b_count,
            "c_count": c_count,
            "p_value": round(p_value, 6),
            "is_significant": is_significant,
            "alpha": 1 - confidence_level
        },
        "concordant_pairs": {
            "both_valid": a_count,
            "both_invalid": d_count
        }
    }
    
    # Generate Markdown report
    report_lines = [
        "# Statistical Analysis Report: Fine-Tuned vs Baseline",
        "",
        "## Overview",
        f"- **Total Samples Analyzed**: {n}",
        f"- **Confidence Level**: {confidence_level * 100}%",
        "",
        "## Validity Rates",
        f"- **Fine-Tuned Model**: {ft_validity_rate:.2%} ({sum(1 for s in fine_tuned_scores if s.get('valid', False))}/{n})",
        f"- **Zero-Shot Baseline**: {bl_validity_rate:.2%} ({sum(1 for s in baseline_scores if s.get('valid', False))}/{n})",
        f"- **Absolute Improvement**: {improvement:.2%} (95% CI: [{ci_lower:.2%}, {ci_upper:.2%}])",
        "",
        "## McNemar's Test for Paired Binary Data",
        "",
        "McNemar's test was used to determine if the improvement in validity scores is statistically significant.",
        "",
        "| Category | Count |",
        "|----------|-------|",
        f"| Both Valid (a) | {a_count} |",
        f"| Fine-Tuned Valid, Baseline Invalid (b) | {b_count} |",
        f"| Fine-Tuned Invalid, Baseline Valid (c) | {c_count} |",
        f"| Both Invalid (d) | {d_count} |",
        "",
        f"**Test Statistic**: Chi-squared (1 df)",
        f"**P-value**: {p_value:.6f}",
        f"**Alpha Level**: {1 - confidence_level}",
        f"**Result**: {'Significant' if is_significant else 'Not Significant'} at {confidence_level * 100}% confidence",
        "",
        "## Conclusion",
        "",
        f"The fine-tuned model shows a {'statistically significant' if is_significant else 'non-significant'} improvement "
        f"over the zero-shot baseline (p = {p_value:.6f}).",
        "",
        f"The absolute improvement in route validity is {improvement:.2%} "
        f"with a {confidence_level * 100}% confidence interval of [{ci_lower:.2%}, {ci_upper:.2%}]."
    ]
    
    report_content = "\n".join(report_lines)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(report_content)
    
    logger.info(f"Statistical report written to {output_path}")
    
    return results

def main():
    """Entry point for statistical analysis script."""
    logger = get_logger(__name__)
    set_seed(42)
    
    # Default paths
    scores_path = Path("data/results/validation_scores.json")
    report_path = Path("data/results/statistical_report.md")
    
    # Parse arguments
    if len(sys.argv) > 1:
        scores_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        report_path = Path(sys.argv[2])
        
    logger.info(f"Running statistical analysis on {scores_path}")
    
    try:
        results = generate_statistical_report(scores_path, report_path)
        logger.info("Analysis completed successfully")
        logger.info(f"P-value: {results['mcnemar_test']['p_value']}")
        logger.info(f"Significant: {results['mcnemar_test']['is_significant']}")
        
        # Print summary to stdout
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()