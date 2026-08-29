"""
Sensitivity Analysis for Safety Thresholds.

This module implements a sensitivity analysis to demonstrate the robustness
of the "unsafe" classification (Type I error > threshold) near the 0.10 boundary.
It re-runs comparative analysis with alternative thresholds (0.05, 0.10, 0.15, 0.20)
and generates a report identifying how classifications shift across these boundaries.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

# Import existing utilities from the project
from analyze import load_simulation_results, calculate_error_rates
from compare_results import load_all_results, categorize_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default thresholds for sensitivity analysis
DEFAULT_THRESHOLDS = [0.05, 0.10, 0.15, 0.20]
DESIGN_THRESHOLD = 0.10

def load_all_result_files(results_dir: Path) -> List[Path]:
    """
    Discover all result JSON files in the results directory.
    
    Args:
        results_dir: Path to the results directory.
        
    Returns:
        List of Path objects pointing to JSON files.
    """
    pattern = str(results_dir / "*.json")
    files = list(Path().glob(pattern))
    logger.info(f"Found {len(files)} result files in {results_dir}")
    return files

def load_result_data(file_paths: List[Path]) -> List[Dict[str, Any]]:
    """
    Load data from multiple result JSON files.
    
    Args:
        file_paths: List of paths to JSON files.
        
    Returns:
        List of dictionaries containing the loaded JSON data.
    """
    results = []
    for fp in file_paths:
        try:
            with open(fp, 'r') as f:
                data = json.load(f)
                data['_source_file'] = fp.name
                results.append(data)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Failed to load {fp}: {e}")
    return results

def extract_error_metrics(result_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    """
    Extract Type I and Type II error rates from a result dictionary.
    
    Args:
        result_data: Dictionary containing simulation results.
        
    Returns:
        Tuple of (type_i_rate, type_ii_rate) or (None, None) if not found.
    """
    type_i = None
    type_ii = None
    
    # Try to find error rates in the expected structure
    if 'error_rates' in result_data:
        type_i = result_data['error_rates'].get('type_i')
        type_ii = result_data['error_rates'].get('type_ii')
    elif 'type_i_rate' in result_data:
        type_i = result_data['type_i_rate']
        type_ii = result_data.get('type_ii_rate')
    elif 'metrics' in result_data:
        type_i = result_data['metrics'].get('type_i')
        type_ii = result_data['metrics'].get('type_ii')
        
    return type_i, type_ii

def classify_safety_status(type_i_rate: Optional[float], threshold: float) -> str:
    """
    Classify whether a configuration is 'safe' or 'unsafe' based on Type I error.
    
    Args:
        type_i_rate: The observed Type I error rate.
        threshold: The safety threshold.
        
    Returns:
        String classification: 'safe', 'unsafe', or 'unknown' if data is missing.
    """
    if type_i_rate is None:
        return 'unknown'
    if type_i_rate > threshold:
        return 'unsafe'
    return 'safe'

def analyze_threshold_sensitivity(
    results: List[Dict[str, Any]],
    thresholds: List[float] = DEFAULT_THRESHOLDS
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis across multiple thresholds.
    
    For each result configuration, determine its safety status at each threshold
    and track how classifications change near the design threshold (0.10).
    
    Args:
        results: List of result dictionaries.
        thresholds: List of thresholds to analyze.
        
    Returns:
        Dictionary containing the sensitivity analysis results.
    """
    analysis = {
        'thresholds_analyzed': thresholds,
        'design_threshold': DESIGN_THRESHOLD,
        'configurations': [],
        'summary': {
            'total_configurations': len(results),
            'classifications_at_design_threshold': {
                'safe': 0,
                'unsafe': 0,
                'unknown': 0
            }
        }
    }
    
    for result in results:
        type_i, type_ii = extract_error_metrics(result)
        config_analysis = {
            'source_file': result.get('_source_file', 'unknown'),
            'type_i_rate': type_i,
            'type_ii_rate': type_ii,
            'classifications': {}
        }
        
        for threshold in thresholds:
            status = classify_safety_status(type_i, threshold)
            config_analysis['classifications'][str(threshold)] = status
            
            # Track counts at design threshold
            if abs(threshold - DESIGN_THRESHOLD) < 1e-6:
                analysis['summary']['classifications_at_design_threshold'][status] += 1
        
        # Identify if this configuration is near the boundary
        # (i.e., status changes between 0.05 and 0.20)
        statuses = list(config_analysis['classifications'].values())
        if 'safe' in statuses and 'unsafe' in statuses:
            config_analysis['near_boundary'] = True
        else:
            config_analysis['near_boundary'] = False
        
        analysis['configurations'].append(config_analysis)
    
    return analysis

def generate_sensitivity_report(
    sensitivity_data: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Generate a detailed sensitivity analysis report.
    
    Args:
        sensitivity_data: Dictionary containing the analysis results.
        output_path: Path where the report will be saved.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add metadata
    report = {
        'metadata': {
            'description': 'Sensitivity Analysis for Safety Thresholds',
            'design_threshold': DESIGN_THRESHOLD,
            'analysis_thresholds': sensitivity_data['thresholds_analyzed'],
            'generated_by': 'T041_sensitivity_analysis',
            'disclaimer': 'DISCLAIMER: Findings are associational and do not imply causation. '
                         'This analysis demonstrates the robustness of safety classifications '
                         'near the threshold boundary.'
        },
        'summary': sensitivity_data['summary'],
        'detailed_results': sensitivity_data['configurations']
    }
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sensitivity analysis report saved to {output_path}")

def main():
    """
    Main entry point for the sensitivity analysis task.
    """
    # Define paths
    project_root = Path(__file__).parent.parent
    results_dir = project_root / 'results'
    output_dir = project_root / 'results'
    output_file = output_dir / 'sensitivity_analysis_report.json'
    
    logger.info(f"Starting sensitivity analysis. Results directory: {results_dir}")
    
    if not results_dir.exists():
        logger.error(f"Results directory does not exist: {results_dir}")
        return
    
    # Load all result files
    file_paths = load_all_result_files(results_dir)
    if not file_paths:
        logger.warning("No result files found. Skipping sensitivity analysis.")
        return
    
    results = load_result_data(file_paths)
    if not results:
        logger.error("Failed to load any result data.")
        return
    
    # Perform sensitivity analysis
    logger.info(f"Analyzing {len(results)} configurations across {len(DEFAULT_THRESHOLDS)} thresholds")
    sensitivity_data = analyze_threshold_sensitivity(results, DEFAULT_THRESHOLDS)
    
    # Generate report
    generate_sensitivity_report(sensitivity_data, output_file)
    
    # Print summary to console
    print("\n" + "="*60)
    print("SENSITIVITY ANALYSIS SUMMARY")
    print("="*60)
    print(f"Configurations analyzed: {sensitivity_data['summary']['total_configurations']}")
    print(f"Design threshold: {sensitivity_data['design_threshold']}")
    print(f"Thresholds analyzed: {sensitivity_data['thresholds_analyzed']}")
    print("\nClassifications at design threshold (0.10):")
    for status, count in sensitivity_data['summary']['classifications_at_design_threshold'].items():
        print(f"  {status}: {count}")
    
    # Identify configurations near the boundary
    near_boundary = [
        c for c in sensitivity_data['configurations'] 
        if c.get('near_boundary', False)
    ]
    print(f"\nConfigurations near the safety boundary: {len(near_boundary)}")
    if near_boundary:
        print("Files:")
        for c in near_boundary:
            print(f"  - {c['source_file']} (Type I rate: {c['type_i_rate']})")
    
    print("="*60)
    logger.info("Sensitivity analysis completed successfully.")

if __name__ == "__main__":
    main()