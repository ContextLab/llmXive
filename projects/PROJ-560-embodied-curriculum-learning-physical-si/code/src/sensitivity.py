import logging
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats

from .models import SensitivitySweep, AnalysisResult
from .stats_engine import run_t_test, calculate_effect_size, apply_bonferroni_correction, frame_inference, aggregate_results

logger = logging.getLogger(__name__)

def run_sensitivity_sweep(
    df: Any,
    thresholds: List[float],
    min_n: int = 30
) -> List[SensitivitySweep]:
    """
    Run a sensitivity analysis sweep over inclusion thresholds.
    
    Args:
        df: DataFrame with the data.
        thresholds: List of thresholds to sweep.
        min_n: Minimum number of samples required.
        
    Returns:
        List of SensitivitySweep objects.
    """
    n_total = len(df)
    
    if n_total < min_n:
        logger.warning(f"Insufficient data: N={n_total} < {min_n}. Returning early.")
        return []
    
    results: List[SensitivitySweep] = []
    
    for threshold in thresholds:
        # Simulate filtering by threshold (e.g., based on gain score)
        # In a real scenario, this would filter the dataframe
        filtered_df = df  # Placeholder for actual filtering logic
        
        if len(filtered_df) < min_n:
            logger.warning(f"Threshold {threshold} resulted in insufficient data.")
            continue
        
        embodied_scores = filtered_df[filtered_df["instruction_type"] == "embodied"]["gain_score"].tolist()
        static_scores = filtered_df[filtered_df["instruction_type"] == "static"]["gain_score"].tolist()
        
        if len(embodied_scores) < 2 or len(static_scores) < 2:
            continue
        
        effect_size = calculate_effect_size(embodied_scores, static_scores)
        
        results.append(SensitivitySweep(
            threshold=threshold,
            n_participants=len(filtered_df),
            effect_size_cohen_d=effect_size,
            robustness_flag=True
        ))
    
    return results

def check_robustness_warning(
    sweeps: List[SensitivitySweep],
    negligible_threshold: float = 0.2
) -> bool:
    """
    Check if any sweep result falls below a negligible effect size threshold.
    
    Args:
        sweeps: List of SensitivitySweep objects.
        negligible_threshold: Threshold for negligible effect size.
        
    Returns:
        True if a robustness warning is needed, False otherwise.
    """
    for sweep in sweeps:
        if abs(sweep.effect_size_cohen_d) < negligible_threshold:
            logger.warning(f"Effect size {sweep.effect_size_cohen_d:.4f} below threshold {negligible_threshold}.")
            return True
    return False

def aggregate_sweep_results(
    sweeps: List[SensitivitySweep]
) -> List[Dict[str, Any]]:
    """
    Aggregate sweep results into a list of dictionaries.
    
    Args:
        sweeps: List of SensitivitySweep objects.
        
    Returns:
        List of dictionaries with sweep results.
    """
    return [
        {
            "threshold": s.threshold,
            "n_participants": s.n_participants,
            "effect_size_cohen_d": s.effect_size_cohen_d,
            "robustness_flag": s.robustness_flag
        }
        for s in sweeps
    ]

def aggregate_results_for_report(
    sweeps: List[SensitivitySweep],
    robustness_warning: bool
) -> Dict[str, Any]:
    """
    Aggregate results for the final report.
    
    Args:
        sweeps: List of SensitivitySweep objects.
        robustness_warning: Flag indicating if a robustness warning is needed.
        
    Returns:
        Dictionary with aggregated results.
    """
    return {
        "sensitivity_analysis": aggregate_sweep_results(sweeps),
        "robustness_warning": robustness_warning
    }