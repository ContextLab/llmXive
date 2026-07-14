import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils import setup_logging, pin_random_seed

logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Optional[List[Dict[str, Any]]]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Baseline metrics file not found: {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            # Handle both list and dict with 'datasets' key
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'datasets' in data:
                return data['datasets']
            else:
                logger.warning(f"Unexpected baseline metrics structure in {filepath}")
                return []
    except Exception as e:
        logger.error(f"Error loading baseline metrics: {e}")
        return None

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Optional[List[Dict[str, Any]]]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Cleaned metrics file not found: {filepath}")
        return None
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'datasets' in data:
                return data['datasets']
            else:
                logger.warning(f"Unexpected cleaned metrics structure in {filepath}")
                return []
    except Exception as e:
        logger.error(f"Error loading cleaned metrics: {e}")
        return None

def bin_dataset_size(n_rows: int) -> str:
    """
    Bin dataset size into categories:
    - 'small': n < 50
    - 'medium': 50 <= n <= 200
    - 'large': n > 200
    """
    if n_rows < 50:
        return 'small'
    elif n_rows <= 200:
        return 'medium'
    else:
        return 'large'

def analyze_size_bin(
    baseline_entries: List[Dict[str, Any]],
    cleaned_entries: List[Dict[str, Any]],
    bin_name: str
) -> Dict[str, Any]:
    """
    Analyze metrics for a specific dataset size bin.
    Returns statistics on p-value shifts, CI width changes, and effect sizes.
    """
    bin_entries = []

    # Combine baseline and cleaned entries
    for base_entry in baseline_entries:
        dataset_name = base_entry.get('dataset_name') or base_entry.get('name')
        n_rows = base_entry.get('dataset_size') or base_entry.get('n_rows') or 0
        
        if bin_dataset_size(n_rows) == bin_name:
            # Find matching cleaned entry
            cleaned_entry = None
            for clean_entry in cleaned_entries:
                if clean_entry.get('dataset_name') == dataset_name:
                    cleaned_entry = clean_entry
                    break
            
            bin_entries.append({
                'dataset_name': dataset_name,
                'size': n_rows,
                'baseline': base_entry,
                'cleaned': cleaned_entry
            })

    result = {
        'bin': bin_name,
        'count': len(bin_entries),
        'p_value_shifts': [],
        'ci_width_changes': [],
        'effect_size_deltas': []
    }

    if len(bin_entries) == 0:
        logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' has 0 datasets.")
        return result

    for entry in bin_entries:
        base_data = entry['baseline']
        clean_data = entry['cleaned']

        if not clean_data:
            continue

        # Extract p-values
        base_p = None
        clean_p = None

        # Handle different structures
        if 'analysis' in base_data and 't_test' in base_data['analysis']:
            base_p = base_data['analysis']['t_test'].get('p_value')
        elif 't_test' in base_data:
            base_p = base_data['t_test'].get('p_value')
        
        if 'analysis' in clean_data and 't_test' in clean_data['analysis']:
            clean_p = clean_data['analysis']['t_test'].get('p_value')
        elif 't_test' in clean_data:
            clean_p = clean_data['t_test'].get('p_value')

        if base_p is not None and clean_p is not None:
            shift = abs(clean_p - base_p)
            result['p_value_shifts'].append(shift)

        # Extract CI widths
        base_ci = None
        clean_ci = None

        if 'analysis' in base_data and 't_test' in base_data['analysis']:
            ci = base_data['analysis']['t_test'].get('ci')
            if ci and len(ci) == 2:
                base_ci = ci[1] - ci[0]
        elif 't_test' in base_data:
            ci = base_data['t_test'].get('ci')
            if ci and len(ci) == 2:
                base_ci = ci[1] - ci[0]

        if 'analysis' in clean_data and 't_test' in clean_data['analysis']:
            ci = clean_data['analysis']['t_test'].get('ci')
            if ci and len(ci) == 2:
                clean_ci = ci[1] - ci[0]
        elif 't_test' in clean_data:
            ci = clean_data['t_test'].get('ci')
            if ci and len(ci) == 2:
                clean_ci = ci[1] - ci[0]

        if base_ci is not None and clean_ci is not None:
            width_change = clean_ci - base_ci
            result['ci_width_changes'].append(width_change)

        # Extract effect sizes
        base_es = None
        clean_es = None

        if 'analysis' in base_data and 't_test' in base_data['analysis']:
            base_es = base_data['analysis']['t_test'].get('effect_size')
        elif 't_test' in base_data:
            base_es = base_data['t_test'].get('effect_size')

        if 'analysis' in clean_data and 't_test' in clean_data['analysis']:
            clean_es = clean_data['analysis']['t_test'].get('effect_size')
        elif 't_test' in clean_data:
            clean_es = clean_data['t_test'].get('effect_size')

        if base_es is not None and clean_es is not None:
            delta = clean_es - base_es
            result['effect_size_deltas'].append(delta)

    # Calculate summary statistics
    import numpy as np
    if result['p_value_shifts']:
        result['p_value_shift_mean'] = float(np.mean(result['p_value_shifts']))
        result['p_value_shift_median'] = float(np.median(result['p_value_shifts']))
        result['p_value_shift_std'] = float(np.std(result['p_value_shifts']))
    else:
        result['p_value_shift_mean'] = None
        result['p_value_shift_median'] = None
        result['p_value_shift_std'] = None

    if result['ci_width_changes']:
        result['ci_width_change_mean'] = float(np.mean(result['ci_width_changes']))
        result['ci_width_change_median'] = float(np.median(result['ci_width_changes']))
        result['ci_width_change_std'] = float(np.std(result['ci_width_changes']))
    else:
        result['ci_width_change_mean'] = None
        result['ci_width_change_median'] = None
        result['ci_width_change_std'] = None

    if result['effect_size_deltas']:
        result['effect_size_delta_mean'] = float(np.mean(result['effect_size_deltas']))
        result['effect_size_delta_median'] = float(np.median(result['effect_size_deltas']))
        result['effect_size_delta_std'] = float(np.std(result['effect_size_deltas']))
    else:
        result['effect_size_delta_mean'] = None
        result['effect_size_delta_median'] = None
        result['effect_size_delta_std'] = None

    return result

def run_sensitivity_analysis(
    baseline_metrics: Optional[List[Dict[str, Any]]],
    cleaned_metrics: Optional[List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Run full sensitivity analysis across dataset size bins.
    """
    if not baseline_metrics:
        logger.error("No baseline metrics found. Cannot run sensitivity analysis.")
        return {'error': 'No baseline metrics found'}

    if not cleaned_metrics:
        logger.warning("No cleaned metrics found. Some bins may be empty.")
        cleaned_metrics = []

    bins = ['small', 'medium', 'large']
    bin_results = []

    for bin_name in bins:
        logger.info(f"Analyzing bin: {bin_name}")
        bin_result = analyze_size_bin(baseline_metrics, cleaned_metrics, bin_name)
        bin_results.append(bin_result)

        if bin_result['count'] < 1:
            logger.warning(f"CONSTRAINT_VIOLATION: Bin '{bin_name}' has < 1 dataset. Proceeding anyway.")

    return {
        'timestamp': datetime.now().isoformat(),
        'bins': bin_results,
        'total_datasets_analyzed': sum(b['count'] for b in bin_results)
    }

def main():
    """Main entry point for dataset size sensitivity analysis."""
    logger = setup_logging("INFO")
    pin_random_seed(42)

    logger.info("Starting dataset size sensitivity analysis (T030)...")

    # Load metrics
    baseline_metrics = load_baseline_metrics()
    cleaned_metrics = load_cleaned_metrics()

    # Run analysis
    analysis_result = run_sensitivity_analysis(baseline_metrics, cleaned_metrics)

    # Write output
    output_path = "data/processed/size_sensitivity_analysis.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(analysis_result, f, indent=2)

    logger.info(f"Size sensitivity analysis complete. Output written to {output_path}")
    return 0

if __name__ == "__main__":
    exit(main())