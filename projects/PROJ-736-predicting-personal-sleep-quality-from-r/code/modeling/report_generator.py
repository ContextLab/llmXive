"""
Report generation module for T026 and T026c.
Handles loading and saving of ResultReport.json.
"""
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from config import get_paths, ensure_dirs


def load_result_report() -> Dict[str, Any]:
    """
    Load the ResultReport.json file.
    If it doesn't exist, return an empty report structure.
    """
    paths = get_paths()
    report_file = paths['data_results'] / 'ResultReport.json'
    
    if not report_file.exists():
        logging.warning(f"ResultReport.json not found at {report_file}. Creating new report.")
        return {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'version': '1.0'
            },
            'model_metrics': {},
            'permutation_test': {},
            'bootstrap_ci': {},
            'sensitivity_analysis': {},
            'visualization': {}
        }
    
    with open(report_file, 'r') as f:
        return json.load(f)


def save_result_report(report: Dict[str, Any]) -> None:
    """
    Save the ResultReport.json file.
    """
    paths = get_paths()
    ensure_dirs(paths)
    report_file = paths['data_results'] / 'ResultReport.json'
    
    # Update metadata
    report['metadata']['last_updated'] = datetime.now().isoformat()
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logging.info(f"Saved ResultReport.json to {report_file}")


def load_permutation_p_value() -> Optional[float]:
    """Load permutation test p-value from report."""
    report = load_result_report()
    return report.get('permutation_test', {}).get('p_value')


def load_bootstrap_ci() -> Optional[Dict[str, float]]:
    """Load bootstrap confidence intervals from report."""
    report = load_result_report()
    return report.get('bootstrap_ci', {})


def load_model_metrics() -> Optional[Dict[str, float]]:
    """Load model metrics from report."""
    report = load_result_report()
    return report.get('model_metrics', {})


def load_sensitivity_results() -> Optional[Dict[str, Any]]:
    """Load sensitivity analysis results from report."""
    report = load_result_report()
    return report.get('sensitivity_analysis', {})


def generate_result_report(
    model_metrics: Optional[Dict[str, float]] = None,
    permutation_p_value: Optional[float] = None,
    bootstrap_ci: Optional[Dict[str, float]] = None,
    sensitivity_results: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate or update the ResultReport.json with all metrics.
    """
    report = load_result_report()
    
    # Update model metrics
    if model_metrics:
        report['model_metrics'] = model_metrics
    
    # Update permutation test results
    if permutation_p_value is not None:
        report['permutation_test'] = {
            'p_value': permutation_p_value,
            'note': 'Approximation derived from 100-subject stratified subset (Plan Override of FR-006)',
            'subset_size': 100
        }
    
    # Update bootstrap CI
    if bootstrap_ci:
        report['bootstrap_ci'] = bootstrap_ci
    
    # Update sensitivity analysis
    if sensitivity_results:
        report['sensitivity_analysis'] = sensitivity_results
        if sensitivity_results.get('incomplete'):
            report['sensitivity_analysis']['note'] = 'Analysis incomplete due to time budget constraint'
    
    # Ensure metadata exists
    if 'metadata' not in report:
        report['metadata'] = {}
    report['metadata']['generated_at'] = datetime.now().isoformat()
    
    save_result_report(report)
    return report


def main():
    """CLI entry point for report generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate ResultReport.json')
    parser.add_argument('--metrics', type=str, help='JSON string of model metrics')
    parser.add_argument('--p-value', type=float, help='Permutation test p-value')
    parser.add_argument('--ci', type=str, help='JSON string of bootstrap CI')
    
    args = parser.parse_args()
    
    model_metrics = json.loads(args.metrics) if args.metrics else None
    bootstrap_ci = json.loads(args.ci) if args.ci else None
    
    report = generate_result_report(
        model_metrics=model_metrics,
        permutation_p_value=args.p_value,
        bootstrap_ci=bootstrap_ci
    )
    
    print(f"ResultReport.json generated at {get_paths()['data_results'] / 'ResultReport.json'}")
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
