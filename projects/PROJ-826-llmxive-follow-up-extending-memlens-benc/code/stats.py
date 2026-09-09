import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy.stats import wilcoxon

logger = logging.getLogger(__name__)

MIN_SAMPLE_SIZE = 30

def stratify_samples(
    results_fine: List[Dict[str, Any]],
    results_coarse: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter out samples with detection_status 'fallback' or 'zero_detection'.
    Returns paired lists of (fine_score, coarse_score) for valid samples.
    """
    valid_fine = []
    valid_coarse = []

    # Create lookup for coarse results by question_id
    coarse_lookup = {item['question_id']: item for item in results_coarse}

    for fine_item in results_fine:
        qid = fine_item['question_id']
        status = fine_item.get('detection_status', 'unknown')

        # Filter based on T021 logic
        if status in ['fallback', 'zero_detection']:
            logger.info(f"Stratifying out sample {qid} due to detection_status: {status}")
            continue

        if qid in coarse_lookup:
            valid_fine.append(fine_item)
            valid_coarse.append(coarse_lookup[qid])
        else:
            logger.warning(f"Missing coarse result for question_id: {qid}")

    return valid_fine, valid_coarse

def run_wilcoxon_test(
    fine_scores: List[float],
    coarse_scores: List[float]
) -> Optional[Dict[str, Any]]:
    """
    Run Wilcoxon signed-rank test on paired scores.
    Returns None if sample size is insufficient (handled by caller).
    """
    if len(fine_scores) != len(coarse_scores):
        raise ValueError("Fine and coarse score lists must be of equal length.")

    if len(fine_scores) < 2:
        return None

    try:
        statistic, p_value = wilcoxon(fine_scores, coarse_scores)
        return {
            "statistic": float(statistic),
            "p_value": float(p_value),
            "method": "wilcoxon_signed_rank"
        }
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        return None

def calculate_effect_size(
    fine_scores: List[float],
    coarse_scores: List[float]
) -> Dict[str, float]:
    """
    Calculate effect size (Cohen's d for paired samples).
    d = (mean_diff) / std_diff
    """
    if len(fine_scores) != len(coarse_scores) or len(fine_scores) == 0:
        return {"cohens_d": 0.0, "mean_diff": 0.0, "std_diff": 0.0}

    diff = np.array(fine_scores) - np.array(coarse_scores)
    mean_diff = float(np.mean(diff))
    std_diff = float(np.std(diff, ddof=1))

    if std_diff == 0:
        cohens_d = 0.0
    else:
        cohens_d = mean_diff / std_diff

    return {
        "cohens_d": cohens_d,
        "mean_diff": mean_diff,
        "std_diff": std_diff
    }

def check_significance(p_value: float, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Check if p-value indicates statistical significance.
    """
    is_significant = p_value < alpha
    return {
        "p_value": p_value,
        "alpha": alpha,
        "is_significant": is_significant,
        "interpretation": "Significant" if is_significant else "Not Significant"
    }

def handle_insufficient_sample_size(
    n: int,
    fine_scores: List[float],
    coarse_scores: List[float]
) -> Dict[str, Any]:
    """
    T025 Implementation: Handle cases where n < MIN_SAMPLE_SIZE.
    Returns descriptive statistics only, no inferential test.
    """
    if n >= MIN_SAMPLE_SIZE:
        return None

    logger.warning(
        f"Insufficient sample size (n={n} < {MIN_SAMPLE_SIZE}). "
        "Reporting descriptive statistics only."
    )

    fine_mean = float(np.mean(fine_scores)) if fine_scores else 0.0
    fine_std = float(np.std(fine_scores, ddof=1)) if len(fine_scores) > 1 else 0.0
    coarse_mean = float(np.mean(coarse_scores)) if coarse_scores else 0.0
    coarse_std = float(np.std(coarse_scores, ddof=1)) if len(coarse_scores) > 1 else 0.0

    diff = np.array(fine_scores) - np.array(coarse_scores) if fine_scores and coarse_scores else np.array([])
    mean_diff = float(np.mean(diff)) if len(diff) > 0 else 0.0
    std_diff = float(np.std(diff, ddof=1)) if len(diff) > 1 else 0.0

    return {
        "status": "insufficient_sample_size",
        "n": n,
        "min_required": MIN_SAMPLE_SIZE,
        "descriptive_stats": {
            "fine": {
                "mean": fine_mean,
                "std": fine_std,
                "count": len(fine_scores)
            },
            "coarse": {
                "mean": coarse_mean,
                "std": coarse_std,
                "count": len(coarse_scores)
            },
            "difference": {
                "mean": mean_diff,
                "std": std_diff
            }
        },
        "inferential_test": None,
        "message": f"Sample size (n={n}) is below threshold ({MIN_SAMPLE_SIZE}). Wilcoxon test skipped."
    }

def generate_comparison_report(
    results_fine: List[Dict[str, Any]],
    results_coarse: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main orchestrator for statistical comparison (T022, T024, T025).
    1. Stratify samples.
    2. Check sample size.
    3. If n >= 30: Run Wilcoxon + Effect Size.
    4. If n < 30: Return descriptive stats only (T025).
    5. Save report to disk.
    """
    # 1. Stratify
    valid_fine, valid_coarse = stratify_samples(results_fine, results_coarse)
    n = len(valid_fine)

    if n == 0:
        report = {
            "status": "error",
            "message": "No valid samples remaining after stratification.",
            "n": 0
        }
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
        return report

    # Extract scores (assuming 'accuracy' key exists from T020)
    fine_scores = [item.get('accuracy', 0.0) for item in valid_fine]
    coarse_scores = [item.get('accuracy', 0.0) for item in valid_coarse]

    # 2. Check Sample Size (T025)
    if n < MIN_SAMPLE_SIZE:
        report = handle_insufficient_sample_size(n, fine_scores, coarse_scores)
    else:
        # 3. Run Inferential Test
        test_result = run_wilcoxon_test(fine_scores, coarse_scores)
        effect_size = calculate_effect_size(fine_scores, coarse_scores)
        significance = None
        if test_result and test_result['p_value'] is not None:
            significance = check_significance(test_result['p_value'])

        report = {
            "status": "complete",
            "n": n,
            "descriptive_stats": {
                "fine": {
                    "mean": float(np.mean(fine_scores)),
                    "std": float(np.std(fine_scores, ddof=1)),
                    "count": n
                },
                "coarse": {
                    "mean": float(np.mean(coarse_scores)),
                    "std": float(np.std(coarse_scores, ddof=1)),
                    "count": n
                }
            },
            "inferential_test": {
                "method": "wilcoxon_signed_rank",
                "results": test_result,
                "effect_size": effect_size,
                "significance": significance
            }
        }

    # 4. Save Report
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Comparison report saved to {output_path}")

    return report

def main():
    """
    Entry point for stats module.
    Expects input files to be passed via arguments or hardcoded paths for testing.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run statistical comparison on evaluation results.")
    parser.add_argument("--fine-input", type=str, required=True, help="Path to fine strategy results JSON")
    parser.add_argument("--coarse-input", type=str, required=True, help="Path to coarse strategy results JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output comparison report JSON")
    args = parser.parse_args()

    with open(args.fine_input, 'r') as f:
        results_fine = json.load(f)
    with open(args.coarse_input, 'r') as f:
        results_coarse = json.load(f)

    report = generate_comparison_report(results_fine, results_coarse, args.output)
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()