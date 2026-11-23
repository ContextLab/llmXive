import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from .models import AnalysisResult, DatasetRecord, SensitivitySweep
from .stats_engine import (
    aggregate_stats_results,
    write_analysis_results,
    run_ancova,
    run_t_test,
    calculate_effect_size,
    calculate_confidence_interval,
    apply_bonferroni_correction,
    check_collinearity,
    calculate_power,
    frame_inference
)
import pandas as pd

logger = logging.getLogger(__name__)

def aggregate_and_write_results(
    df: pd.DataFrame,
    output_path: str,
    sensitivity_sweeps: Optional[List[SensitivitySweep]] = None
) -> Dict[str, Any]:
    """
    Aggregate statistical results and write to a JSON file.
    
    Args:
        df: DataFrame with the data.
        output_path: Path to the output JSON file.
        sensitivity_sweeps: Optional list of sensitivity sweep results.
        
    Returns:
        Dictionary of aggregated results.
    """
    # Prepare data for ANCOVA
    ancova_result = run_ancova(
        df=df,
        dependent_var="gain_score",
        factor_var="instruction_type",
        covariate_var="pre_test_score"
    )
    
    # Prepare data for t-test
    embodied_scores = df[df["instruction_type"] == "embodied"]["gain_score"].tolist()
    static_scores = df[df["instruction_type"] == "static"]["gain_score"].tolist()
    
    t_stat, p_val = run_t_test(embodied_scores, static_scores)
    
    # Effect size
    effect_size = calculate_effect_size(embodied_scores, static_scores)
    
    # Confidence interval
    ci = calculate_confidence_interval(
        effect_size,
        len(embodied_scores),
        len(static_scores)
    )
    
    # Power
    power = calculate_power(effect_size, len(embodied_scores), len(static_scores))
    
    # Collinearity
    collinearity = check_collinearity(df, ["pre_test_score", "gain_score"])
    
    # Framing
    inference_framing = frame_inference({})
    
    # Aggregate
    results = aggregate_stats_results(
        ancova_result=ancova_result,
        t_test_result=(t_stat, p_val),
        effect_size=effect_size,
        confidence_interval=ci,
        power=power,
        collinearity=collinearity,
        inference_framing=inference_framing
    )
    
    # Add sensitivity sweeps if provided
    if sensitivity_sweeps:
        results["sensitivity_analysis"] = [
            {
                "threshold": s.threshold,
                "n_participants": s.n_participants,
                "effect_size_cohen_d": s.effect_size_cohen_d,
                "robustness_flag": s.robustness_flag
            }
            for s in sensitivity_sweeps
        ]
    
    # Write results
    write_analysis_results(results, output_path)
    
    return results

def process_and_save_analysis(
    records: List[DatasetRecord],
    output_path: str,
    sensitivity_sweeps: Optional[List[SensitivitySweep]] = None
) -> Dict[str, Any]:
    """
    Process dataset records and save analysis results.
    
    Args:
        records: List of DatasetRecord objects.
        output_path: Path to the output JSON file.
        sensitivity_sweeps: Optional list of sensitivity sweep results.
        
    Returns:
        Dictionary of results.
    """
    df = pd.DataFrame([
        {
            "pre_test_score": r.pre_test_score,
            "post_test_score": r.post_test_score,
            "instruction_type": r.instruction_type,
            "gain_score": getattr(r, "gain_score", r.post_test_score - r.pre_test_score)
        }
        for r in records
    ])
    
    return aggregate_and_write_results(df, output_path, sensitivity_sweeps)