import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from scipy import stats

from src.utils.logging_config import get_logger, setup_logging

def load_success_rates(eval_results_path: str) -> Dict[str, List[float]]:
    """
    Load success rate vectors from the evaluation results JSON.
    
    Expected structure in JSON:
    {
        "within-embodiment": {"success_rate": [0.8, 0.75, ...], ...},
        "cross-embodiment": {"success_rate": [0.6, 0.65, ...], ...}
    }
    
    Returns a dict mapping scenario names to their success rate lists.
    """
    logger = get_logger("wilcoxon_test")
    
    if not os.path.exists(eval_results_path):
        raise FileNotFoundError(f"Evaluation results file not found: {eval_results_path}")
    
    with open(eval_results_path, 'r') as f:
        data = json.load(f)
    
    result = {}
    for key in ['within-embodiment', 'cross-embodiment']:
        if key in data and 'success_rate' in data[key]:
            result[key] = data[key]['success_rate']
            logger.info(f"Loaded {len(result[key])} success rates for {key}")
        else:
            logger.warning(f"Missing success rates for {key} in {eval_results_path}")
    
    return result

def compute_wilcoxon_signed_rank(
    sample1: List[float], 
    sample2: List[float]
) -> Tuple[float, float]:
    """
    Compute the Wilcoxon signed-rank test statistic and p-value.
    
    Args:
        sample1: Success rates from the first condition (e.g., cross-embodiment).
        sample2: Success rates from the second condition (e.g., within-embodiment).
        
    Returns:
        Tuple of (statistic, p_value).
    """
    if len(sample1) != len(sample2):
        raise ValueError(
            f"Sample sizes must match for paired test: "
            f"len(sample1)={len(sample1)}, len(sample2)={len(sample2)}"
        )
    
    if len(sample1) < 2:
        raise ValueError("At least 2 paired samples are required for Wilcoxon test.")
    
    statistic, p_value = stats.wilcoxon(sample1, sample2)
    return statistic, p_value

def apply_holm_bonferroni(p_values: List[float]) -> List[bool]:
    """
    Apply Holm-Bonferroni correction to a list of p-values.
    
    This function determines which comparisons are significant after correction.
    
    Args:
        p_values: List of raw p-values from multiple tests.
        
    Returns:
        List of booleans indicating if each test is significant after correction.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values with their original indices
    sorted_indices = sorted(range(n), key=lambda i: p_values[i])
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    # Apply Holm-Bonferroni step-down procedure
    # Compare sorted p-values against alpha / (n - rank)
    alpha = 0.05
    significant = [True] * n
    
    for rank, (idx, p_val) in enumerate(zip(sorted_indices, sorted_p_values)):
        threshold = alpha / (n - rank)
        if p_val > threshold:
            # From this point on, no tests are significant
            for i in range(rank, n):
                significant[sorted_indices[i]] = False
            break
    
    # Reorder results to match original input order
    reordered_significant = [significant[i] for i in range(n)]
    return reordered_significant

def run_wilcoxon_analysis(
    eval_results_path: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Run the full Wilcoxon signed-rank test analysis with Holm-Bonferroni correction.
    
    Args:
        eval_results_path: Path to the evaluation results JSON file.
        output_path: Path where the results JSON will be written.
        
    Returns:
        Dictionary containing the analysis results.
    """
    logger = get_logger("wilcoxon_test")
    logger.info(f"Starting Wilcoxon analysis on {eval_results_path}")
    
    # Load data
    success_rates = load_success_rates(eval_results_path)
    
    if 'within-embodiment' not in success_rates or 'cross-embodiment' not in success_rates:
        raise ValueError(
            "Evaluation results must contain both 'within-embodiment' and "
            "'cross-embodiment' success rate vectors."
        )
    
    within_emb = success_rates['within-embodiment']
    cross_emb = success_rates['cross-embodiment']
    
    # Perform Wilcoxon signed-rank test
    statistic, p_value = compute_wilcoxon_signed_rank(cross_emb, within_emb)
    
    # For a single comparison, Holm-Bonferroni is equivalent to no correction,
    # but we implement it generally for consistency with the pipeline design.
    # We treat this as a single hypothesis test.
    is_significant = apply_holm_bonferroni([p_value])[0]
    
    # Prepare results
    results = {
        "p_value": float(p_value),
        "is_significant": bool(is_significant),
        "method": "wilcoxon_signed_rank_with_holm_bonferroni",
        "statistic": float(statistic),
        "n_samples": len(within_emb),
        "mean_within_embodiment": float(sum(within_emb) / len(within_emb)),
        "mean_cross_embodiment": float(sum(cross_emb) / len(cross_emb)),
        "improvement": float(sum(within_emb) / len(within_emb) - sum(cross_emb) / len(cross_emb))
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis complete. Results written to {output_path}")
    logger.info(f"p-value: {p_value:.6f}, Significant: {is_significant}")
    
    return results

def main():
    """CLI entry point for the Wilcoxon test."""
    setup_logging()
    logger = get_logger("wilcoxon_test")
    
    # Default paths based on project structure
    base_dir = Path(__file__).resolve().parent.parent.parent
    eval_results_path = base_dir / "data" / "eval_results.json"
    output_path = base_dir / "data" / "stat_results.json"
    
    # Allow overrides via environment variables
    if "EVAL_RESULTS_PATH" in os.environ:
        eval_results_path = Path(os.environ["EVAL_RESULTS_PATH"])
    if "STAT_RESULTS_PATH" in os.environ:
        output_path = Path(os.environ["STAT_RESULTS_PATH"])
    
    try:
        results = run_wilcoxon_analysis(str(eval_results_path), str(output_path))
        print(json.dumps(results, indent=2))
        sys.exit(0)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
