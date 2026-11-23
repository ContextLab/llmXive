"""
Threshold identification logic for User Story 3.

Implements FR-005: Flag configurations where Type I error > 0.10
AND compare against baseline error rate to quantify impact.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from analyze import load_simulation_results, calculate_error_rates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fixed design threshold as per FR-005 and SC-001
TYPE_I_ERROR_THRESHOLD = 0.10

def load_all_result_files(results_dir: Path) -> List[Path]:
    """
    Discover all result JSON files in the results directory.
    
    Args:
        results_dir: Path to the results directory
        
    Returns:
        List of paths to all .json files found
    """
    if not results_dir.exists():
        logger.warning(f"Results directory does not exist: {results_dir}")
        return []
        
    return list(results_dir.glob("*.json"))

def load_result_data(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a single result JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data or None if loading fails
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return None

def extract_metadata_and_errors(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract relevant metadata and error rates from result data.
    
    Args:
        data: Parsed result JSON data
        
    Returns:
        Dictionary with extracted metadata and error rates
    """
    metadata = data.get('metadata', {})
    stats = data.get('statistics', {})
    
    # Extract dataset and configuration info
    dataset_name = metadata.get('dataset', 'unknown')
    sample_size = metadata.get('sample_size', 0)
    augmentation_method = metadata.get('augmentation_method', 'baseline')
    condition = metadata.get('condition', 'unknown')
    
    # Extract error rates
    type_i_error = stats.get('type_i_error_rate')
    type_ii_error = stats.get('type_ii_error_rate')
    type_i_ci_lower = stats.get('type_i_error_ci_lower')
    type_i_ci_upper = stats.get('type_i_error_ci_upper')
    
    return {
        'dataset': dataset_name,
        'sample_size': sample_size,
        'augmentation_method': augmentation_method,
        'condition': condition,
        'type_i_error': type_i_error,
        'type_ii_error': type_ii_error,
        'type_i_ci_lower': type_i_ci_lower,
        'type_i_ci_upper': type_i_ci_upper
    }

def identify_threshold_violations(
    result: Dict[str, Any],
    baseline_results: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Identify if a configuration violates the Type I error threshold.
    
    Args:
        result: Extracted metadata and errors for a single result
        baseline_results: Dictionary of baseline error rates for comparison
            Key format: (dataset, sample_size, condition)
            
    Returns:
        Dictionary with violation status and impact quantification
    """
    dataset = result['dataset']
    sample_size = result['sample_size']
    condition = result['condition']
    method = result['augmentation_method']
    type_i_error = result['type_i_error']
    
    # Check if Type I error exceeds threshold
    is_violation = type_i_error is not None and type_i_error > TYPE_I_ERROR_THRESHOLD
    
    # Quantify impact against baseline
    baseline_key = (dataset, sample_size, condition)
    baseline_error = baseline_results.get(baseline_key)
    
    impact_analysis = {
        'baseline_error_rate': baseline_error,
        'current_error_rate': type_i_error,
        'absolute_difference': None,
        'relative_increase': None,
        'impact_severity': 'none'
    }
    
    if baseline_error is not None and type_i_error is not None:
        absolute_diff = type_i_error - baseline_error
        impact_analysis['absolute_difference'] = absolute_diff
        
        if baseline_error > 0:
            relative_inc = absolute_diff / baseline_error
            impact_analysis['relative_increase'] = relative_inc
        
        # Determine severity
        if is_violation:
            if relative_inc is not None and relative_inc > 1.0:
                impact_analysis['impact_severity'] = 'critical'
            elif absolute_diff > 0.05:
                impact_analysis['impact_severity'] = 'high'
            else:
                impact_analysis['impact_severity'] = 'moderate'
        elif absolute_diff > 0:
            impact_analysis['impact_severity'] = 'low'
    
    return {
        'is_violation': is_violation,
        'threshold_value': TYPE_I_ERROR_THRESHOLD,
        'impact_analysis': impact_analysis
    }

def generate_threshold_report(
    results_dir: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Generate a comprehensive threshold violation report.
    
    Args:
        results_dir: Directory containing result JSON files
        output_path: Path to save the threshold report
        
    Returns:
        Complete threshold report dictionary
    """
    logger.info(f"Scanning results directory: {results_dir}")
    result_files = load_all_result_files(results_dir)
    
    if not result_files:
        logger.warning("No result files found in directory")
        return {
            'threshold_report': {
                'threshold': TYPE_I_ERROR_THRESHOLD,
                'total_configurations': 0,
                'violations': [],
                'summary': {}
            }
        }
    
    # First pass: collect baseline results for comparison
    baseline_results = {}
    all_results = []
    
    for file_path in result_files:
        data = load_result_data(file_path)
        if data is None:
            continue
            
        extracted = extract_metadata_and_errors(data)
        all_results.append({
            'file': str(file_path.name),
            'data': extracted
        })
        
        # Store baseline results for comparison
        if extracted['augmentation_method'] == 'baseline':
            key = (extracted['dataset'], extracted['sample_size'], extracted['condition'])
            baseline_results[key] = extracted['type_i_error']
    
    # Second pass: identify violations
    violations = []
    non_violations = []
    
    for item in all_results:
        result_data = item['data']
        violation_info = identify_threshold_violations(result_data, baseline_results)
        
        report_entry = {
            'file': item['file'],
            'dataset': result_data['dataset'],
            'sample_size': result_data['sample_size'],
            'method': result_data['augmentation_method'],
            'condition': result_data['condition'],
            'type_i_error': result_data['type_i_error'],
            'type_i_ci': (result_data['type_i_ci_lower'], result_data['type_i_ci_upper']),
            **violation_info
        }
        
        if violation_info['is_violation']:
            violations.append(report_entry)
        else:
            non_violations.append(report_entry)
    
    # Generate summary statistics
    total_configs = len(all_results)
    violation_count = len(violations)
    violation_rate = violation_count / total_configs if total_configs > 0 else 0
    
    # Group violations by method
    violations_by_method = {}
    for v in violations:
        method = v['method']
        if method not in violations_by_method:
            violations_by_method[method] = []
        violations_by_method[method].append(v)
    
    # Group violations by severity
    severity_counts = {'critical': 0, 'high': 0, 'moderate': 0, 'low': 0}
    for v in violations:
        severity = v['impact_severity']
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    report = {
        'metadata': {
            'threshold': TYPE_I_ERROR_THRESHOLD,
            'generated_at': os.popen('date -Iseconds 2>/dev/null || date').read().strip(),
            'total_configurations_analyzed': total_configs,
            'violations_found': violation_count,
            'non_violations': len(non_violations),
            'violation_rate': violation_rate
        },
        'violations_by_method': {
            method: len(items) for method, items in violations_by_method.items()
        },
        'severity_distribution': severity_counts,
        'detailed_violations': violations,
        'safe_configurations': non_violations,
        'disclaimer': "DISCLAIMER: Findings are associational and do not imply causation. "
                     "Results are specific to the datasets and conditions tested."
    }
    
    # Save report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Threshold report saved to: {output_path}")
    logger.info(f"Found {violation_count} violations out of {total_configs} configurations")
    
    return report

def main():
    """Main entry point for threshold identification."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Identify configurations where Type I error exceeds threshold'
    )
    parser.add_argument(
        '--results-dir',
        type=str,
        default='results',
        help='Directory containing result JSON files'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/threshold_violations.json',
        help='Path to save threshold report'
    )
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    output_path = Path(args.output)
    
    report = generate_threshold_report(results_dir, output_path)
    
    # Print summary
    print("\n" + "="*60)
    print("THRESHOLD VIOLATION SUMMARY")
    print("="*60)
    print(f"Threshold: {report['metadata']['threshold']}")
    print(f"Total Configurations: {report['metadata']['total_configurations_analyzed']}")
    print(f"Violations Found: {report['metadata']['violations_found']}")
    print(f"Violation Rate: {report['metadata']['violation_rate']:.2%}")
    print("\nViolations by Method:")
    for method, count in report['violations_by_method'].items():
        print(f"  {method}: {count}")
    print("\nSeverity Distribution:")
    for severity, count in report['severity_distribution'].items():
        print(f"  {severity}: {count}")
    print("="*60)

if __name__ == '__main__':
    main()