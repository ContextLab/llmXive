"""
Report generation module for finalizing results.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error

def load_result_report():
    """
    Load existing result report if it exists.
    
    Returns:
        Result report dictionary or empty dict
    """
    paths = get_paths()
    report_path = paths['results_dir'] / "ResultReport.json"
    
    if report_path.exists():
        with open(report_path, 'r') as f:
            return json.load(f)
    
    return {}

def save_result_report(report: dict):
    """
    Save result report to disk.
    
    Args:
        report: Result report dictionary
    """
    paths = get_paths()
    report_path = paths['results_dir'] / "ResultReport.json"
    ensure_dirs()
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logging.info(f"Saved result report to {report_path}")

def load_permutation_p_value():
    """
    Load permutation test p-value.
    
    Returns:
        P-value or None
    """
    paths = get_paths()
    perm_path = paths['results_dir'] / "permutation_p_value.json"
    
    if perm_path.exists():
        with open(perm_path, 'r') as f:
            data = json.load(f)
            return data.get('p_value')
    
    return None

def load_bootstrap_ci():
    """
    Load bootstrap confidence intervals.
    
    Returns:
        Bootstrap results dictionary or None
    """
    paths = get_paths()
    boot_path = paths['results_dir'] / "bootstrap_results.json"
    
    if boot_path.exists():
        with open(boot_path, 'r') as f:
            return json.load(f)
    
    return None

def load_model_metrics():
    """
    Load model metrics.
    
    Returns:
        Metrics dictionary or None
    """
    paths = get_paths()
    metrics_path = paths['results_dir'] / "model_metrics.json"
    
    if metrics_path.exists():
        with open(metrics_path, 'r') as f:
            return json.load(f)
    
    return None

def load_sensitivity_results():
    """
    Load sensitivity analysis results.
    
    Returns:
        Sensitivity results dictionary or None
    """
    paths = get_paths()
    sens_path = paths['results_dir'] / "sensitivity_analysis.json"
    
    if sens_path.exists():
        with open(sens_path, 'r') as f:
            return json.load(f)
    
    return None

def generate_result_report():
    """
    Generate final result report.
    
    Returns:
        Result report dictionary
    """
    report = {
        'timestamp': datetime.now().isoformat(),
        'version': '1.0',
        'pipeline_complete': True,
    }
    
    # Add metrics
    metrics = load_model_metrics()
    if metrics:
        report['model_metrics'] = metrics
    
    # Add bootstrap results
    bootstrap = load_bootstrap_ci()
    if bootstrap:
        report['bootstrap_ci'] = bootstrap
    
    # Add permutation p-value
    p_value = load_permutation_p_value()
    if p_value is not None:
        report['permutation_p_value'] = p_value
        report['p_value_note'] = "Approximation derived from 100-subject subset (Plan Override of FR-006)"
    
    # Add sensitivity analysis
    sensitivity = load_sensitivity_results()
    if sensitivity:
        report['sensitivity_analysis'] = sensitivity
    
    return report

def finalize_report():
    """
    Finalize and save the result report.
    """
    logger = logging.getLogger(__name__)
    log_stage_start(logger, "Report Generation")
    
    try:
        report = generate_result_report()
        save_result_report(report)
        log_stage_complete(logger, "Report Generation")
    except Exception as e:
        log_stage_error(logger, "Report Generation", str(e))
        raise

def main():
    """
    Main function to generate report.
    """
    finalize_report()

if __name__ == "__main__":
    main()
