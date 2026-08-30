import json
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import logging

logger = logging.getLogger('sensitivity')

class SensitivityError(Exception):
    """Custom exception for sensitivity analysis errors."""
    pass

def load_statistical_results() -> Dict[str, Any]:
    """Load statistical results from JSON."""
    path = Path('artifacts/statistical_results.json')
    if not path.exists():
        raise SensitivityError(f"Statistical results not found: {path}")
    
    with open(path, 'r') as f:
        return json.load(f)

def calculate_quasi_thermal_ratio(results: Dict[str, Any]) -> Dict[str, float]:
    """Calculate quasi-thermal classification ratios."""
    ratios = {}
    for key, data in results.items():
        # Ratio of accepted to total tests
        accepted = (not data['reject_ks_fdr']) + (not data['reject_chi2'])
        total = 2
        ratios[key] = accepted / total
    return ratios

def sweep_alpha_thresholds(results: Dict[str, Any], thresholds: List[float]) -> Dict[str, Dict[float, bool]]:
    """Sweep over alpha thresholds and record rejection decisions."""
    sweep_results = {}
    
    for key, data in results.items():
        sweep_results[key] = {}
        for alpha in thresholds:
            # Re-evaluate rejection based on new alpha
            reject = data['ks_p_value'] < alpha
            sweep_results[key][alpha] = reject
    
    return sweep_results

def sweep_quasi_thermal_boundaries(results: Dict[str, Any], boundaries: List[float]) -> Dict[str, Dict[float, float]]:
    """Sweep over energy-ratio boundaries."""
    sweep_results = {}
    
    for key, data in results.items():
        sweep_results[key] = {}
        for boundary in boundaries:
            # Classification rate based on boundary
            ratio = calculate_quasi_thermal_ratio({key: data})[key]
            classified = ratio >= boundary
            sweep_results[key][boundary] = float(classified)
    
    return sweep_results

def verify_robustness(results: Dict[str, Any], thresholds: List[float]) -> Dict[str, Any]:
    """Verify robustness across thresholds for primary bin."""
    # Primary bin: median frequency
    bins = list(results.keys())
    if not bins:
        return {'stable_across_thresholds': False, 'decisions': {}}
    
    # Sort by frequency value
    freqs = [float(k.split('_')[0]) for k in bins]
    median_idx = np.argsort(freqs)[len(freqs)//2]
    primary_bin = bins[median_idx]
    
    decisions = {}
    for alpha in thresholds:
        p_val = results[primary_bin]['ks_p_value']
        decisions[alpha] = p_val < alpha
    
    # Check stability
    unique_decisions = set(decisions.values())
    stable = len(unique_decisions) == 1
    
    return {
        'stable_across_thresholds': stable,
        'decisions': decisions,
        'primary_bin': primary_bin
    }

def perform_leave_one_out_cv(results: Dict[str, Any]) -> Dict[str, Any]:
    """Perform leave-one-out cross-validation on bins."""
    bins = list(results.keys())
    cv_results = {}
    
    for i, left_out in enumerate(bins):
        subset = {k: v for j, (k, v) in enumerate(results.items()) if j != i}
        # Calculate rejection rate on subset
        rejections = sum(1 for v in subset.values() if v['reject_ks_fdr'])
        cv_results[left_out] = {
            'rejection_rate': rejections / len(subset) if subset else 0,
            'n_bins': len(subset)
        }
    
    return cv_results

def run_sensitivity_analysis(results: Dict[str, Any], thresholds: List[float], boundaries: List[float]) -> Dict[str, Any]:
    """Run full sensitivity analysis."""
    alpha_sweep = sweep_alpha_thresholds(results, thresholds)
    boundary_sweep = sweep_quasi_thermal_boundaries(results, boundaries)
    robustness = verify_robustness(results, thresholds)
    cv_results = perform_leave_one_out_cv(results)
    
    return {
        'alpha_sweep': alpha_sweep,
        'boundary_sweep': boundary_sweep,
        'robustness': robustness,
        'cv_results': cv_results
    }

def main(args=None):
    """Main entry point for sensitivity analysis."""
    if args is None:
        parser = argparse.ArgumentParser(description='Sensitivity Analysis')
        parser.add_argument('--thresholds', type=str, default='0.01,0.05,0.10', help='Comma-separated alpha thresholds')
        parser.add_argument('--verbose', action='store_true', help='Verbose logging')
        args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        thresholds = [float(t) for t in args.thresholds.split(',')]
        boundaries = [0.01, 0.05, 0.10]
        
        results = load_statistical_results()
        analysis = run_sensitivity_analysis(results, thresholds, boundaries)
        
        # Write report
        output_path = Path('artifacts/sensitivity_analysis_report.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Sensitivity report written to {output_path}")
        
        # Write stability check
        stability_path = Path('artifacts/stability_check.json')
        with open(stability_path, 'w') as f:
            json.dump(analysis['robustness'], f, indent=2)
        
        logger.info(f"Stability check written to {stability_path}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
