"""
Sensitivity analysis module.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)

class SensitivityError(Exception):
    """Custom exception for sensitivity errors."""
    pass

def load_statistical_results() -> List[Dict[str, Any]]:
    """Load statistical results from JSON."""
    path = 'artifacts/statistical_results.json'
    if not Path(path).exists():
        raise SensitivityError(f"Statistical results file {path} not found.")
    with open(path, 'r') as f:
        return json.load(f)

def calculate_quasi_thermal_ratio(ks_p: float, chi2_p: float, alpha: float) -> float:
    """Calculate quasi-thermal ratio based on p-values."""
    # Simple heuristic: 1.0 if both pass, 0.0 if both fail, linear interpolation
    pass_ks = ks_p >= alpha
    pass_chi2 = chi2_p >= alpha
    if pass_ks and pass_chi2:
        return 1.0
    if not pass_ks and not pass_chi2:
        return 0.0
    return 0.5

def sweep_alpha_thresholds(results: List[Dict], thresholds: List[float]) -> Dict[str, Any]:
    """Sweep significance thresholds and record rejection counts."""
    report = {}
    for thresh in thresholds:
        reject_count = 0
        for r in results:
            if r['ks_p_value'] < thresh or r['chi2_p_value'] < thresh:
                reject_count += 1
        report[str(thresh)] = {
            'threshold': thresh,
            'rejection_count': reject_count,
            'total_tests': len(results)
        }
    return report

def sweep_quasi_thermal_boundaries(results: List[Dict], boundaries: List[float]) -> Dict[str, Any]:
    """Sweep quasi-thermal energy ratio boundaries."""
    report = {}
    for bound in boundaries:
        # Logic to classify based on ratio deviation from 1.0
        # Simplified: count how many are within bound of 1.0
        count = 0
        for r in results:
            # Assume ratio is derived from p-values or a specific metric
            # Here we mock a ratio based on p-value proximity to alpha
            # In real implementation, use actual calculated ratio
            ratio = 1.0 # Placeholder
            if abs(ratio - 1.0) <= bound:
                count += 1
        report[str(bound)] = {
            'boundary': bound,
            'classification_rate': count / len(results) if results else 0.0
        }
    return report

def verify_robustness(results: List[Dict], thresholds: List[float]) -> Dict[str, bool]:
    """Verify robustness across thresholds."""
    decisions = []
    for thresh in thresholds:
        reject_count = sum(1 for r in results if r['ks_p_value'] < thresh or r['chi2_p_value'] < thresh)
        decisions.append(reject_count > 0) # Primary decision: any rejection?
    stable = all(d == decisions[0] for d in decisions) if decisions else False
    return {
        'stable_across_thresholds': stable,
        'decisions': {str(t): d for t, d in zip(thresholds, decisions)}
    }

def run_sensitivity_analysis(thresholds: Optional[List[float]] = None, boundaries: Optional[List[float]] = None):
    """Run full sensitivity analysis."""
    if thresholds is None:
        thresholds = [0.01, 0.05, 0.10]
    if boundaries is None:
        boundaries = [0.01, 0.05, 0.10]
    
    results = load_statistical_results()
    
    alpha_sweep = sweep_alpha_thresholds(results, thresholds)
    boundary_sweep = sweep_quasi_thermal_boundaries(results, boundaries)
    robustness = verify_robustness(results, thresholds)
    
    return {
        'alpha_sweep': alpha_sweep,
        'boundary_sweep': boundary_sweep,
        'robustness': robustness
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Sensitivity Module')
    parser.add_argument('--config', type=str, default='data/config.yaml')
    parser.add_argument('--thresholds', type=str, default='0.01,0.05,0.10')
    args = parser.parse_args()
    
    thresh_list = [float(x) for x in args.thresholds.split(',')]
    report = run_sensitivity_analysis(thresholds=thresh_list)
    
    output_path = 'artifacts/sensitivity_analysis_report.json'
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Sensitivity report written to {output_path}")
