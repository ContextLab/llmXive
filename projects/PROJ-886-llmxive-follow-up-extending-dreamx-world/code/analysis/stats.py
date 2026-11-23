import os
import json
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from scipy import stats as scipy_stats
from utils.config import ensure_directories
from code.analysis.metrics_writer import load_metrics_csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_metrics_csv(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load metrics from the derived CSV file.
    Handles null values for failed SfM trajectories (mae_position, mae_rotation).
    """
    return load_metrics_csv(csv_path)

def load_convergence_flags(metrics_data: List[Dict[str, Any]]) -> Tuple[List[int], List[int]]:
    """
    Extract convergence flags for Baseline and DreamX-Lite.
    Returns two lists of 0/1 integers (1 = converged/SfM success).
    """
    baseline_flags = []
    dreamx_flags = []
    for row in metrics_data:
        # Assuming columns 'baseline_converged' and 'dreamx_converged' exist or derived from sfm_status
        # Based on T025, we check if convergence is true
        b_flag = 1 if row.get('baseline_converged', False) else 0
        d_flag = 1 if row.get('dreamx_converged', False) else 0
        baseline_flags.append(b_flag)
        dreamx_flags.append(d_flag)
    return baseline_flags, dreamx_flags

def calculate_censoring_rate(flags: List[int]) -> float:
    """
    Calculate the censoring rate (proportion of failed trajectories).
    Censoring Rate = (Total - Converged) / Total
    """
    if not flags:
        return 0.0
    failed = sum(1 for f in flags if f == 0)
    return failed / len(flags)

def mcnemar_test(baseline_flags: List[int], dreamx_flags: List[int]) -> Dict[str, Any]:
    """
    Perform McNemar's test for paired binary data (convergence).
    Null Hypothesis: The proportion of successes is the same for both models.
    """
    if len(baseline_flags) != len(dreamx_flags):
        raise ValueError("Flag lists must be of equal length")

    n = len(baseline_flags)
    # Contingency table:
    #           DreamX Success | DreamX Failure
    # Base Succ       a              b
    # Base Fail       c              d
    
    a = sum(1 for b, d in zip(baseline_flags, dreamx_flags) if b == 1 and d == 1)
    b = sum(1 for b, d in zip(baseline_flags, dreamx_flags) if b == 1 and d == 0)
    c = sum(1 for b, d in zip(baseline_flags, dreamx_flags) if b == 0 and d == 1)
    d = sum(1 for b, d in zip(baseline_flags, dreamx_flags) if b == 0 and d == 0)

    # McNemar's chi-squared statistic: (|b - c| - 1)^2 / (b + c) with continuity correction
    if (b + c) == 0:
        logger.warning("No discordant pairs found. McNemar's test undefined.")
        return {
            "test_statistic": None,
            "p_value": None,
            "null_hypothesis": "Proportions are equal",
            "contingency_table": {"a": a, "b": b, "c": c, "d": d}
        }

    stat = ((abs(b - c) - 1) ** 2) / (b + c)
    p_val = 1.0 - scipy_stats.chi2.cdf(stat, df=1)

    return {
        "test_statistic": float(stat),
        "p_value": float(p_val),
        "null_hypothesis": "The proportion of converged trajectories is the same for Baseline and DreamX-Lite.",
        "contingency_table": {"a": a, "b": b, "c": c, "d": d},
        "discordant_pairs": b + c
    }

def wilcoxon_signed_rank_test(metrics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Perform Wilcoxon signed-rank test on MAE scores for converged trajectories only.
    Filters out rows where convergence is false (null MAE).
    """
    baseline_maes = []
    dreamx_maes = []

    for row in metrics_data:
        # Only include if both converged (or at least one, but typically paired requires both)
        # Spec says: filter for convergence=true. Assuming we compare pairs where both succeeded.
        b_conv = row.get('baseline_converged', False)
        d_conv = row.get('dreamx_converged', False)
        
        if b_conv and d_conv:
            b_mae = row.get('mae_position_baseline')
            d_mae = row.get('mae_position_dreamx')
            
            if b_mae is not None and d_mae is not None:
                baseline_maes.append(float(b_mae))
                dreamx_maes.append(float(d_mae))

    if len(baseline_maes) < 2:
        logger.warning("Not enough converged pairs for Wilcoxon test.")
        return {
            "test_statistic": None,
            "p_value": None,
            "null_hypothesis": "The distribution of MAE differences is symmetric around zero.",
            "n_converged_pairs": len(baseline_maes)
        }

    stat, p_val = scipy_stats.wilcoxon(baseline_maes, dreamx_maes)

    return {
        "test_statistic": float(stat),
        "p_value": float(p_val),
        "null_hypothesis": "The distribution of differences in MAE (Baseline - DreamX-Lite) is symmetric around zero.",
        "n_converged_pairs": len(baseline_maes)
    }

def calculate_information_theoretic_sufficiency_ratio(metrics_data: List[Dict[str, Any]]) -> float:
    """
    Calculate the Information-Theoretic Sufficiency Ratio (ITSR).
    Formula: (Converged Count) / (Total Count) * (Mean Success Rate)
    Simplified as the proportion of useful data points that are valid for analysis.
    Per Spec SC-005, this measures the 'quality' of the dataset for statistical inference.
    Here we define it as the ratio of converged pairs to total pairs.
    """
    total = len(metrics_data)
    if total == 0:
        return 0.0
    
    valid_pairs = 0
    for row in metrics_data:
        if row.get('baseline_converged', False) and row.get('dreamx_converged', False):
            valid_pairs += 1
    
    return valid_pairs / total

def run_statistical_analysis(csv_path: str, output_json_path: str) -> Dict[str, Any]:
    """
    Orchestrate the full statistical analysis:
    1. Load metrics
    2. Calculate Censoring Rate
    3. Run McNemar's Test
    4. Run Wilcoxon Signed-Rank Test
    5. Calculate ITSR
    6. Save results to JSON
    """
    logger.info(f"Loading metrics from {csv_path}")
    metrics_data = load_metrics_csv(csv_path)
    
    if not metrics_data:
        raise ValueError("No metrics data found. Cannot run analysis.")

    # 1. Censoring Rates
    b_flags, d_flags = load_convergence_flags(metrics_data)
    b_censor = calculate_censoring_rate(b_flags)
    d_censor = calculate_censoring_rate(d_flags)

    # 2. McNemar
    mcnemar_results = mcnemar_test(b_flags, d_flags)

    # 3. Wilcoxon
    wilcoxon_results = wilcoxon_signed_rank_test(metrics_data)

    # 4. ITSR
    itsr = calculate_information_theoretic_sufficiency_ratio(metrics_data)

    results = {
        "total_trajectories": len(metrics_data),
        "censoring_rate": {
            "baseline": b_censor,
            "dreamx_lite": d_censor
        },
        "mcnemar_test": mcnemar_results,
        "wilcoxon_test": wilcoxon_results,
        "information_theoretic_sufficiency_ratio": itsr,
        "metadata": {
            "input_file": csv_path,
            "analysis_timestamp": str(np.datetime64('now'))
        }
    }

    # Ensure output directory exists
    ensure_directories([str(Path(output_json_path).parent)])

    with open(output_json_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Statistical results saved to {output_json_path}")
    return results

def main():
    """Entry point for the statistical analysis script."""
    # Default paths based on project structure
    base_dir = Path(__file__).parent.parent.parent
    csv_path = base_dir / "data" / "derived" / "metrics.csv"
    json_path = base_dir / "data" / "derived" / "statistical_results.json"

    # Allow override via arguments if needed, but for now use defaults or env
    import argparse
    parser = argparse.ArgumentParser(description="Run Statistical Analysis on DreamX-Lite Metrics")
    parser.add_argument("--input-csv", type=str, default=str(csv_path), help="Path to metrics.csv")
    parser.add_argument("--output-json", type=str, default=str(json_path), help="Path to output JSON")
    args = parser.parse_args()

    try:
        run_statistical_analysis(args.input_csv, args.output_json)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise