"""
Sensitivity analysis module.

Implements threshold sweeping and robustness checks for statistical results.
"""
import logging
from typing import List, Dict, Any, Optional

import numpy as np
from scipy import stats

from .models import SensitivitySweep, AnalysisResult
from .stats_engine import run_t_test, calculate_effect_size, apply_bonferroni_correction, frame_inference, aggregate_results

logger = logging.getLogger(__name__)


def run_sensitivity_sweep(
    gain_scores_embodied: List[float],
    gain_scores_static: List[float],
    thresholds: List[float]
) -> List[SensitivitySweep]:
    """
    Execute a sensitivity analysis by sweeping over significance thresholds.

    Args:
        gain_scores_embodied (List[float]): Gain scores for the embodied group.
        gain_scores_static (List[float]): Gain scores for the static group.
        thresholds (List[float]): List of thresholds to test.

    Returns:
        List[SensitivitySweep]: List of sweep results.
    """
    if len(gain_scores_embodied) + len(gain_scores_static) < 30:
        logger.warning("Insufficient data for robustness check (N < 30). Skipping sweep.")
        return []

    results = []
    for threshold in thresholds:
        # Run t-test
        t_stat, p_val = run_t_test(gain_scores_embodied, gain_scores_static)
        effect = calculate_effect_size(gain_scores_embodied, gain_scores_static)

        sweep_result = SensitivitySweep(
            threshold=threshold,
            effect_size=effect,
            p_value=p_val,
            sample_size=len(gain_scores_embodied) + len(gain_scores_static)
        )
        results.append(sweep_result)

    logger.info(f"Sensitivity sweep completed for {len(thresholds)} thresholds.")
    return results


def check_robustness_warning(sweep_results: List[SensitivitySweep], minimum_effect: float = 0.2) -> bool:
    """
    Check if the effect size drops below a substantively meaningful threshold
    at any point in the sweep.

    Args:
        sweep_results (List[SensitivitySweep]): Results from the sensitivity sweep.
        minimum_effect (float): The minimum substantively meaningful effect size.

    Returns:
        bool: True if robustness warning should be raised, False otherwise.
    """
    for result in sweep_results:
        if abs(result.effect_size) < minimum_effect:
            logger.warning(f"Robustness warning: Effect size {result.effect_size} dropped below {minimum_effect} at threshold {result.threshold}")
            return True
    return False


def aggregate_sweep_results(sweep_results: List[SensitivitySweep]) -> Dict[str, Any]:
    """
    Aggregate sweep results into a summary dictionary.

    Args:
        sweep_results (List[SensitivitySweep]): List of sweep results.

    Returns:
        Dict[str, Any]: Aggregated summary.
    """
    if not sweep_results:
        return {"sweep_data": [], "robustness_warning": True, "reason": "No sweep data available"}

    summary = {
        "sweep_data": [r.to_dict() for r in sweep_results],
        "robustness_warning": check_robustness_warning(sweep_results)
    }
    return summary


def aggregate_results_for_report(analysis_result: AnalysisResult, sweep_results: List[SensitivitySweep]) -> Dict[str, Any]:
    """
    Combine the main analysis result with sensitivity sweep results.

    Args:
        analysis_result (AnalysisResult): The primary analysis result.
        sweep_results (List[SensitivitySweep]): The sensitivity sweep results.

    Returns:
        Dict[str, Any]: Combined report dictionary.
    """
    report = analysis_result.to_dict()
    report["sensitivity_analysis"] = aggregate_sweep_results(sweep_results)
    return report
