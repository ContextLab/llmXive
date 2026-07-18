"""
Results Aggregation Module for Embodied Curriculum Learning.

This module aggregates statistical results from the analysis engine and
sensitivity sweep, then writes the final report to a JSON file.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from .models import AnalysisResult, DatasetRecord, SensitivitySweep
from .stats_engine import (
    run_t_test,
    calculate_effect_size,
    calculate_confidence_interval,
    apply_bonferroni_correction,
    frame_inference,
    check_collinearity,
    calculate_power,
    aggregate_results
)
from .sensitivity import (
    run_sensitivity_sweep,
    check_robustness_warning,
    aggregate_sweep_results,
    aggregate_results_for_report
)


def process_and_save_analysis(
    records: List[DatasetRecord],
    output_path: str,
    sweep_thresholds: List[float]
) -> AnalysisResult:
    """
    Process records, run analysis and sensitivity sweep, and save results.

    Args:
        records: List of DatasetRecord objects.
        output_path: Path to write the JSON results file.
        sweep_thresholds: List of thresholds for sensitivity analysis.

    Returns:
        The main AnalysisResult object.
    """
    logger = logging.getLogger(__name__)

    # Group by instruction type
    embodied_gain = [r.gain_score for r in records if r.instruction_type == "embodied" and r.gain_score is not None]
    static_gain = [r.gain_score for r in records if r.instruction_type == "static" and r.gain_score is not None]

    if not embodied_gain or not static_gain:
        raise ValueError("Insufficient data: missing embodied or static group.")

    # Run main analysis
    main_result = aggregate_results(
        embodied_gain,
        static_gain,
        concept_name="math_reasoning",
        n_tests=len(sweep_thresholds)
    )

    # Run sensitivity sweep
    sweep_results = run_sensitivity_sweep(records, sweep_thresholds)

    # Aggregate for report
    report = aggregate_results_for_report(main_result, sweep_results)

    # Write to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Results written to {output_path}")

    return main_result


def aggregate_and_write_results(
    results: List[AnalysisResult],
    output_path: str
) -> None:
    """
    Aggregate multiple analysis results and write to a JSON file.

    Args:
        results: List of AnalysisResult objects.
        output_path: Path to write the JSON results file.
    """
    logger = logging.getLogger(__name__)

    data = [r.to_dict() for r in results]

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Wrote {len(results)} results to {output_path}")
