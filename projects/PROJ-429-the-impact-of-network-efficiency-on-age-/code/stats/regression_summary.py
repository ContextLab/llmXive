"""
T032: Create regression_summary.json with power analysis warnings.

This script generates a summary JSON file for the regression analysis.
It specifically checks the power analysis results and appends a warning
if the study is underpowered for cognitive analysis.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

from config import ensure_dirs, get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_regression_results(results_path: Path) -> Dict[str, Any]:
    """
    Load regression results from a JSON file.
    
    Args:
        results_path: Path to the regression results JSON file.
        
    Returns:
        Dictionary containing regression results.
    """
    if not results_path.exists():
        logger.warning(f"Regression results file not found: {results_path}")
        return {}
    
    try:
        with open(results_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse regression results JSON: {e}")
        return {}

def load_power_analysis(power_path: Path) -> Dict[str, Any]:
    """
    Load power analysis results from a JSON file.
    
    Args:
        power_path: Path to the power analysis JSON file.
        
    Returns:
        Dictionary containing power analysis results.
    """
    if not power_path.exists():
        logger.warning(f"Power analysis file not found: {power_path}")
        return {}
    
    try:
        with open(power_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse power analysis JSON: {e}")
        return {}

def generate_summary(
    regression_results: Dict[str, Any],
    power_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate the regression summary with warnings based on power analysis.
    
    Args:
        regression_results: Dictionary containing regression results.
        power_analysis: Dictionary containing power analysis results.
        
    Returns:
        Dictionary containing the regression summary.
    """
    warnings: List[str] = []
    
    # Check power analysis results
    if power_analysis:
        is_sufficient = power_analysis.get('is_sufficient', True)
        if not is_sufficient:
            warnings.append('Low Power for Cognitive Analysis')
            logger.warning("Power analysis indicates insufficient power for cognitive analysis.")
    
    # Add other potential warnings based on regression results
    if not regression_results:
        warnings.append('No regression results available')
        logger.warning("No regression results found to summarize.")
    
    summary = {
        'warnings': warnings,
        'power_analysis_status': power_analysis.get('is_sufficient', 'unknown'),
        'regression_results_available': bool(regression_results),
        'summary_generated_at': get_config_summary().get('timestamp', 'unknown')
    }
    
    return summary

def main():
    """
    Main entry point for generating the regression summary.
    """
    config = get_config_summary()
    project_root = Path(config['project_root'])
    
    # Define paths
    regression_results_path = project_root / 'data' / 'results' / 'regression_results.json'
    power_analysis_path = project_root / 'data' / 'results' / 'power_analysis.json'
    summary_output_path = project_root / 'data' / 'results' / 'regression_summary.json'
    
    # Ensure output directory exists
    ensure_dirs([summary_output_path.parent])
    
    logger.info(f"Loading regression results from: {regression_results_path}")
    regression_results = load_regression_results(regression_results_path)
    
    logger.info(f"Loading power analysis from: {power_analysis_path}")
    power_analysis = load_power_analysis(power_analysis_path)
    
    logger.info("Generating regression summary...")
    summary = generate_summary(regression_results, power_analysis)
    
    # Write summary to file
    try:
        with open(summary_output_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Regression summary written to: {summary_output_path}")
    except IOError as e:
        logger.error(f"Failed to write regression summary: {e}")
        sys.exit(1)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
