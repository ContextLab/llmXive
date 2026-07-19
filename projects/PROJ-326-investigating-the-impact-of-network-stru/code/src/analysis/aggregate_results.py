"""
Data aggregation and filtering module for User Story 3.

This module loads simulation results, filters out invalid runs (divergence,
disconnected networks), and aggregates metrics for downstream analysis.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from code.src.utils.logging import log_metric

logger = logging.getLogger(__name__)

# Constants for status filtering
STATUS_EXCLUDED = [
    "[SIMULATION_DIVERGENCE]",
    "[DISCONNECTED_NETWORK_FAILURE]"
]

def load_simulation_results(file_path: str) -> pd.DataFrame:
    """
    Load simulation results from a JSON file into a pandas DataFrame.

    Args:
        file_path: Path to the simulation_results.json file.

    Returns:
        DataFrame containing the simulation results.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Simulation results file not found: {file_path}")

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        # Handle case where data might be wrapped in a dict, e.g., {"results": [...]}
        if isinstance(data, dict) and 'results' in data:
            data = data['results']
        else:
            raise ValueError(f"Expected list of results in {file_path}, got {type(data)}")

    if len(data) == 0:
        raise ValueError(f"Simulation results file is empty: {file_path}")

    df = pd.DataFrame(data)
    logger.info(f"Loaded {len(df)} simulation results from {file_path}")
    return df

def filter_valid_runs(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Filter out runs with excluded status codes.

    Args:
        df: DataFrame of simulation results.

    Returns:
        Tuple of (filtered DataFrame, count of excluded runs).
    """
    if 'status' not in df.columns:
        logger.warning("No 'status' column found in simulation results. Assuming all valid.")
        return df, 0

    initial_count = len(df)
    # Filter rows where status is NOT in the excluded list
    # Handle potential NaN values in status column
    mask = df['status'].apply(lambda x: x not in STATUS_EXCLUDED if isinstance(x, str) else True)
    filtered_df = df[mask]
    excluded_count = initial_count - len(filtered_df)

    if excluded_count > 0:
        logger.info(f"Filtered out {excluded_count} runs with excluded status: {STATUS_EXCLUDED}")
    else:
        logger.info("No runs excluded based on status.")

    return filtered_df, excluded_count

def aggregate_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute aggregated metrics (mean, median, variance) for numeric columns.

    Args:
        df: Filtered DataFrame of simulation results.

    Returns:
        Dictionary containing aggregated metrics per numeric column.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_cols:
        logger.warning("No numeric columns found to aggregate.")
        return {}

    aggregated = {}
    for col in numeric_cols:
        values = df[col].dropna()
        if len(values) == 0:
            continue

        aggregated[col] = {
            "count": int(len(values)),
            "mean": float(values.mean()),
            "median": float(values.median()),
            "variance": float(values.var()),
            "std": float(values.std()),
            "min": float(values.min()),
            "max": float(values.max())
        }

    logger.info(f"Aggregated metrics for {len(numeric_cols)} numeric columns.")
    return aggregated

def aggregate_results(
    input_path: str,
    output_path: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main function to load, filter, and aggregate simulation results.

    Args:
        input_path: Path to simulation_results.json.
        output_path: Path to save aggregated_results.json.
        config: Optional configuration dictionary.

    Returns:
        Dictionary containing the full aggregated result structure.
    """
    logger.info(f"Starting aggregation for {input_path}")

    # Load data
    df = load_simulation_results(input_path)

    # Filter data
    valid_df, excluded_count = filter_valid_runs(df)

    if len(valid_df) == 0:
        logger.error("No valid runs remaining after filtering. Aborting aggregation.")
        raise ValueError("No valid runs found after filtering. Check input data and status codes.")

    # Aggregate metrics
    metrics = aggregate_metrics(valid_df)

    # Group by topology class if available
    topology_groups = {}
    if 'topology_class' in valid_df.columns:
        for topo in valid_df['topology_class'].unique():
            if pd.isna(topo):
                continue
            topo_df = valid_df[valid_df['topology_class'] == topo]
            topo_metrics = aggregate_metrics(topo_df)
            topology_groups[str(topo)] = topo_metrics
        logger.info(f"Grouped metrics by {len(topology_groups)} topology classes.")

    # Construct final result
    result = {
        "total_input_records": len(df),
        "valid_records": len(valid_df),
        "excluded_records": excluded_count,
        "excluded_statuses": STATUS_EXCLUDED,
        "aggregated_metrics": metrics,
        "topology_specific_metrics": topology_groups,
        "status": "SUCCESS"
    }

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Aggregated results saved to {output_path}")
    return result

def main():
    """Entry point for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Aggregate simulation results")
    parser.add_argument(
        "--input",
        type=str,
        default="data/analysis/simulation_results.json",
        help="Path to simulation_results.json"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/analysis/aggregated_results.json",
        help="Path to save aggregated_results.json"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to config file (optional)"
    )

    args = parser.parse_args()

    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        result = aggregate_results(args.input, args.output)
        print(f"Aggregation complete. Valid records: {result['valid_records']}")
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        raise

if __name__ == "__main__":
    main()
