"""
No Threshold Reporting Module.

Implements logic to detect and report when no resolution threshold is found
(i.e., bias remains within limits even at low audio frequencies).

This module ensures strict typing and comprehensive documentation
as per task T039 requirements.
"""
import logging
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

def check_bias_across_all_resolutions(metrics: List[Dict[str, Any]]) -> bool:
    """
    Check if bias exceeds the threshold for ANY resolution.
    
    Args:
        metrics: List of all metrics.
        
    Returns:
        True if bias NEVER exceeds the threshold (no threshold found), False otherwise.
    """
    for m in metrics:
        if m.get('exceeds_threshold', False):
            return False
    return True

def generate_no_threshold_report(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a report for the "No threshold found" scenario.
    
    Args:
        metrics: List of all metrics.
        
    Returns:
        Dictionary containing the report details.
    """
    min_rate = min(m['sampling_rate'] for m in metrics) if metrics else 0
    
    return {
        'scenario': 'No Threshold Found',
        'description': 'Bias remained within catalog confidence intervals for all tested resolutions.',
        'lowest_tested_rate': min_rate,
        'implication': 'The data resolution is sufficient even at the lowest tested rate.',
        'recommendation': 'Consider testing lower rates or re-evaluating the bias threshold.'
    }

def save_no_threshold_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the no-threshold report to a JSON file.
    
    Args:
        report: The report dictionary.
        output_path: Path to the output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"No-threshold report saved to {output_path}")

def main() -> None:
    """
    Main entry point for no-threshold reporting.
    """
    from code.config import RESULTS_DIR
    
    metrics_dir = RESULTS_DIR / 'metrics'
    output_file = RESULTS_DIR / 'no_threshold_report.json'
    
    import json
    metrics = []
    if metrics_dir.exists():
        for f in metrics_dir.glob("*.json"):
            with open(f, 'r') as file:
                metrics.append(json.load(file))
    
    if check_bias_across_all_resolutions(metrics):
        report = generate_no_threshold_report(metrics)
        save_no_threshold_report(report, output_file)
    else:
        logger.info("Threshold found; no-threshold report not generated.")

if __name__ == '__main__':
    main()
