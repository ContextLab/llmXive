"""
Report Generation Module.

This module handles the creation of final summary reports by aggregating
results from correlation analysis, power analysis, and multicollinearity checks.
It ensures all required fields are present in the output JSON.

Functions:
    load_json_file: Loads a JSON file.
    generate_final_report: Aggregates results into a final report.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """
    Loads a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Dictionary representing the JSON content.
    """
    if not file_path.exists():
        return {}
    
    with open(file_path, 'r') as f:
        return json.load(f)

def generate_final_report(
    correlation_results: Dict[str, Any],
    power_results: Dict[str, Any],
    collinearity_results: Dict[str, Any],
    warning_flags: List[str]
) -> Dict[str, Any]:
    """
    Generates the final summary report by combining all analysis results.

    Args:
        correlation_results: Results from correlation analysis.
        power_results: Results from power analysis.
        collinearity_results: Results from multicollinearity check.
        warning_flags: List of warning flags.

    Returns:
        Dictionary representing the final report.
    """
    report = {
        'r': correlation_results.get('r'),
        'p_value': correlation_results.get('p_value'),
        'ci_lower': correlation_results.get('ci_lower'),
        'ci_upper': correlation_results.get('ci_upper'),
        'power': power_results.get('power'),
        'hypothesis_status': 'Supported' if correlation_results.get('p_value', 1.0) < 0.05 else 'Not Supported',
        'warning_flags': warning_flags
    }
    
    if collinearity_results.get('collinearity_flag'):
        report['warning_flags'].append('Multicollinearity detected: resonant_surface_density excluded')
    
    return report

def main():
    """
    Entry point for testing the report generator module directly.
    """
    logger.info("Report generator module initialized.")
