"""
Sensitivity Analysis for Safety Thresholds.

This module implements the sensitivity analysis required for T041.
It re-runs the comparative analysis with alternative thresholds to demonstrate
the robustness of the "unsafe" classification near the 0.10 boundary.

It loads existing simulation results, calculates error rates, and tests
against a range of thresholds (e.g., 0.08, 0.10, 0.12) to show how
classifications shift.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_THRESHOLD = 0.10
SENSITIVITY_RANGES = [0.05, 0.08, 0.10, 0.12, 0.15]
RESULTS_DIR = Path("results")
OUTPUT_FILE = Path("results/sensitivity_analysis_report.json")

def load_all_result_files() -> List[Dict[str, Any]]:
    """
    Loads all JSON result files from the results directory.

    Returns:
        List of dictionaries containing the parsed JSON data from each file.
    """
    result_files = []
    if not RESULTS_DIR.exists():
        logger.warning(f"Results directory {RESULTS_DIR} does not exist.")
        return result_files

    for file_path in RESULTS_DIR.glob("*.json"):
        if file_path.name.startswith("summary") or file_path.name.startswith("sensitivity"):
            continue  # Skip summary and existing sensitivity reports to avoid recursion

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['_source_file'] = file_path.name
                result_files.append(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")

    logger.info(f"Loaded {len(result_files)} result files for sensitivity analysis.")
    return result_files

def load_result_data(result: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    """
    Extracts Type I and Type II error rates from a result dictionary.

    Args:
        result: A dictionary containing simulation results.

    Returns:
        Tuple of (type_i_error, type_ii_error) or (None, None) if missing.
    """
    type_i = None
    type_ii = None

    # Try to find in metadata or top level
    if 'metadata' in result:
        type_i = result['metadata'].get('type_i_error_rate')
        type_ii = result['metadata'].get('type_ii_error_rate')
    
    if type_i is None and 'type_i_error_rate' in result:
        type_i = result['type_i_error_rate']
    if type_ii is None and 'type_ii_error_rate' in result:
        type_ii = result['type_ii_error_rate']

    # Handle list of errors if aggregated differently
    if isinstance(type_i, list) and len(type_i) > 0:
        type_i = np.mean(type_i)
    if isinstance(type_ii, list) and len(type_ii) > 0:
        type_ii = np.mean(type_ii)

    return type_i, type_ii

def extract_error_metrics(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extracts relevant error metrics and metadata for analysis.

    Args:
        result: The result dictionary.

    Returns:
        Dictionary with extracted metrics.
    """
    type_i, type_ii = load_result_data(result)
    
    # Extract configuration details
    config = result.get('metadata', {}).get('config', {})
    dataset_name = config.get('dataset', result.get('_source_file', 'unknown'))
    size = config.get('size', result.get('metadata', {}).get('size', 'unknown'))
    method = config.get('method', result.get('metadata', {}).get('method', 'baseline'))

    return {
        'source_file': result.get('_source_file', 'unknown'),
        'dataset': dataset_name,
        'size': size,
        'method': method,
        'type_i_error': type_i,
        'type_ii_error': type_ii
    }

def classify_safety_status(type_i_error: Optional[float], threshold: float) -> str:
    """
    Classifies the safety status based on Type I error and a given threshold.

    Args:
        type_i_error: The observed Type I error rate.
        threshold: The safety threshold to compare against.

    Returns:
        'unsafe' if error > threshold, 'safe' otherwise.
    """
    if type_i_error is None:
        return "unknown"
    return "unsafe" if type_i_error > threshold else "safe"

def analyze_threshold_sensitivity(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Performs sensitivity analysis by re-classifying results against multiple thresholds.

    Args:
        results: List of result dictionaries.

    Returns:
        Dictionary containing the sensitivity analysis report.
    """
    analysis = {
        'description': "Sensitivity analysis of safety thresholds near 0.10 boundary.",
        'thresholds_tested': SENSITIVITY_RANGES,
        'baseline_threshold': DEFAULT_THRESHOLD,
        'total_configurations_analyzed': len(results),
        'sensitivity_matrix': {}
    }

    # Initialize matrix for each threshold
    for t in SENSITIVITY_RANGES:
        analysis['sensitivity_matrix'][str(t)] = {
            'total': 0,
            'safe': 0,
            'unsafe': 0,
            'unknown': 0,
            'details': []
        }

    # Analyze each result against all thresholds
    for res in results:
        metrics = extract_error_metrics(res)
        if metrics['type_i_error'] is None:
            continue

        for t in SENSITIVITY_RANGES:
            status = classify_safety_status(metrics['type_i_error'], t)
            entry = analysis['sensitivity_matrix'][str(t)]
            entry['total'] += 1
            entry[status] += 1
            
            # Record specific configuration status for this threshold
            if status != classify_safety_status(metrics['type_i_error'], DEFAULT_THRESHOLD):
                # Only log if status changes relative to baseline to highlight sensitivity
                entry['details'].append({
                    'config': f"{metrics['dataset']}_{metrics['size']}_{metrics['method']}",
                    'type_i_error': metrics['type_i_error'],
                    'status_at_threshold': status,
                    'status_at_baseline': classify_safety_status(metrics['type_i_error'], DEFAULT_THRESHOLD)
                })

    # Summary of shifts
    shifts = {
        'thresholds_with_shifts': [],
        'total_shifts': 0
    }
    
    for t in SENSITIVITY_RANGES:
        if t == DEFAULT_THRESHOLD:
            continue
        details = analysis['sensitivity_matrix'][str(t)]['details']
        if details:
            shifts['thresholds_with_shifts'].append(t)
            shifts['total_shifts'] += len(details)

    analysis['shift_summary'] = shifts

    return analysis

def generate_sensitivity_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates the final sensitivity analysis report.

    Args:
        results: List of result dictionaries.

    Returns:
        The complete report dictionary.
    """
    logger.info("Generating sensitivity analysis report...")
    
    report = {
        'metadata': {
            'generated_by': 'sensitivity_analysis.py',
            'task_id': 'T041',
            'disclaimer': 'DISCLAIMER: Findings are associational and do not imply causation. This analysis demonstrates robustness of threshold classifications.',
            'thresholds': SENSITIVITY_RANGES
        },
        'analysis': analyze_threshold_sensitivity(results)
    }

    return report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the report to a JSON file.

    Args:
        report: The report dictionary.
        output_path: Path to save the file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Sensitivity analysis report saved to {output_path}")

def main():
    """
    Main entry point for the sensitivity analysis.
    """
    logger.info("Starting Safety Threshold Sensitivity Analysis (T041)...")
    
    # Load existing results
    results = load_all_result_files()
    
    if not results:
        logger.error("No result files found to analyze. Ensure the pipeline has run successfully.")
        # Create a minimal report indicating failure to find data
        report = {
            'metadata': {
                'generated_by': 'sensitivity_analysis.py',
                'task_id': 'T041',
                'error': 'No result files found. Pipeline must run successfully before sensitivity analysis.'
            },
            'analysis': {}
        }
        save_report(report, OUTPUT_FILE)
        return

    # Generate report
    report = generate_sensitivity_report(results)
    
    # Save report
    save_report(report, OUTPUT_FILE)
    
    logger.info("Sensitivity Analysis completed successfully.")

if __name__ == "__main__":
    main()