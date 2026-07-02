import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from config import load_config, ensure_directories
from logging_config import setup_logging
from model import run_initial_correlations

logger = logging.getLogger(__name__)

def save_regression_results(results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save regression results to a JSON file.

    Args:
        results: Dictionary containing regression coefficients, p-values, and diagnostics.
        output_path: Optional path to save the file. Defaults to config output path.

    Returns:
        Path to the saved file.
    """
    config = load_config()
    if output_path is None:
        output_dir = config.get('output_dir', 'outputs')
        ensure_directories([output_dir])
        output_path = Path(output_dir) / 'regression_results.json'
    else:
        ensure_directories([output_path.parent])

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Regression results saved to {output_path}")
    return output_path

def save_correlation_results(results: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save correlation results to a JSON file.

    Args:
        results: Dictionary containing correlation coefficients, p-values, and methods.
        output_path: Optional path to save the file. Defaults to config output path.

    Returns:
        Path to the saved file.
    """
    config = load_config()
    if output_path is None:
        output_dir = config.get('output_dir', 'outputs')
        ensure_directories([output_dir])
        output_path = Path(output_dir) / 'correlation_results.json'
    else:
        ensure_directories([output_path.parent])

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Correlation results saved to {output_path}")
    return output_path

def main():
    """
    Main entry point to run correlation analysis and save results.
    """
    setup_logging()
    config = load_config()
    ensure_directories([config.get('output_dir', 'outputs')])

    logger.info("Starting correlation analysis and result saving...")

    # Run the correlation analysis which returns the results dictionary
    correlation_results = run_initial_correlations()

    # Save the correlation results to JSON
    save_correlation_results(correlation_results)

    logger.info("Correlation analysis and saving completed successfully.")

if __name__ == "__main__":
    main()