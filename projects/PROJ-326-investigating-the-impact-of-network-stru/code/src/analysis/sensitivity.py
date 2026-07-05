"""
Sensitivity Analysis Module for Network Topology Energy Transfer Study.

This module implements a sensitivity sweep for clustering coefficient thresholds
to analyze how the correlation between network topology and energy diffusion
rates varies across different structural regimes.

Outputs:
    data/analysis/sensitivity_sweep.json: Results of the sensitivity sweep
        containing metrics for each clustering coefficient threshold.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats

from code.src.utils.config import load_config, get_config_value
from code.src.utils.io import compute_file_checksum
from code.src.analysis.regression import analyze_correlation, RegressionResult
from code.src.simulation.schema import load_results

# Configure logging
logger = logging.getLogger(__name__)

# Default thresholds if not specified in config
DEFAULT_THRESHOLDS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
MIN_RESULTS_THRESHOLD = 5  # SC-005: At least 5 distinct cutoffs

def load_simulation_data(results_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load simulation results from the JSON file.

    Args:
        results_path: Path to simulation_results.json. If None, uses default path.

    Returns:
        DataFrame containing simulation results with clustering coefficients.
    """
    if results_path is None:
        config = load_config()
        results_path = Path(get_config_value(config, "paths.analysis_results"))

    if not results_path.exists():
        raise FileNotFoundError(f"Simulation results not found at {results_path}. "
                                "Run simulation first to generate data.")

    results = load_results(results_path)
    df = pd.DataFrame(results)

    # Ensure clustering coefficient column exists
    if 'clustering_coefficient' not in df.columns:
        # Try to compute from metadata if available
        logger.warning("Clustering coefficient not found in results. "
                     "Attempting to load from metadata.")
        # Fallback: would need to join with metadata if available
        raise ValueError("Clustering coefficient data is missing from results. "
                       "Ensure generators log clustering metrics.")

    return df

def filter_by_clustering_threshold(
    df: pd.DataFrame,
    threshold: float,
    direction: str = "above"
) -> pd.DataFrame:
    """
    Filter simulation results based on clustering coefficient threshold.

    Args:
        df: DataFrame with simulation results.
        threshold: Clustering coefficient threshold value.
        direction: "above" (>= threshold) or "below" (<= threshold).

    Returns:
        Filtered DataFrame.
    """
    if direction == "above":
        return df[df['clustering_coefficient'] >= threshold]
    elif direction == "below":
        return df[df['clustering_coefficient'] <= threshold]
    else:
        raise ValueError(f"Invalid direction: {direction}. Use 'above' or 'below'.")

def compute_sensitivity_metrics(
    df_filtered: pd.DataFrame,
    threshold: float,
    direction: str = "above"
) -> Dict[str, Any]:
    """
    Compute sensitivity metrics for a given clustering threshold.

    Analyzes the relationship between clustering coefficient and diffusion rate
    within the filtered subset of data.

    Args:
        df_filtered: Filtered DataFrame.
        threshold: The clustering coefficient threshold used.
        direction: Filter direction used.

    Returns:
        Dictionary containing sensitivity metrics.
    """
    metrics = {
        "threshold": threshold,
        "direction": direction,
        "sample_size": len(df_filtered),
        "mean_clustering": float(df_filtered['clustering_coefficient'].mean()) if len(df_filtered) > 0 else None,
        "std_clustering": float(df_filtered['clustering_coefficient'].std()) if len(df_filtered) > 0 else None,
        "mean_diffusion_rate": float(df_filtered['diffusion_rate'].mean()) if len(df_filtered) > 0 else None,
        "std_diffusion_rate": float(df_filtered['diffusion_rate'].std()) if len(df_filtered) > 0 else None,
        "topology_distribution": {}
    }

    # Compute topology distribution in this subset
    if 'topology_class' in df_filtered.columns:
        topology_counts = df_filtered['topology_class'].value_counts().to_dict()
        metrics['topology_distribution'] = {str(k): int(v) for k, v in topology_counts.items()}

    # Perform correlation analysis if sufficient data
    if len(df_filtered) >= 3 and 'diffusion_rate' in df_filtered.columns:
        try:
            corr_result = analyze_correlation(
                df_filtered['clustering_coefficient'].values,
                df_filtered['diffusion_rate'].values
            )
            metrics['correlation'] = {
                "pearson_r": float(corr_result.pearson_r),
                "p_value": float(corr_result.p_value),
                "sample_size": corr_result.sample_size,
                "significant": corr_result.p_value < 0.05
            }

            # Store effect size if available
            if hasattr(corr_result, 'effect_size') and corr_result.effect_size is not None:
                metrics['correlation']['effect_size'] = float(corr_result.effect_size)

        except Exception as e:
            logger.warning(f"Correlation analysis failed for threshold {threshold}: {e}")
            metrics['correlation'] = {
                "error": str(e),
                "pearson_r": None,
                "p_value": None,
                "significant": False
            }
    else:
        metrics['correlation'] = {
            "note": "Insufficient data for correlation analysis",
            "pearson_r": None,
            "p_value": None,
            "significant": False
        }

    return metrics

def run_sensitivity_sweep(
    df: pd.DataFrame,
    thresholds: Optional[List[float]] = None,
    output_path: Optional[Path] = None,
    direction: str = "above"
) -> Dict[str, Any]:
    """
    Execute a full sensitivity sweep across clustering coefficient thresholds.

    This function:
    1. Iterates through each clustering coefficient threshold
    2. Filters the simulation data based on the threshold
    3. Computes correlation metrics for the filtered subset
    4. Aggregates results into a comprehensive sensitivity report

    Args:
        df: DataFrame with simulation results.
        thresholds: List of clustering coefficient thresholds to sweep.
                   Defaults to DEFAULT_THRESHOLDS.
        output_path: Path to save the results JSON. If None, uses default path.
        direction: Filter direction ("above" or "below").

    Returns:
        Dictionary containing the complete sensitivity sweep results.
    """
    if thresholds is None:
        config = load_config()
        thresholds = get_config_value(config, "sensitivity.thresholds", DEFAULT_THRESHOLDS)

    # Validate thresholds
    if not isinstance(thresholds, list) or len(thresholds) < MIN_RESULTS_THRESHOLD:
        raise ValueError(f"Thresholds must be a list with at least {MIN_RESULTS_THRESHOLD} values. "
                       f"Got {len(thresholds) if isinstance(thresholds, list) else 'non-list'}.")

    if output_path is None:
        config = load_config()
        output_path = Path(get_config_value(config, "paths.sensitivity_results"))

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting sensitivity sweep with {len(thresholds)} thresholds")
    logger.info(f"Thresholds: {thresholds}")

    results = {
        "metadata": {
            "analysis_type": "sensitivity_sweep",
            "parameter": "clustering_coefficient",
            "direction": direction,
            "thresholds_used": thresholds,
            "total_thresholds": len(thresholds),
            "input_file": str(df.index.name or "memory"),
            "timestamp": pd.Timestamp.now().isoformat(),
        },
        "threshold_results": [],
        "summary": {}
    }

    failed_thresholds = []

    for threshold in thresholds:
        try:
            logger.info(f"Processing threshold: {threshold}")

            # Filter data
            df_filtered = filter_by_clustering_threshold(df, threshold, direction)

            # Compute metrics
            metrics = compute_sensitivity_metrics(df_filtered, threshold, direction)

            results["threshold_results"].append(metrics)

            logger.debug(f"  Sample size: {metrics['sample_size']}, "
                       f"Correlation: {metrics['correlation'].get('pearson_r', 'N/A')}")

        except Exception as e:
            logger.error(f"Failed to process threshold {threshold}: {e}")
            failed_thresholds.append({
                "threshold": threshold,
                "error": str(e)
            })

    # Add failure summary
    if failed_thresholds:
        results["failed_thresholds"] = failed_thresholds
        logger.warning(f"Failed to process {len(failed_thresholds)} thresholds")

    # Compute summary statistics
    valid_results = [r for r in results["threshold_results"] if r["sample_size"] > 0]

    if valid_results:
        # Find threshold with strongest correlation
        correlations = [
            r["correlation"]["pearson_r"]
            for r in valid_results
            if r["correlation"].get("pearson_r") is not None
        ]

        if correlations:
            max_abs_corr_idx = np.argmax(np.abs(correlations))
            best_threshold = valid_results[max_abs_corr_idx]["threshold"]
            best_corr = correlations[max_abs_corr_idx]

            results["summary"] = {
                "total_thresholds_processed": len(valid_results),
                "thresholds_with_data": len(valid_results),
                "best_correlation_threshold": best_threshold,
                "best_correlation_value": float(best_corr),
                "mean_sample_size": float(np.mean([r["sample_size"] for r in valid_results])),
                "min_sample_size": int(np.min([r["sample_size"] for r in valid_results])),
                "max_sample_size": int(np.max([r["sample_size"] for r in valid_results])),
            }

            # Check if any correlation is statistically significant
            significant_count = sum(
                1 for r in valid_results
                if r["correlation"].get("significant", False)
            )
            results["summary"]["significant_correlations_count"] = significant_count

    # Validate SC-005: At least 5 distinct cutoffs with results
    if len(results["threshold_results"]) < MIN_RESULTS_THRESHOLD:
        logger.warning(f"SC-005 violation: Only {len(results['threshold_results'])} thresholds processed, "
                     f"minimum required is {MIN_RESULTS_THRESHOLD}")

    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    # Compute checksum for integrity
    checksum = compute_file_checksum(output_path)
    results["metadata"]["output_checksum"] = checksum

    # Update file with checksum
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Sensitivity sweep complete. Results saved to {output_path}")
    logger.info(f"Processed {len(results['threshold_results'])} thresholds")

    return results

def main():
    """
    Entry point for the sensitivity sweep script.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Load simulation data
        logger.info("Loading simulation data...")
        df = load_simulation_data()
        logger.info(f"Loaded {len(df)} simulation results")

        # Run sensitivity sweep
        logger.info("Running sensitivity sweep...")
        results = run_sensitivity_sweep(df)

        # Print summary
        print(f"\nSensitivity Sweep Complete")
        print(f"==========================")
        print(f"Thresholds processed: {results['metadata']['total_thresholds']}")
        print(f"Thresholds with data: {results['summary'].get('thresholds_with_data', 0)}")

        if 'best_correlation_threshold' in results['summary']:
            print(f"Best correlation threshold: {results['summary']['best_correlation_threshold']}")
            print(f"Best correlation value: {results['summary']['best_correlation_value']:.4f}")

        print(f"\nResults saved to: {results['metadata']['output_path']}")

        # Verify SC-005
        if len(results['threshold_results']) >= MIN_RESULTS_THRESHOLD:
            print(f"\n✓ SC-005 Verified: {len(results['threshold_results'])} thresholds (≥ {MIN_RESULTS_THRESHOLD})")
        else:
            print(f"\n✗ SC-005 FAILED: Only {len(results['threshold_results'])} thresholds (need ≥ {MIN_RESULTS_THRESHOLD})")

    except FileNotFoundError as e:
        logger.error(str(e))
        print(f"\nError: {e}")
        print("Please run the simulation first to generate the required data.")
        return 1
    except Exception as e:
        logger.error(f"Sensitivity sweep failed: {e}", exc_info=True)
        print(f"\nError: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
