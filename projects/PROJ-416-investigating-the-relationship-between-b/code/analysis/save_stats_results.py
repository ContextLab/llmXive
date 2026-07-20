"""
Module to save statistical analysis results to CSV.

This module handles the persistence of statistical outputs including
coefficients, p-values, VIF scores, power analysis results, and minimum
sample size requirements to data/metrics/statistical_results.csv.
"""
import csv
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from config import Config

logger = logging.getLogger(__name__)


def load_stats_results_from_dict(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert a dictionary of statistical results into a list of row dictionaries.
    
    Args:
        results: Dictionary containing statistical outputs. Expected keys:
            - 'model_name': Name of the statistical model
            - 'metric_name': The network metric being tested
            - 'coefficient': Regression coefficient
            - 'p_value': P-value from the test
            - 'vif': Variance Inflation Factor (if applicable)
            - 'power': Statistical power
            - 'min_n': Minimum sample size required
            - 'fdr_corrected': Whether FDR correction was applied
            - 'method': Analysis method used
    
    Returns:
        List of dictionaries, each representing a row for CSV output.
    """
    if not results:
        logger.warning("No statistical results provided to save.")
        return []
    
    # If results is already a list of rows, return as is
    if isinstance(results, list):
        return results
    
    # If it's a single dict, wrap it in a list
    if isinstance(results, dict):
        # Ensure it has the expected structure
        row = {
            'model_name': results.get('model_name', ''),
            'metric_name': results.get('metric_name', ''),
            'coefficient': results.get('coefficient', None),
            'p_value': results.get('p_value', None),
            'vif': results.get('vif', None),
            'power': results.get('power', None),
            'min_n': results.get('min_n', None),
            'fdr_corrected': results.get('fdr_corrected', False),
            'method': results.get('method', 'ancova_univariate'),
            'notes': results.get('notes', '')
        }
        return [row]
    
    logger.error(f"Unexpected results type: {type(results)}")
    return []


def save_stats_to_csv(
    results: Dict[str, Any], 
    output_path: Optional[str] = None,
    config: Optional[Config] = None
) -> Path:
    """
    Save statistical results to a CSV file.
    
    This function serializes statistical analysis outputs (coefficients, p-values,
    VIF, power calculations, minimum N) to a structured CSV file for downstream
    reporting and analysis.
    
    Args:
        results: Dictionary containing statistical outputs.
        output_path: Optional custom output path. If None, uses config defaults.
        config: Config object for path resolution.
    
    Returns:
        Path object pointing to the created CSV file.
    
    Raises:
        ValueError: If results is empty or malformed.
        IOError: If unable to write to the output path.
    """
    # Determine output path
    if output_path is None:
        if config is None:
            # Default fallback
            output_path = "data/metrics/statistical_results.csv"
        else:
            output_path = str(config.DATA_METRICS_DIR / "statistical_results.csv")
    
    output_path_obj = Path(output_path)
    
    # Ensure directory exists
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert results to list of rows
    rows = load_stats_results_from_dict(results)
    
    if not rows:
        logger.warning("No data to save. Creating empty CSV with headers.")
        rows = []
    
    # Define CSV headers
    fieldnames = [
        'model_name',
        'metric_name',
        'coefficient',
        'p_value',
        'vif',
        'power',
        'min_n',
        'fdr_corrected',
        'method',
        'notes'
    ]
    
    # Write to CSV
    try:
        with open(output_path_obj, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                # Ensure all keys exist, fill missing with empty string or None
                clean_row = {k: row.get(k, '') for k in fieldnames}
                writer.writerow(clean_row)
        
        logger.info(f"Statistical results saved to: {output_path_obj}")
        return output_path_obj
    
    except IOError as e:
        logger.error(f"Failed to write statistical results to {output_path_obj}: {e}")
        raise


def run_save_stats_results(
    results: Dict[str, Any],
    output_path: Optional[str] = None,
    config: Optional[Config] = None
) -> Path:
    """
    Wrapper function to save statistical results.
    
    This function orchestrates the saving process, handling path resolution
    and error logging.
    
    Args:
        results: Dictionary of statistical outputs.
        output_path: Optional custom output path.
        config: Config object for path resolution.
    
    Returns:
        Path to the saved CSV file.
    """
    return save_stats_to_csv(results, output_path, config)


def main():
    """
    CLI entry point for saving statistical results.
    
    Expects results to be provided via environment variables or a JSON file.
    For testing purposes, can accept a dummy input.
    """
    import argparse
    import json
    from utils.logging import setup_logging
    
    parser = argparse.ArgumentParser(
        description="Save statistical results to CSV."
    )
    parser.add_argument(
        "--input-json",
        type=str,
        help="Path to JSON file containing statistical results."
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Output path for CSV file."
    )
    parser.add_argument(
        "--dummy",
        action="store_true",
        help="Generate dummy results for testing."
    )
    
    args = parser.parse_args()
    setup_logging("save_stats_results")
    
    results = {}
    
    if args.dummy:
        logger.info("Generating dummy statistical results for testing.")
        results = {
            "model_name": "ancova_metric1",
            "metric_name": "modularity",
            "coefficient": 0.45,
            "p_value": 0.032,
            "vif": 1.2,
            "power": 0.75,
            "min_n": 24,
            "fdr_corrected": True,
            "method": "ancova_univariate",
            "notes": "Test run"
        }
    elif args.input_json:
        try:
            with open(args.input_json, 'r') as f:
                results = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load input JSON: {e}")
            return 1
    else:
        logger.error("No input provided. Use --input-json or --dummy.")
        return 1
    
    try:
        output_path = run_save_stats_results(results, args.output_path)
        logger.info(f"Successfully saved results to {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
