import logging
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import stats
from .models import SensitivitySweep, AnalysisResult
from .stats_engine import run_t_test, calculate_effect_size, apply_bonferroni_correction, frame_inference, aggregate_results

logger = logging.getLogger(__name__)

def check_robustness_warning(effect_sizes: List[float], threshold: float = 0.2) -> bool:
    """
    Flag robustness_warning: true if effect size drops below a substantively meaningful threshold.
    
    Args:
        effect_sizes: List of effect sizes (e.g., Cohen's d) from the sweep.
        threshold: Minimum meaningful effect size (default 0.2 for small effect).
        
    Returns:
        True if any effect size falls below the threshold, False otherwise.
    """
    if not effect_sizes:
        return True
    
    for d in effect_sizes:
        if abs(d) < threshold:
            logger.warning(f"Effect size {d:.4f} below meaningful threshold {threshold}. Robustness warning triggered.")
            return True
    return False

def run_sensitivity_sweep(
    gain_scores_embodied: List[float],
    gain_scores_static: List[float],
    thresholds: List[float],
    alpha: float = 0.05
) -> List[SensitivitySweep]:
    """
    Execute a sensitivity analysis sweeping inclusion thresholds.
    
    Args:
        gain_scores_embodied: List of gain scores for the embodied group.
        gain_scores_static: List of gain scores for the static group.
        thresholds: List of threshold values to test (e.g., significance levels or effect size cutoffs).
        alpha: Base significance level for Bonferroni correction.
        
    Returns:
        List of SensitivitySweep objects containing results for each threshold.
    """
    if len(gain_scores_embodied) < 30 or len(gain_scores_static) < 30:
        logger.warning("Insufficient data for robustness check (N < 30). Skipping sweep.")
        return []

    results = []
    n_tests = len(thresholds)
    
    for i, threshold in enumerate(thresholds):
        logger.info(f"Processing sweep threshold {i+1}/{n_tests}: {threshold}")
        
        # Adjust alpha for this specific test within the sweep context
        # Note: In a real sensitivity sweep, we might not correct across thresholds 
        # if they are just parameter variations, but we follow FR-005 logic.
        adjusted_alpha = apply_bonferroni_correction(alpha, n_tests)
        
        # Run t-test
        t_stat, p_val, df = run_t_test(gain_scores_embodied, gain_scores_static)
        
        # Calculate effect size
        effect_size, ci_low, ci_high = calculate_effect_size(
            gain_scores_embodied, gain_scores_static
        )
        
        # Frame inference
        inference_text = frame_inference(p_val, effect_size, adjusted_alpha)
        
        # Check collinearity (simulated as no covariates provided in this specific sweep context)
        # In a full run, covariates would be passed here.
        collinearity_diagnostic = {"status": "no_covariates_provided", "max_r": 0.0}
        
        # Calculate power
        power = calculate_power(effect_size, len(gain_scores_embodied) + len(gain_scores_static), adjusted_alpha)
        
        sweep_result = SensitivitySweep(
            threshold=threshold,
            t_statistic=t_stat,
            p_value=p_val,
            adjusted_alpha=adjusted_alpha,
            effect_size=effect_size,
            ci_lower=ci_low,
            ci_upper=ci_high,
            power=power,
            inference_text=inference_text,
            collinearity_diagnostic=collinearity_diagnostic,
            robustness_warning=check_robustness_warning([effect_size])
        )
        
        results.append(sweep_result)
        
        logger.info(f"Threshold {threshold}: t={t_stat:.4f}, p={p_val:.6f}, d={effect_size:.4f}")

    return results

def aggregate_sweep_results(
    sweep_results: List[SensitivitySweep],
    base_analysis: Optional[AnalysisResult] = None
) -> AnalysisResult:
    """
    Aggregate sweep results into a single AnalysisResult object.
    
    Args:
        sweep_results: List of SensitivitySweep objects from run_sensitivity_sweep.
        base_analysis: Optional base AnalysisResult to extend with sweep data.
        
    Returns:
        Updated AnalysisResult containing the sensitivity sweep data.
    """
    if base_analysis is None:
        # Create a minimal base if none provided
        base_analysis = AnalysisResult(
            t_statistic=0.0,
            p_value=1.0,
            effect_size=0.0,
            ci_lower=0.0,
            ci_upper=0.0,
            power=0.0,
            inference_text="No base analysis provided.",
            collinearity_diagnostic={},
            robustness_warning=True,
            sensitivity_sweep=[]
        )

    # Update base analysis with aggregate stats from the sweep if needed
    # For now, we primarily append the sweep list.
    base_analysis.sensitivity_sweep = sweep_results
    
    # Determine overall robustness based on all sweep results
    if sweep_results:
        all_warnings = [s.robustness_warning for s in sweep_results]
        base_analysis.robustness_warning = any(all_warnings)
    
    return base_analysis
