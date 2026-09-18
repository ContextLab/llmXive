"""
Sensitivity analysis module for p-value threshold evaluation.

This module provides utilities to perform sensitivity analysis across
varying significance levels (p-value thresholds) to assess the robustness
of statistical findings.

FR-009: Implement p-value threshold sensitivity analysis.
"""

import sys
import logging
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd

# Configure logger for this module
logger = logging.getLogger(__name__)


def setup_logger_module(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a logger for the module.

    Args:
        name: Logger name (usually __name__)
        level: Logging level

    Returns:
        Configured logger instance
    """
    log = logging.getLogger(name)
    log.setLevel(level)
    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        log.addHandler(handler)
    return log


def run_sensitivity_analysis(
    correlation_results: Union[pd.DataFrame, Dict],
    p_value_columns: List[str],
    thresholds: List[float] = [0.01, 0.05, 0.1],
    target_column: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis across multiple p-value thresholds.

    This function evaluates how the number of significant correlations
    (or other metrics) varies as the significance threshold changes.

    Args:
        correlation_results: DataFrame or dict containing correlation results
                            with p-values. Expected columns include p-values
                            for each correlation pair.
        p_value_columns: List of column names containing p-values to evaluate.
        thresholds: List of p-value thresholds to evaluate (default: [0.01, 0.05, 0.1]).
        target_column: Optional column name to focus on (e.g., 'thermal_conductivity').
                       If None, all correlations are evaluated.

    Returns:
        Dictionary containing sensitivity analysis results with keys:
            - 'thresholds': list of thresholds evaluated
            - 'results': dict mapping each threshold to a dict of:
                - 'significant_count': number of correlations below threshold
                - 'significant_pairs': list of (feature, target) pairs
                - 'correlation_values': dict of correlation coefficients for significant pairs
            - 'summary': summary statistics across thresholds

    Raises:
        ValueError: If correlation_results is empty or p_value_columns not found
        TypeError: If correlation_results is not a DataFrame or dict
    """
    log = setup_logger_module(__name__)
    log.info(f"Starting sensitivity analysis with thresholds: {thresholds}")

    # Convert dict to DataFrame if needed
    if isinstance(correlation_results, dict):
        df = pd.DataFrame(correlation_results)
    elif isinstance(correlation_results, pd.DataFrame):
        df = correlation_results.copy()
    else:
        raise TypeError("correlation_results must be a DataFrame or dict")

    if df.empty:
        raise ValueError("correlation_results is empty")

    # Validate p-value columns exist
    missing_cols = [col for col in p_value_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"P-value columns not found in DataFrame: {missing_cols}")

    results = {}

    for threshold in thresholds:
        log.info(f"Evaluating threshold: {threshold}")

        # Count significant correlations (p < threshold)
        significant_mask = df[p_value_columns] < threshold

        # Get count of significant correlations
        significant_count = significant_mask.sum().sum()

        # Extract significant pairs and their values
        significant_pairs = []
        correlation_values = {}

        for col in p_value_columns:
            mask = significant_mask[col]
            if mask.any():
                for idx in df[mask].index:
                    pair = (idx, col)
                    significant_pairs.append(pair)
                    # Get correlation coefficient if available
                    corr_col = col.replace('p_value', 'correlation')
                    if corr_col in df.columns:
                        correlation_values[str(pair)] = df.loc[idx, corr_col]
                    else:
                        # Try to infer correlation column name
                        correlation_values[str(pair)] = None

        results[str(threshold)] = {
            'significant_count': int(significant_count),
            'significant_pairs': significant_pairs,
            'correlation_values': correlation_values
        }

    # Generate summary
    summary = {
        'total_thresholds': len(thresholds),
        'min_significant': min(r['significant_count'] for r in results.values()),
        'max_significant': max(r['significant_count'] for r in results.values()),
        'thresholds_evaluated': thresholds
    }

    log.info(f"Sensitivity analysis complete. Significant counts: {results}")

    return {
        'thresholds': thresholds,
        'results': results,
        'summary': summary
    }


def save_sensitivity_report(
    sensitivity_results: Dict[str, Any],
    output_path: Union[str, Path]
) -> None:
    """
    Save sensitivity analysis results to a JSON file.

    Args:
        sensitivity_results: Dictionary containing sensitivity analysis results
        output_path: Path to save the JSON report
    """
    log = setup_logger_module(__name__)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sensitivity_results, f, indent=2, default=str)

    log.info(f"Sensitivity report saved to {output_path}")


def main() -> None:
    """
    Main entry point for sensitivity analysis CLI.

    Usage:
        python -m src.utils.sensitivity --input data/results/correlation_matrix.json
                                       --output data/results/sensitivity_analysis.json
                                       --thresholds 0.01 0.05 0.1
    """
    parser = argparse.ArgumentParser(
        description='Perform p-value threshold sensitivity analysis'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        required=True,
        help='Input JSON file containing correlation results'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Output JSON file for sensitivity analysis report'
    )
    parser.add_argument(
        '--thresholds', '-t',
        type=float,
        nargs='+',
        default=[0.01, 0.05, 0.1],
        help='P-value thresholds to evaluate (default: 0.01 0.05 0.1)'
    )
    parser.add_argument(
        '--p-value-columns', '-p',
        type=str,
        nargs='+',
        default=['p_value'],
        help='Column names containing p-values (default: p_value)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    args = parser.parse_args()

    # Initialize seed
    np.random.seed(args.seed)
    random_state = args.seed

    log = setup_logger_module(__name__)
    log.info(f"Running sensitivity analysis with seed: {random_state}")

    # Load input data
    input_path = Path(args.input)
    if not input_path.exists():
        log.error(f"Input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, 'r', encoding='utf-8') as f:
        correlation_data = json.load(f)

    # Run sensitivity analysis
    try:
        results = run_sensitivity_analysis(
            correlation_results=correlation_data,
            p_value_columns=args.p_value_columns,
            thresholds=args.thresholds
        )
    except (ValueError, TypeError) as e:
        log.error(f"Sensitivity analysis failed: {e}")
        sys.exit(1)

    # Save report
    save_sensitivity_report(results, args.output)
    log.info("Sensitivity analysis completed successfully")


if __name__ == '__main__':
    main()
