import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from utils import setup_logging, pin_random_seed
from config import Config

# Constants for binning
BIN_THRESHOLDS = [(0, 50), (50, 200), (200, float('inf'))]
BIN_LABELS = ['small_n<50', 'medium_50-200', 'large_>200']

def load_baseline_metrics(filepath: str = "data/processed/baseline_metrics.json") -> Dict[str, Any]:
    """Load baseline metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baseline metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def load_cleaned_metrics(filepath: str = "data/processed/cleaned_metrics.json") -> Dict[str, Any]:
    """Load cleaned metrics from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Cleaned metrics file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def bin_dataset_size(n_rows: int) -> str:
    """
    Assign a dataset size bin label based on row count.
    Bins: n<50, 50-200, >200
    """
    for (lower, upper), label in zip(BIN_THRESHOLDS, BIN_LABELS):
        if lower <= n_rows < upper:
            return label
    # Fallback for exact boundary at 200 if needed, though logic above covers >200
    if n_rows >= 200:
        return 'large_>200'
    return 'small_n<50'

def analyze_size_bin(
    baseline_entries: List[Dict],
    cleaned_entries: List[Dict],
    bin_label: str
) -> Dict[str, Any]:
    """
    Analyze metrics for a specific size bin.
    Returns aggregated statistics (count, mean shifts, etc.) for the bin.
    """
    bin_baseline = []
    bin_cleaned = []

    for entry in baseline_entries:
        # Extract dataset size if available, otherwise estimate or skip
        # Assuming 'dataset_size' or 'n_rows' is in the entry
        size = entry.get('dataset_size') or entry.get('n_rows') or entry.get('size')
        if size is None:
            # Try to infer from data if present, else skip
            continue
        
        if bin_dataset_size(size) == bin_label:
            bin_baseline.append(entry)
            # Find matching cleaned entry (by dataset name)
            ds_name = entry.get('dataset_name') or entry.get('name')
            for clean_entry in cleaned_entries:
                if (clean_entry.get('dataset_name') or clean_entry.get('name')) == ds_name:
                    bin_cleaned.append(clean_entry)
                    break

    count = len(bin_baseline)
    if count == 0:
        return {
            'bin': bin_label,
            'count': 0,
            'mean_p_value_shift': None,
            'mean_ci_width_change': None,
            'inconsistency_rate': None,
            'note': 'No datasets in this bin'
        }

    # Calculate shifts
    p_shifts = []
    ci_changes = []
    inconsistent_count = 0

    for i, b_entry in enumerate(bin_baseline):
        if i < len(bin_cleaned):
            c_entry = bin_cleaned[i]
            
            # P-value shift
            b_p = b_entry.get('t_test', {}).get('p_value')
            c_p = c_entry.get('t_test', {}).get('p_value')
            if b_p is not None and c_p is not None:
                p_shifts.append(abs(c_p - b_p))
                # Check significance change (p < 0.05)
                if (b_p < 0.05) != (c_p < 0.05):
                    inconsistent_count += 1

            # CI width change
            b_ci = b_entry.get('t_test', {}).get('ci')
            c_ci = c_entry.get('t_test', {}).get('ci')
            if b_ci and c_ci and len(b_ci) == 2 and len(c_ci) == 2:
                b_width = b_ci[1] - b_ci[0]
                c_width = c_ci[1] - c_ci[0]
                ci_changes.append(c_width - b_width)

    mean_p_shift = sum(p_shifts) / len(p_shifts) if p_shifts else None
    mean_ci_change = sum(ci_changes) / len(ci_changes) if ci_changes else None
    inconsistency_rate = inconsistent_count / count if count > 0 else None

    return {
        'bin': bin_label,
        'count': count,
        'mean_p_value_shift': mean_p_shift,
        'mean_ci_width_change': mean_ci_change,
        'inconsistency_rate': inconsistency_rate,
        'datasets_analyzed': [e.get('dataset_name') or e.get('name') for e in bin_baseline]
    }

def run_sensitivity_analysis(
    baseline_metrics: Dict[str, Any],
    cleaned_metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across dataset size bins.
    Logs warnings if bins have <1 dataset.
    """
    logger = logging.getLogger(__name__)
    
    baseline_list = baseline_metrics.get('datasets', [])
    cleaned_list = cleaned_metrics.get('datasets', [])

    results = {
        'analysis_type': 'dataset_size_sensitivity',
        'timestamp': datetime.now().isoformat(),
        'bins': {},
        'summary': {}
    }

    all_empty = True
    for label in BIN_LABELS:
        analysis = analyze_size_bin(baseline_list, cleaned_list, label)
        results['bins'][label] = analysis
        
        if analysis['count'] > 0:
            all_empty = False
            logger.info(f"Bin {label}: {analysis['count']} datasets analyzed. "
                        f"Mean p-shift: {analysis['mean_p_value_shift']}, "
                        f"Inconsistency: {analysis['inconsistency_rate']}")
        else:
            # Log warning as per requirement
            if all_empty and label == BIN_LABELS[0]:
                # Only log once if ALL bins are empty, or per bin? 
                # Requirement: "Log warning if <1 dataset per bin."
                logger.warning(f"CONSTRAINT_VIOLATION: Bin {label} has 0 datasets.")
            elif label == BIN_LABELS[0]:
                # First bin empty
                logger.warning(f"CONSTRAINT_VIOLATION: Bin {label} has 0 datasets.")
            else:
                logger.warning(f"CONSTRAINT_VIOLATION: Bin {label} has 0 datasets.")

    # Summary
    total_datasets = len(baseline_list)
    results['summary'] = {
        'total_datasets_analyzed': total_datasets,
        'bins_with_data': sum(1 for b in results['bins'].values() if b['count'] > 0),
        'bins_empty': sum(1 for b in results['bins'].values() if b['count'] == 0)
    }

    if results['summary']['bins_empty'] > 0:
        logger.warning(f"Sensitivity analysis completed with {results['summary']['bins_empty']} empty bins.")
    
    return results

def main():
    """Main entry point for T030."""
    logger = setup_logging("INFO")
    pin_random_seed(42)
    
    logger.info("Starting T030: Dataset Size Sensitivity Analysis")
    
    try:
        # Load metrics
        baseline_metrics = load_baseline_metrics()
        cleaned_metrics = load_cleaned_metrics()
        
        logger.info("Loaded baseline and cleaned metrics successfully.")
        
        # Run analysis
        sensitivity_results = run_sensitivity_analysis(baseline_metrics, cleaned_metrics)
        
        # Save output
        output_path = "data/processed/sensitivity_analysis_size_bins.json"
        with open(output_path, 'w') as f:
            json.dump(sensitivity_results, f, indent=2)
        
        logger.info(f"Sensitivity analysis results saved to {output_path}")
        return True
        
    except FileNotFoundError as e:
        logger.error(f"Missing required data file: {e}")
        return False
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)