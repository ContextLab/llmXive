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
    aggregate_sweep_results
)

logger = logging.getLogger(__name__)

def aggregate_and_write_results(
    processed_records: List[DatasetRecord],
    concept_definitions: List[str],
    thresholds: List[float],
    output_path: str
) -> AnalysisResult:
    """
    Aggregate all statistical results into an AnalysisResult object and write to JSON.

    This function performs the core aggregation logic for Task T026:
    1. Calculates gain scores for each record.
    2. Groups records by instruction_type (Embodied vs Static).
    3. Runs t-tests, effect size, power, collinearity checks.
    4. Runs sensitivity sweep if thresholds provided.
    5. Aggregates everything into an AnalysisResult object.
    6. Writes the result to a JSON file.

    Args:
        processed_records: List of DatasetRecord objects with gain scores.
        concept_definitions: List of concept names being tested.
        thresholds: List of significance thresholds for sensitivity sweep.
        output_path: Path to write the JSON results file.

    Returns:
        AnalysisResult object containing all aggregated statistics.
    """
    logger.info("Starting results aggregation...")

    # Group records by instruction type
    embodied_scores = []
    static_scores = []

    for record in processed_records:
        if record.instruction_type == "embodied":
            embodied_scores.append(record.post_test_score - record.pre_test_score)
        elif record.instruction_type == "static":
            static_scores.append(record.post_test_score - record.pre_test_score)

    if not embodied_scores or not static_scores:
        raise ValueError("Insufficient data: Both 'embodied' and 'static' groups must have records.")

    # Run primary statistical tests
    t_stat, p_val = run_t_test(embodied_scores, static_scores)
    effect_size = calculate_effect_size(embodied_scores, static_scores)
    ci_low, ci_high = calculate_confidence_interval(embodied_scores, static_scores, effect_size)
    bonferroni_alpha = apply_bonferroni_correction(0.05, len(concept_definitions))
    is_significant = p_val < bonferroni_alpha
    framing = frame_inference(t_stat, p_val, effect_size, is_significant)
    collinearity_diag = check_collinearity(processed_records)
    power = calculate_power(embodied_scores, static_scores, effect_size)

    # Run sensitivity sweep if thresholds provided
    sweep_results = []
    robustness_warning = False
    if thresholds:
        logger.info(f"Running sensitivity sweep with thresholds: {thresholds}")
        sweep_results = run_sensitivity_sweep(
            embodied_scores,
            static_scores,
            thresholds,
            concept_definitions
        )
        robustness_warning = check_robustness_warning(sweep_results)

    # Aggregate all results
    result = AnalysisResult(
        t_statistic=t_stat,
        p_value=p_val,
        effect_size=effect_size,
        confidence_interval=(ci_low, ci_high),
        bonferroni_alpha=bonferroni_alpha,
        is_significant=is_significant,
        inference_framing=framing,
        collinearity_diagnostics=collinearity_diag,
        power=power,
        underpowered=power < 0.80,
        sensitivity_sweep=sweep_results,
        robustness_warning=robustness_warning,
        sample_sizes={
            "embodied": len(embodied_scores),
            "static": len(static_scores)
        },
        concept_count=len(concept_definitions)
    )

    # Write to JSON
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Convert AnalysisResult to dict for JSON serialization
    result_dict = {
        "t_statistic": result.t_statistic,
        "p_value": result.p_value,
        "effect_size": result.effect_size,
        "confidence_interval": list(result.confidence_interval),
        "bonferroni_alpha": result.bonferroni_alpha,
        "is_significant": result.is_significant,
        "inference_framing": result.inference_framing,
        "collinearity_diagnostics": result.collinearity_diagnostics,
        "power": result.power,
        "underpowered": result.underpowered,
        "sensitivity_sweep": [
            {
                "threshold": s.threshold,
                "effect_size": s.effect_size,
                "is_significant": s.is_significant
            }
            for s in result.sensitivity_sweep
        ],
        "robustness_warning": result.robustness_warning,
        "sample_sizes": result.sample_sizes,
        "concept_count": result.concept_count
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, indent=2)

    logger.info(f"Results written to {output_path}")
    return result

def process_and_save_analysis(
    records: List[DatasetRecord],
    concepts: List[str],
    thresholds: List[float],
    output_dir: str
) -> AnalysisResult:
    """
    Convenience wrapper to process records and save analysis results.

    Args:
        records: List of DatasetRecord objects.
        concepts: List of concept names.
        thresholds: List of significance thresholds.
        output_dir: Directory to write results.

    Returns:
        AnalysisResult object.
    """
    output_path = Path(output_dir) / "results.json"
    return aggregate_and_write_results(records, concepts, thresholds, str(output_path))
