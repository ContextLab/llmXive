"""
Sensitivity Analysis Module for Embodied Curriculum Learning.

This module provides functions for running sensitivity sweeps across different
inclusion thresholds to demonstrate the robustness of the headline effect size.
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats

from .models import SensitivitySweep, AnalysisResult
from .stats_engine import run_t_test, calculate_effect_size, apply_bonferroni_correction, frame_inference, aggregate_results


def run_sensitivity_sweep(
    records: List[Any],
    thresholds: List[float],
    concept_name: str = "math_reasoning"
) -> List[SensitivitySweep]:
    """
    Run a sensitivity analysis sweep across multiple thresholds.

    Args:
        records: List of DatasetRecord objects.
        thresholds: List of threshold values to test.
        concept_name: Name of the concept being analyzed.

    Returns:
        List of SensitivitySweep objects for each threshold.
    """
    logger = logging.getLogger(__name__)
    n_total = len(records)

    # Check total N
    if n_total < 30:
        logger.warning(f"Insufficient data for sensitivity sweep: N={n_total} < 30")
        return []

    sweep_results = []

    for threshold in thresholds:
        # Filter records based on threshold (example: filter by absolute gain)
        # This is a placeholder logic; actual filtering depends on the use case
        filtered_records = [
            r for r in records
            if r.gain_score is not None and abs(r.gain_score) >= threshold
        ]

        if len(filtered_records) < 30:
            logger.warning(f"Threshold {threshold} results in insufficient data: N={len(filtered_records)}")
            continue

        # Split into groups
        embodied = [r.gain_score for r in filtered_records if r.instruction_type == "embodied"]
        static = [r.gain_score for r in filtered_records if r.instruction_type == "static"]

        if len(embodied) < 2 or len(static) < 2:
            continue

        t_stat, p_val = run_t_test(embodied, static)
        effect_size = calculate_effect_size(embodied, static)
        bonf_p = apply_bonferroni_correction(p_val, len(thresholds))
        is_sig = bonf_p < 0.05

        sweep_results.append(SensitivitySweep(
            threshold=threshold,
            effect_size=effect_size,
            is_significant=is_sig,
            sample_size=len(filtered_records)
        ))

    logger.info(f"Sensitivity sweep completed. {len(sweep_results)} valid thresholds.")
    return sweep_results


def check_robustness_warning(
    sweep_results: List[SensitivitySweep],
    effect_size_threshold: float = 0.5
) -> bool:
    """
    Check if the effect size drops below a predefined threshold at any point.

    Args:
        sweep_results: List of SensitivitySweep objects.
        effect_size_threshold: Minimum acceptable effect size.

    Returns:
        True if a robustness warning should be flagged, False otherwise.
    """
    for result in sweep_results:
        if abs(result.effect_size) < effect_size_threshold:
            return True
    return False


def aggregate_sweep_results(
    sweep_results: List[SensitivitySweep]
) -> Dict[str, Any]:
    """
    Aggregate sweep results into a summary dictionary.

    Args:
        sweep_results: List of SensitivitySweep objects.

    Returns:
        Dictionary with aggregated sweep information.
    """
    if not sweep_results:
        return {"sweep_results": [], "robustness_warning": False}

    data = [r.to_dict() for r in sweep_results]
    robustness_warning = check_robustness_warning(sweep_results)

    return {
        "sweep_results": data,
        "robustness_warning": robustness_warning,
        "n_thresholds_tested": len(sweep_results)
    }


def aggregate_results_for_report(
    main_result: AnalysisResult,
    sweep_results: List[SensitivitySweep]
) -> Dict[str, Any]:
    """
    Combine main analysis result with sensitivity sweep results.

    Args:
        main_result: The primary AnalysisResult object.
        sweep_results: List of SensitivitySweep objects.

    Returns:
        Dictionary containing the full report.
    """
    sweep_summary = aggregate_sweep_results(sweep_results)

    return {
        "main_analysis": main_result.to_dict(),
        "sensitivity_analysis": sweep_summary
    }
