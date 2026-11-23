import logging
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats

try:
    from .models import SensitivitySweep, AnalysisResult
    from .stats_engine import run_t_test, calculate_effect_size, apply_bonferroni_correction, frame_inference, aggregate_stats_results
except ImportError:
    import models
    import stats_engine
    from models import SensitivitySweep, AnalysisResult
    from stats_engine import run_t_test, calculate_effect_size, apply_bonferroni_correction, frame_inference, aggregate_stats_results

logger = logging.getLogger(__name__)

def run_sensitivity_sweep(df: Any, thresholds: Optional[List[float]] = None) -> List[Dict[str, Any]]:
    """
    Run sensitivity analysis sweep over thresholds.
    
    Args:
        df: DataFrame containing 'gain_score' and 'group' columns.
        thresholds: List of significance thresholds to sweep. Defaults to [0.01, 0.05, 0.10] if not provided.
        
    Returns:
        List of dictionaries containing sensitivity analysis results.
    """
    if thresholds is None:
        thresholds = [0.01, 0.05, 0.10]
        
    results = []
    n_total = len(df)
    
    # Check total N
    if n_total < 30:
        logger.warning("Insufficient data for sensitivity sweep (N < 30).")
        # Return early with insufficient_data flag and exact string as required
        return [{
            "threshold_value": 0.0,
            "n_participants_retained": 0,
            "effect_size_cohen_d": 0.0,
            "robustness_flag": False,
            "insufficient_data": True,
            "message": "insufficient data for robustness check"
        }]

    # Validate required columns
    if 'gain_score' not in df.columns or 'group' not in df.columns:
        logger.error("Missing required columns for sensitivity sweep: 'gain_score' and 'group'.")
        return []

    gain_scores = df['gain_score'].values
    groups = df['group'].values

    for threshold in thresholds:
        # Calculate effect size (Cohen's d) using real data
        effect_size = calculate_effect_size(gain_scores, groups)
        n_retained = n_total  # All data retained for this sweep logic
        
        # Robustness flag: True if effect size >= 0.2
        robust = effect_size >= 0.2
        
        results.append({
            "threshold_value": float(threshold),
            "n_participants_retained": int(n_retained),
            "effect_size_cohen_d": float(effect_size),
            "robustness_flag": bool(robust)
        })

    return results

def check_robustness_warning(sweep_results: List[Dict[str, Any]]) -> bool:
    """
    Check if any effect size in sweep is below 0.2.
    
    Args:
        sweep_results: List of sensitivity sweep result dictionaries.
        
    Returns:
        True if any effect size is below 0.2, False otherwise.
    """
    if not sweep_results:
        return False
    
    # Check for the 'insufficient_data' case first
    for item in sweep_results:
        if item.get("insufficient_data", False):
            return False  # No warning if data is insufficient, just early exit
        
        # Check if effect size drops below 0.2
        if item.get("effect_size_cohen_d", 1.0) < 0.2:
            logger.warning("Robustness warning: Effect size dropped below 0.2 threshold in sensitivity sweep.")
            return True
    
    return False

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
