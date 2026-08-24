"""
Task T030: Verify metrics computed for real datasets.

Reads data/processed/metrics.json and verifies that ACF, Hurst, and 
spectral density peak ratio are computed for all entries.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging import setup_logger, log_info, log_warning, log_error, log_critical

REQUIRED_METRICS = ['hurst', 'acf_vector', 'spectral_peak_ratio']

def verify_metrics(metrics_path: Path) -> Dict[str, Any]:
    """
    Verify that all required metrics are present in the metrics file.
    
    Args:
        metrics_path: Path to data/processed/metrics.json
        
    Returns:
        Dictionary with verification status and details
    """
    result = {
        'status': 'PASS',
        'total_entries': 0,
        'verified_entries': 0,
        'missing_metrics': [],
        'details': []
    }
    
    if not metrics_path.exists():
        log_error(f"Metrics file not found: {metrics_path}")
        result['status'] = 'FAIL'
        result['error'] = f"File not found: {metrics_path}"
        return result
    
    try:
        with open(metrics_path, 'r') as f:
            metrics_data = json.load(f)
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse metrics JSON: {e}")
        result['status'] = 'FAIL'
        result['error'] = f"Invalid JSON: {e}"
        return result
    
    if not isinstance(metrics_data, list):
        log_error(f"Expected metrics_data to be a list, got {type(metrics_data)}")
        result['status'] = 'FAIL'
        result['error'] = "Metrics data must be a list"
        return result
    
    result['total_entries'] = len(metrics_data)
    
    for i, entry in enumerate(metrics_data):
        entry_details = {
            'index': i,
            'source': entry.get('source', 'unknown'),
            'is_shuffled': entry.get('is_shuffled', False),
            'present_metrics': [],
            'missing_metrics': []
        }
        
        for metric in REQUIRED_METRICS:
            if metric in entry and entry[metric] is not None:
                entry_details['present_metrics'].append(metric)
            else:
                entry_details['missing_metrics'].append(metric)
                if metric not in result['missing_metrics']:
                    result['missing_metrics'].append(metric)
        
        if not entry_details['missing_metrics']:
            result['verified_entries'] += 1
            entry_details['status'] = 'PASS'
        else:
            entry_details['status'] = 'FAIL'
            log_warning(f"Entry {i} ({entry_details['source']}) missing metrics: {entry_details['missing_metrics']}")
        
        result['details'].append(entry_details)
    
    if result['verified_entries'] == result['total_entries']:
        result['status'] = 'PASS'
        log_info(f"Verification PASSED: All {result['total_entries']} entries have required metrics.")
    else:
        result['status'] = 'FAIL'
        log_error(f"Verification FAILED: {result['total_entries'] - result['verified_entries']} entries missing metrics.")
    
    return result

def main():
    """Main entry point for T030 verification."""
    logger = setup_logger("T030_verification", level=logging.INFO)
    
    # Define paths
    metrics_path = project_root / "data" / "processed" / "metrics.json"
    output_path = project_root / "data" / "results" / "t030_verification.json"
    
    log_info(f"Starting T030 verification for: {metrics_path}")
    
    # Verify metrics
    verification_result = verify_metrics(metrics_path)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write verification result
    with open(output_path, 'w') as f:
        json.dump(verification_result, f, indent=2)
    
    log_info(f"Verification result written to: {output_path}")
    
    # Exit with appropriate code
    if verification_result['status'] == 'PASS':
        log_info("T030 verification completed successfully.")
        sys.exit(0)
    else:
        log_critical("T030 verification failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()