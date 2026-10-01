import logging
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats

try:
    from .models import SensitivitySweep, AnalysisResult
    from .stats_engine import run_t_test, calculate_effect_size, apply_bonferroni_correction, frame_inference, aggregate_results
except ImportError:
    import models
    import stats_engine
    from models import SensitivitySweep, AnalysisResult
    from stats_engine import run_t_test, calculate_effect_size, apply_bonferroni_correction, frame_inference, aggregate_results

logger = logging.getLogger(__name__)

def run_sensitivity_sweep(df: Any, thresholds: List[float]) -> List[Dict[str, Any]]:
    """
    Run sensitivity analysis sweep over thresholds.
    """
    results = []
    n_total = len(df)
    
    if n_total < 30:
        logger.warning("Insufficient data for sensitivity sweep (N < 30).")
        return []

    # Assuming df has 'gain_score' and 'group' columns
    if 'gain_score' not in df.columns or 'group' not in df.columns:
        logger.error("Missing required columns for sensitivity sweep.")
        return []

    gain_scores = df['gain_score'].values
    groups = df['group'].values

    for threshold in thresholds:
        # In a real scenario, threshold might filter data or adjust significance
        # Here we simulate by retaining all data and calculating effect size
        # A real implementation would filter based on some criterion related to threshold
        
        # For this MVP, we just calculate effect size and flag robustness
        effect_size = calculate_effect_size(gain_scores, groups)
        n_retained = n_total # Assume all retained for simplicity
        
        robust = effect_size >= 0.2
        
        results.append({
            "threshold_value": threshold,
            "n_participants_retained": n_retained,
            "effect_size_cohen_d": effect_size,
            "robustness_flag": robust
        })

    return results

def check_robustness_warning(sweep_results: List[Dict[str, Any]]) -> bool:
    """
    Check if any effect size in sweep is below 0.2.
    """
    return any(item.get("effect_size_cohen_d", 1.0) < 0.2 for item in sweep_results)

def aggregate_sweep_results(sweep_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate sweep results for reporting."""
    return {
        "sweep_count": len(sweep_results),
        "results": sweep_results
    }

def aggregate_results_for_report(analysis_result: Dict[str, Any], sweep_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge analysis and sweep results."""
    report = analysis_result.copy()
    report["sensitivity_analysis"] = sweep_results
    report["robustness_warning"] = check_robustness_warning(sweep_results)
    return report
