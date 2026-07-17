"""
Sensitivity analysis module for investigating the impact of clustering coefficient thresholds
on energy transfer dynamics in spin systems.

This module implements a sensitivity sweep that filters simulation results by varying
clustering coefficient thresholds and computes sensitivity metrics for each threshold.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from code.src.utils.reproducibility import ensure_data_directory

logger = logging.getLogger(__name__)


def load_simulation_data(
    results_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load simulation results from the analysis directory.

    Args:
        results_path: Path to simulation_results.json. If None, uses default location.

    Returns:
        DataFrame containing simulation results with clustering coefficients and diffusion rates.

    Raises:
        FileNotFoundError: If the simulation results file does not exist.
        ValueError: If the file is empty or has invalid format.
    """
    if results_path is None:
        results_path = Path("data/analysis/simulation_results.json")

    if not results_path.exists():
        raise FileNotFoundError(
            f"Simulation results file not found at {results_path}. "
            "Run the simulation pipeline first."
        )

    with open(results_path, "r") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Simulation results must be a list of records.")

    if len(data) == 0:
        raise ValueError("Simulation results file is empty.")

    df = pd.DataFrame(data)

    # Verify required columns exist
    required_cols = ["network_id", "clustering_coefficient", "diffusion_rate", "topology_class"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info(f"Loaded {len(df)} simulation records from {results_path}")
    return df


def filter_by_clustering_threshold(
    df: pd.DataFrame,
    threshold: float,
    operator: str = "ge"
) -> pd.DataFrame:
    """
    Filter simulation results by clustering coefficient threshold.

    Args:
        df: DataFrame of simulation results.
        threshold: Clustering coefficient threshold value.
        operator: Comparison operator ('ge' for >=, 'le' for <=, 'eq' for ==).

    Returns:
        Filtered DataFrame containing only records meeting the threshold criteria.
    """
    if operator == "ge":
        filtered = df[df["clustering_coefficient"] >= threshold]
    elif operator == "le":
        filtered = df[df["clustering_coefficient"] <= threshold]
    elif operator == "eq":
        filtered = df[np.isclose(df["clustering_coefficient"], threshold)]
    else:
        raise ValueError(f"Unknown operator: {operator}. Use 'ge', 'le', or 'eq'.")

    logger.debug(
        f"Filtered to {len(filtered)} records with clustering {operator} {threshold}"
    )
    return filtered


def compute_sensitivity_metrics(
    df: pd.DataFrame,
    threshold: float
) -> Dict[str, Any]:
    """
    Compute sensitivity metrics for a given clustering coefficient threshold.

    Args:
        df: Filtered DataFrame of simulation results.
        threshold: The clustering coefficient threshold used for filtering.

    Returns:
        Dictionary containing sensitivity metrics including:
        - sample_size: Number of networks in the filtered set
        - mean_diffusion_rate: Average diffusion rate
        - std_diffusion_rate: Standard deviation of diffusion rates
        - min_diffusion_rate: Minimum diffusion rate
        - max_diffusion_rate: Maximum diffusion rate
        - variance: Variance of diffusion rates
        - threshold: The threshold value used
    """
    if len(df) == 0:
        return {
            "threshold": threshold,
            "sample_size": 0,
            "mean_diffusion_rate": np.nan,
            "std_diffusion_rate": np.nan,
            "min_diffusion_rate": np.nan,
            "max_diffusion_rate": np.nan,
            "variance": np.nan,
            "topology_distribution": {}
        }

    diffusion_rates = df["diffusion_rate"].values

    # Compute topology distribution
    topology_counts = df["topology_class"].value_counts().to_dict()

    return {
        "threshold": float(threshold),
        "sample_size": int(len(df)),
        "mean_diffusion_rate": float(np.mean(diffusion_rates)),
        "std_diffusion_rate": float(np.std(diffusion_rates)),
        "min_diffusion_rate": float(np.min(diffusion_rates)),
        "max_diffusion_rate": float(np.max(diffusion_rates)),
        "variance": float(np.var(diffusion_rates)),
        "topology_distribution": topology_counts
    }


def run_sensitivity_sweep(
    df: pd.DataFrame,
    thresholds: Optional[List[float]] = None,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Run a sensitivity sweep over clustering coefficient thresholds.

    This function filters the simulation data by multiple clustering coefficient
    thresholds and computes sensitivity metrics for each threshold.

    Args:
        df: DataFrame of simulation results.
        thresholds: List of clustering coefficient thresholds to sweep.
                   If None, uses default 5 thresholds: [0.0, 0.2, 0.4, 0.6, 0.8].
        output_path: Path to save the sensitivity sweep results. If None,
                    results are returned but not saved.

    Returns:
        List of dictionaries containing sensitivity metrics for each threshold.

    Raises:
        ValueError: If fewer than 5 thresholds are provided or if the data
                   is insufficient for meaningful analysis.
    """
    if thresholds is None:
        # Default thresholds: 5 distinct cutoffs as required by SC-005
        thresholds = [0.0, 0.2, 0.4, 0.6, 0.8]

    if len(thresholds) < 5:
        raise ValueError(
            f"SC-005 requires at least 5 distinct cutoffs. "
            f"Received {len(thresholds)} thresholds."
        )

    # Verify thresholds are in valid range [0, 1]
    for t in thresholds:
        if not (0.0 <= t <= 1.0):
            raise ValueError(
                f"Clustering coefficient threshold {t} is out of valid range [0, 1]."
            )

    logger.info(f"Starting sensitivity sweep with {len(thresholds)} thresholds: {thresholds}")

    results = []
    for threshold in sorted(thresholds):
        filtered_df = filter_by_clustering_threshold(df, threshold, operator="ge")
        metrics = compute_sensitivity_metrics(filtered_df, threshold)
        results.append(metrics)
        logger.debug(
            f"Threshold {threshold}: {metrics['sample_size']} samples, "
            f"mean diffusion = {metrics['mean_diffusion_rate']:.4f}"
        )

    # Verify we have results for all thresholds
    if len(results) != len(thresholds):
        raise RuntimeError(
            f"Expected {len(thresholds)} results, got {len(results)}"
        )

    logger.info(f"Sensitivity sweep complete. Computed metrics for {len(results)} thresholds.")

    # Save results if output path provided
    if output_path is not None:
        save_sensitivity_results(results, output_path)

    return results


def save_sensitivity_results(
    results: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save sensitivity sweep results to a JSON file.

    Args:
        results: List of sensitivity metric dictionaries.
        output_path: Path to save the results file.
    """
    ensure_data_directory(output_path)

    # Verify content before saving
    if len(results) < 5:
        raise ValueError(
            f"SC-005 requires at least 5 cutoffs in sensitivity sweep. "
            f"Got {len(results)} results."
        )

    # Verify all thresholds are distinct
    thresholds = [r["threshold"] for r in results]
    if len(thresholds) != len(set(thresholds)):
        raise ValueError("Duplicate thresholds detected in sensitivity sweep results.")

    output_data = {
        "sweep_parameters": {
            "num_thresholds": len(results),
            "thresholds": thresholds,
            "operator": "ge"
        },
        "results": results,
        "verification": {
            "meets_sc005": len(results) >= 5,
            "all_thresholds_distinct": len(thresholds) == len(set(thresholds)),
            "thresholds_in_valid_range": all(0.0 <= t <= 1.0 for t in thresholds)
        },
        "metadata": {
            "generated_by": "sensitivity.py::run_sensitivity_sweep",
            "timestamp": None  # Will be set by caller if needed
        }
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Saved sensitivity sweep results to {output_path}")


def main() -> None:
    """
    Main entry point for running the sensitivity sweep analysis.

    This function:
    1. Loads simulation results from data/analysis/simulation_results.json
    2. Runs a sensitivity sweep over clustering coefficient thresholds
    3. Saves results to data/analysis/sensitivity_sweep.json
    4. Verifies the output meets SC-005 requirements (≥5 cutoffs)
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Define paths
    simulation_results_path = Path("data/analysis/simulation_results.json")
    sensitivity_output_path = Path("data/analysis/sensitivity_sweep.json")

    try:
        # Load simulation data
        logger.info(f"Loading simulation results from {simulation_results_path}")
        df = load_simulation_data(simulation_results_path)

        # Define default thresholds (5 distinct cutoffs)
        thresholds = [0.0, 0.2, 0.4, 0.6, 0.8]

        # Run sensitivity sweep
        logger.info(f"Running sensitivity sweep with thresholds: {thresholds}")
        results = run_sensitivity_sweep(
            df,
            thresholds=thresholds,
            output_path=sensitivity_output_path
        )

        # Verify results
        verification = {
            "num_cutoffs": len(results),
            "meets_minimum": len(results) >= 5,
            "thresholds": [r["threshold"] for r in results]
        }

        if verification["meets_minimum"]:
            logger.info(
                f"✓ SC-005 VERIFIED: Sensitivity sweep contains {len(results)} "
                f"cutoffs (minimum 5 required)"
            )
        else:
            logger.error(
                f"✗ SC-005 FAILED: Sensitivity sweep contains only {len(results)} "
                f"cutoffs (minimum 5 required)"
            )

        logger.info(f"Sensitivity sweep analysis complete. Results saved to {sensitivity_output_path}")

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        logger.error("Please run the simulation pipeline first to generate simulation_results.json")
        raise
    except Exception as e:
        logger.error(f"Error during sensitivity sweep: {e}")
        raise


if __name__ == "__main__":
    main()
