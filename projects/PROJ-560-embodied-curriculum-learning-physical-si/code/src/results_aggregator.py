"""
Results aggregation module.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from .models import AnalysisResult, DatasetRecord, SensitivitySweep
from .stats_engine import (
    run_t_test, calculate_effect_size, calculate_confidence_interval,
    apply_bonferroni_correction, frame_inference, check_collinearity,
    calculate_power, aggregate_results
)
from .sensitivity import run_sensitivity_sweep, aggregate_results_for_report

logger = logging.getLogger(__name__)


def aggregate_and_write_results(
    records: List[DatasetRecord],
    output_path: str,
    sweep_thresholds: Optional[List[float]] = None
) -> None:
    """
    Aggregate analysis results and write to a JSON file.

    Args:
        records (List[DatasetRecord]): List of dataset records.
        output_path (str): Path to the output JSON file.
        sweep_thresholds (Optional[List[float]]): Thresholds for sensitivity sweep.
    """
    embodied = [r.post_test_score - r.pre_test_score for r in records if r.instruction_type == "embodied"]
    static = [r.post_test_score - r.pre_test_score for r in records if r.instruction_type == "static"]

    if not embodied or not static:
        logger.error("Missing groups for analysis.")
        return

    t_stat, p_val = run_t_test(embodied, static)
    effect = calculate_effect_size(embodied, static)
    ci = calculate_confidence_interval(embodied, static)
    power = calculate_power(embodied, static)

    caveats = frame_inference(effect, p_val, [])
    collinearity = check_collinearity({"embodied": embodied, "static": static})

    sweep_results = []
    if sweep_thresholds:
        sweep_results = run_sensitivity_sweep(embodied, static, sweep_thresholds)

    robustness_warning = None
    if sweep_results:
        from .sensitivity import check_robustness_warning
        robustness_warning = check_robustness_warning(sweep_results)

    result = aggregate_results(t_stat, p_val, effect, ci, caveats, power, collinearity, robustness_warning)

    report = aggregate_results_for_report(result, sweep_results)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Results aggregated and written to {output_path}")


def process_and_save_analysis(
    records: List[DatasetRecord],
    output_path: str,
    sweep_thresholds: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Process records, run analysis, and save results.

    Args:
        records (List[DatasetRecord]): Input records.
        output_path (str): Output path.
        sweep_thresholds (Optional[List[float]]): Sweep thresholds.

    Returns:
        Dict[str, Any]: The generated report.
    """
    aggregate_and_write_results(records, output_path, sweep_thresholds)
    # Re-load for return (inefficient but safe for this context)
    with open(output_path, 'r', encoding='utf-8') as f:
        return json.load(f)
