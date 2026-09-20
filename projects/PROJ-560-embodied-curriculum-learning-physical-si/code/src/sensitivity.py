import logging
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats
from .models import SensitivitySweep, AnalysisResult
from .stats_engine import run_t_test, calculate_effect_size, apply_bonferroni_correction, frame_inference, aggregate_results


logger = logging.getLogger(__name__)


def run_sensitivity_sweep(
    records: List[Any], 
    thresholds: List[float]
) -> List[SensitivitySweep]:
    """
    Run a sensitivity sweep over significance thresholds.
    
    Args:
        records: List of dataset records.
        thresholds: List of significance thresholds to test.
        
    Returns:
        List of SensitivitySweep objects.
    """
    if len(records) < 30:
        logger.warning("Insufficient data for sensitivity sweep (N < 30).")
        return []
        
    groups: Dict[str, List[float]] = {}
    for r in records:
        if r.instruction_type not in groups:
            groups[r.instruction_type] = []
        gain = r.post_test_score - r.pre_test_score
        groups[r.instruction_type].append(gain)
        
    if len(groups) < 2:
        return []
        
    g1_keys = list(groups.keys())
    g1 = groups[g1_keys[0]]
    g2 = groups[g1_keys[1]]
    
    _, p_val = run_t_test(g1, g2)
    effect = calculate_effect_size(g1, g2)
    
    results = []
    for thresh in thresholds:
        significant = p_val < thresh
        results.append(SensitivitySweep(
            threshold=thresh,
            effect_size=effect,
            significant=significant
        ))
        
    logger.info(f"Sensitivity sweep completed with {len(results)} thresholds.")
    return results


def check_robustness_warning(sweep_results: List[SensitivitySweep]) -> bool:
    """
    Check if the effect size drops below a negligible threshold.
    
    Args:
        sweep_results: List of sweep results.
        
    Returns:
        True if robustness warning is triggered.
    """
    negligible_threshold = 0.2
    for res in sweep_results:
        if abs(res.effect_size) < negligible_threshold and res.significant:
            logger.warning("Effect size is negligible but significant at some threshold.")
            return True
    return False


def aggregate_sweep_results(results: List[SensitivitySweep]) -> List[Dict[str, Any]]:
    """
    Aggregate sweep results for reporting.
    
    Args:
        results: List of SensitivitySweep objects.
        
    Returns:
        List of dictionaries for JSON serialization.
    """
    return [r.to_dict() for r in results]


def aggregate_results_for_report(sweep_results: List[SensitivitySweep]) -> List[Dict[str, Any]]:
    """
    Prepare sweep results for the main report.
    
    Args:
        sweep_results: List of SensitivitySweep objects.
        
    Returns:
        List of dictionaries.
    """
    return aggregate_sweep_results(sweep_results)
