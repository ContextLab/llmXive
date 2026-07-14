"""
T030: Implement dataset size binning sensitivity analysis.

Bins datasets by size: n < 50, 50 <= n <= 200, n > 200.
Logs warnings if bins are empty (CONSTRAINT_VIOLATION).
Depends on baseline_metrics.json and cleaned_metrics.json.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils import setup_logging, pin_random_seed

logger = setup_logging("INFO")

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Optional[Dict[str, Any]]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Baseline metrics file not found: {filepath}")
        return None
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Optional[Dict[str, Any]]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Cleaned metrics file not found: {filepath}")
        return None
    with open(filepath, 'r') as f:
        return json.load(f)

def bin_dataset_size(n_rows: int) -> str:
    """
    Assign a dataset size bin based on row count.
    
    Bins:
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
    datasets: List[Dict[str, Any]], 
    bin_label: str, 
    metrics_source: str
) -> Dict[str, Any]:
    """
    Analyze a specific size bin.
    
    Returns stats: count, list of dataset names, average p-value shift, etc.
    """
    if not datasets:
        return {
            'bin': bin_label,
            'count': 0,
            'datasets': [],
            'avg_p_value_shift': None,
            'avg_ci_width_change': None,
            'avg_effect_size_delta': None,
            'warning': f"CONSTRAINT_VIOLATION: Bin '{bin_label}' is empty ({metrics_source})."
        }
    
    dataset_names = [d.get('dataset_name', d.get('name', 'Unknown')) for d in datasets]
    
    # Calculate shifts if metrics are available
    p_shifts = []
    ci_changes = []
    effect_deltas = []
    
    for d in datasets:
        # Extract p-value shift if available
        if 'p_value_shift' in d:
            p_shifts.append(d['p_value_shift'])
        if 'ci_width_change' in d:
            ci_changes.append(d['ci_width_change'])
        if 'effect_size_delta' in d:
            effect_deltas.append(d['effect_size_delta'])
    
    return {
        'bin': bin_label,
        'count': len(datasets),
        'datasets': dataset_names,
        'avg_p_value_shift': sum(p_shifts) / len(p_shifts) if p_shifts else None,
        'avg_ci_width_change': sum(ci_changes) / len(ci_changes) if ci_changes else None,
        'avg_effect_size_delta': sum(effect_deltas) / len(effect_deltas) if effect_deltas else None,
        'warning': None
    }

def run_sensitivity_analysis(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run sensitivity analysis by dataset size binning.
    
    Combines baseline and cleaned datasets, bins them, and analyzes each bin.
    """
    pin_random_seed(42)
    
    baseline_datasets = baseline_metrics.get('datasets', [])
    cleaned_datasets = cleaned_metrics.get('datasets', [])
    
    # Map cleaned metrics to baseline by dataset name
    cleaned_map = {}
    for c in cleaned_datasets:
        name = c.get('dataset_name', c.get('name'))
        if name:
            cleaned_map[name] = c
    
    # Merge and bin
    all_bins = {'small': [], 'medium': [], 'large': []}
    
    for b in baseline_datasets:
        name = b.get('dataset_name', b.get('name'))
        n_rows = b.get('dataset_size', b.get('n_rows', 0))
        bin_label = bin_dataset_size(n_rows)
        
        entry = {
            'dataset_name': name,
            'dataset_size': n_rows,
            'bin': bin_label,
            'baseline': b
        }
        
        # Attach cleaned metrics if available
        if name in cleaned_map:
            c = cleaned_map[name]
            # Calculate shifts
            base_p = b.get('t_test', {}).get('p_value') if isinstance(b.get('t_test'), dict) else b.get('p_value')
            clean_p = c.get('t_test', {}).get('p_value') if isinstance(c.get('t_test'), dict) else c.get('p_value')
            
            if base_p is not None and clean_p is not None:
                entry['p_value_shift'] = abs(clean_p - base_p)
            
            base_ci = b.get('t_test', {}).get('ci', [None, None]) if isinstance(b.get('t_test'), dict) else b.get('ci')
            clean_ci = c.get('t_test', {}).get('ci', [None, None]) if isinstance(c.get('t_test'), dict) else c.get('ci')
            
            if base_ci and clean_ci and base_ci[0] is not None and clean_ci[0] is not None:
                base_width = abs(base_ci[1] - base_ci[0])
                clean_width = abs(clean_ci[1] - clean_ci[0])
                entry['ci_width_change'] = clean_width - base_width
            
            base_eff = b.get('effect_size', b.get('cohen_d'))
            clean_eff = c.get('effect_size', c.get('cohen_d'))
            if base_eff is not None and clean_eff is not None:
                entry['effect_size_delta'] = clean_eff - base_eff
        
        all_bins[bin_label].append(entry)
    
    # Analyze each bin
    results = {}
    for bin_label in ['small', 'medium', 'large']:
        bin_data = all_bins[bin_label]
        analysis = analyze_size_bin(bin_data, bin_label, "combined")
        results[bin_label] = analysis
        
        if analysis['warning']:
            logger.warning(analysis['warning'])
    
    # Final summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'analysis_type': 'dataset_size_sensitivity',
        'bins': results,
        'total_datasets_analyzed': sum(len(b) for b in all_bins.values())
    }
    
    return summary

def main():
    """Main entry point for T030."""
    logger.info("Starting T030: Dataset Size Sensitivity Analysis")
    
    # Load metrics
    baseline = load_baseline_metrics()
    if not baseline:
        logger.error("Failed to load baseline metrics. Cannot proceed.")
        return 1
    
    cleaned = load_cleaned_metrics()
    if not cleaned:
        logger.error("Failed to load cleaned metrics. Cannot proceed.")
        return 1
    
    # Run analysis
    report = run_sensitivity_analysis(baseline, cleaned)
    
    # Write output
    output_path = "data/processed/sensitivity_analysis_by_size.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sensitivity analysis written to {output_path}")
    return 0

if __name__ == "__main__":
    exit(main())
