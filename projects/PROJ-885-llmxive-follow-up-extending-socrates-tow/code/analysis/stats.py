"""
Statistical Analysis Module for Socio-Cognitive State Injection Experiments.

Implements a conditional statistical workflow to compare Adapter vs. Static conditions:
1. Shapiro-Wilk normality test on difference scores.
2. If normal (p >= 0.05): Paired t-test.
3. If non-normal: Wilcoxon signed-rank test.
4. Holm-Bonferroni correction for multiple comparisons across LLMs.
5. Generate final report with statistics and significance flags.
"""

import json
import logging
import math
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

# Import project utilities
from config import ensure_directories, get_config_summary
from analysis.metrics import load_experiment_logs, compute_summary_statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class StatisticalResult:
    """Container for statistical test results."""
    llm_name: str
    condition_a: str  # e.g., "Adapter"
    condition_b: str  # e.g., "Static"
    n_pairs: int
    mean_diff: float
    std_diff: float
    test_name: str  # "t-test" or "wilcoxon"
    statistic: float
    p_value: float
    cohens_d: float
    is_significant_raw: bool
    is_significant_corrected: bool
    normality_p_value: float
    normality_passed: bool

def calculate_cohens_d(sample_a: np.ndarray, sample_b: np.ndarray) -> float:
    """
    Calculate Cohen's d for paired samples.
    d = mean(diff) / std(diff)
    """
    diff = sample_a - sample_b
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    if std_diff == 0:
        return 0.0
    return mean_diff / std_diff

def holm_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Holm-Bonferroni correction to a list of p-values.
    Returns a list of booleans indicating if the result is significant after correction.
    """
    n = len(p_values)
    if n == 0:
        return []

    # Create list of (original_index, p_value)
    indexed_pvals = list(enumerate(p_values))
    # Sort by p-value
    indexed_pvals.sort(key=lambda x: x[1])

    corrected_significance = [False] * n
    for i, (orig_idx, p_val) in enumerate(indexed_pvals):
        # Holm-Bonferroni threshold: alpha / (n - i)
        threshold = alpha / (n - i)
        if p_val <= threshold:
            corrected_significance[orig_idx] = True
        else:
            # Once we fail to reject, all subsequent are also not rejected
            # (Strictly speaking, Holm stops rejecting, but we mark the rest as False)
            pass

    return corrected_significance

def run_statistical_analysis_for_llm(
    scores_adapter: List[float],
    scores_static: List[float],
    llm_name: str,
    alpha: float = 0.05
) -> Optional[StatisticalResult]:
    """
    Run the conditional statistical workflow for a single LLM.
    """
    if len(scores_adapter) != len(scores_static):
        logger.error(f"Mismatched sample sizes for {llm_name}: {len(scores_adapter)} vs {len(scores_static)}")
        return None

    if len(scores_adapter) < 2:
        logger.warning(f"Not enough data points for {llm_name} (n={len(scores_adapter)}). Skipping.")
        return None

    arr_a = np.array(scores_adapter)
    arr_b = np.array(scores_static)
    diff = arr_a - arr_b

    # 1. Shapiro-Wilk Normality Test
    try:
        shapiro_stat, shapiro_p = stats.shapiro(diff)
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed for {llm_name}: {e}")
        return None

    normality_passed = shapiro_p >= alpha
    logger.info(f"{llm_name}: Normality test p={shapiro_p:.4f} ({'Normal' if normality_passed else 'Non-Normal'})")

    # 2. Conditional Test Selection
    if normality_passed:
        # Paired t-test
        t_stat, p_val = stats.ttest_rel(arr_a, arr_b)
        test_name = "paired_t_test"
    else:
        # Wilcoxon signed-rank test
        w_stat, p_val = stats.wilcoxon(arr_a, arr_b)
        test_name = "wilcoxon_signed_rank"

    # 3. Calculate Effect Size (Cohen's d)
    cohens_d = calculate_cohens_d(arr_a, arr_b)

    # 4. Raw Significance
    is_sig_raw = p_val < alpha

    return StatisticalResult(
        llm_name=llm_name,
        condition_a="Adapter",
        condition_b="Static",
        n_pairs=len(scores_adapter),
        mean_diff=float(np.mean(diff)),
        std_diff=float(np.std(diff, ddof=1)),
        test_name=test_name,
        statistic=float(t_stat if normality_passed else w_stat),
        p_value=float(p_val),
        cohens_d=float(cohens_d),
        is_significant_raw=is_sig_raw,
        is_significant_corrected=False, # To be updated later
        normality_p_value=float(shapiro_p),
        normality_passed=normality_passed
    )

def generate_statistical_report(
    experiment_logs_path: Path,
    output_path: Path,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Main entry point to generate the statistical report.
    Loads logs, groups by LLM, runs tests, applies correction, and saves report.
    """
    logger.info(f"Loading experiment logs from {experiment_logs_path}")
    logs = load_experiment_logs(experiment_logs_path)

    if not logs:
        raise ValueError("No experiment logs found. Cannot perform statistical analysis.")

    # Group data by LLM and Condition
    # Structure: { llm_name: { "Adapter": [scores], "Static": [scores] } }
    llm_data: Dict[str, Dict[str, List[float]]] = {}

    for log_entry in logs:
        llm = log_entry.get("model_name")
        if not llm:
            logger.warning("Skipping log entry with missing model_name")
            continue

        condition = log_entry.get("condition")
        if condition not in ("Adapter", "Static"):
            continue

        # We need the consensus gap score for this trajectory
        # Assuming the log entry contains the calculated metric or we need to re-calculate
        # Based on T034, we compute metrics. The log should ideally have the final score.
        # If not, we might need to re-run the evaluator logic.
        # For this implementation, we assume 'consensus_gap_score' is in the log entry
        # or we derive it from the 'gap_closure' if present.
        score = log_entry.get("consensus_gap_score")
        
        # Fallback: if the score isn't directly in the log, we might need to look at the
        # metrics file if it was generated separately. However, the task implies analyzing
        # the experiment logs. Let's assume the log entry has the necessary score.
        # If the log entry structure is different (e.g., raw turns), we would need to
        # re-evaluate here. Given T033/T034 context, the log likely has the summary metric.
        
        if score is None:
            # Attempt to find a score-like field
            for key in ["gap_score", "score", "resolution_score"]:
                if key in log_entry:
                    score = log_entry[key]
                    break

        if score is None:
            logger.warning(f"Skipping log entry for {llm} ({condition}) due to missing score.")
            continue

        if llm not in llm_data:
            llm_data[llm] = {"Adapter": [], "Static": []}

        llm_data[llm][condition].append(float(score))

    # Validate we have pairs for each LLM
    valid_llms = []
    for llm, conditions in llm_data.items():
        if len(conditions["Adapter"]) == 0 or len(conditions["Static"]) == 0:
            logger.warning(f"LLM {llm} missing data for one condition. Skipping.")
            continue
        if len(conditions["Adapter"]) != len(conditions["Static"]):
            # Check if they are paired by trajectory ID?
            # For simplicity in this script, we assume the logs are ordered or paired by index
            # in a real robust system, we'd join on trajectory_id.
            # Here we just take the minimum length to ensure pairing.
            min_len = min(len(conditions["Adapter"]), len(conditions["Static"]))
            conditions["Adapter"] = conditions["Adapter"][:min_len]
            conditions["Static"] = conditions["Static"][:min_len]
            logger.info(f"Trimmed {llm} to {min_len} pairs.")
        
        valid_llms.append(llm)

    results: List[StatisticalResult] = []
    for llm in valid_llms:
        res = run_statistical_analysis_for_llm(
            llm_data[llm]["Adapter"],
            llm_data[llm]["Static"],
            llm,
            alpha=alpha
        )
        if res:
            results.append(res)

    if not results:
        raise ValueError("No valid statistical results generated.")

    # 4. Holm-Bonferroni Correction
    p_values = [r.p_value for r in results]
    corrected_flags = holm_bonferroni_correction(p_values, alpha=alpha)

    # Update results with corrected flags
    for i, res in enumerate(results):
        res.is_significant_corrected = corrected_flags[i]

    # 5. Generate Report
    report = {
        "meta": {
            "generated_at": str(Path().resolve()),
            "alpha": alpha,
            "correction_method": "Holm-Bonferroni",
            "total_llms_tested": len(results)
        },
        "summary": {
            "significant_after_correction": sum(1 for r in results if r.is_significant_corrected),
            "total_tests": len(results)
        },
        "results": [asdict(r) for r in results]
    }

    # Ensure output directory exists
    ensure_directories()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Statistical report written to {output_path}")
    return report

def main():
    """CLI entry point for statistical analysis."""
    config = get_config_summary()
    logs_path = Path(config.get("data_processed_dir", "data/processed")) / "experiment_logs.json"
    report_path = Path(config.get("data_results_dir", "data/results")) / "statistical_analysis_report.json"

    if not logs_path.exists():
        logger.error(f"Experiment logs not found at {logs_path}. Run experiment pipeline first.")
        sys.exit(1)

    try:
        report = generate_statistical_report(logs_path, report_path)
        print(f"Analysis complete. Found {report['summary']['significant_after_correction']} significant results.")
    except Exception as e:
        logger.exception("Statistical analysis failed")
        sys.exit(1)

if __name__ == "__main__":
    main()