"""
Sensitivity analysis for clustering coefficient thresholds.
Implements the sensitivity sweep to verify how diffusion rates vary across thresholds.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from code.src.simulation.serialization import load_simulation_results
from code.src.utils.reproducibility import ensure_data_directory

logger = logging.getLogger(__name__)

class SensitivityError(Exception):
    """Custom exception for sensitivity analysis errors."""
    pass

def load_simulation_data(input_path: Path) -> pd.DataFrame:
    """
    Load simulation results and convert to DataFrame.

    Args:
        input_path: Path to simulation results JSON

    Returns:
        DataFrame with simulation results
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Simulation results not found: {input_path}")

    results = load_simulation_results(input_path)

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Filter out failed simulations
    df = df[df['status'] == 'SUCCESS']

    logger.info(f"Loaded {len(df)} valid simulation results")
    return df

def filter_by_clustering_threshold(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """
    Filter simulation results by clustering coefficient threshold.

    Args:
        df: DataFrame with simulation results
        threshold: Clustering coefficient threshold

    Returns:
        Filtered DataFrame
    """
    # Filter networks with clustering coefficient <= threshold
    filtered = df[df['avg_clustering'] <= threshold]
    logger.debug(f"Filtered to {len(filtered)} networks with clustering <= {threshold}")
    return filtered

def compute_sensitivity_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute sensitivity metrics for a filtered dataset.

    Args:
        df: Filtered DataFrame

    Returns:
        Dictionary with sensitivity metrics
    """
    if len(df) == 0:
        return {
            'count': 0,
            'mean_diffusion': None,
            'std_diffusion': None,
            'min_diffusion': None,
            'max_diffusion': None
        }

    diffusion_rates = df['diffusion_rate'].dropna()

    return {
        'count': len(diffusion_rates),
        'mean_diffusion': float(diffusion_rates.mean()) if len(diffusion_rates) > 0 else None,
        'std_diffusion': float(diffusion_rates.std()) if len(diffusion_rates) > 0 else None,
        'min_diffusion': float(diffusion_rates.min()) if len(diffusion_rates) > 0 else None,
        'max_diffusion': float(diffusion_rates.max()) if len(diffusion_rates) > 0 else None
    }

def run_sensitivity_sweep(
    df: pd.DataFrame,
    thresholds: Optional[List[float]] = None
) -> List[Dict[str, Any]]:
    """
    Run sensitivity sweep across clustering coefficient thresholds.

    Args:
        df: DataFrame with simulation results
        thresholds: List of thresholds to test (default: 5 distinct cutoffs)

    Returns:
        List of sensitivity results for each threshold
    """
    if thresholds is None:
        # Generate 5 distinct cutoffs as required by SC-005
        thresholds = [0.1, 0.3, 0.5, 0.7, 0.9]

    if len(thresholds) < 5:
        raise SensitivityError("SC-005 requires at least 5 distinct cutoffs")

    results = []

    for threshold in sorted(thresholds):
        filtered_df = filter_by_clustering_threshold(df, threshold)
        metrics = compute_sensitivity_metrics(filtered_df)

        result = {
            'threshold': threshold,
            **metrics
        }
        results.append(result)
        logger.info(f"Sensitivity at threshold {threshold}: {metrics['count']} networks, "
                   f"mean diffusion = {metrics['mean_diffusion']}")

    return results

def save_sensitivity_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save sensitivity sweep results to JSON.

    Args:
        results: List of sensitivity results
        output_path: Path to output file
    """
    ensure_data_directory(output_path)

    output = {
        'cutoffs': [r['threshold'] for r in results],
        'results': results,
        'timestamp': datetime.now().isoformat(),
        'total_thresholds': len(results)
    }

    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    logger.info(f"Saved sensitivity sweep results to {output_path}")

def verify_sensitivity_results(results: List[Dict[str, Any]]) -> bool:
    """
    Verify that sensitivity sweep results meet requirements.

    Args:
        results: List of sensitivity results

    Returns:
        True if requirements met, False otherwise
    """
    if len(results) < 5:
        logger.error("SC-005 violation: fewer than 5 cutoffs")
        return False

    cutoffs = [r['threshold'] for r in results]
    if len(set(cutoffs)) != len(cutoffs):
        logger.error("Duplicate cutoffs found")
        return False

    logger.info("Sensitivity sweep verification passed")
    return True

def main():
    """CLI entry point for sensitivity analysis."""
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description="Sensitivity analysis for clustering thresholds")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Config file path")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    parser.add_argument("--input", type=str, default="data/analysis/simulation_results.json",
                      help="Input simulation results file")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting sensitivity sweep analysis...")

    try:
        # Load simulation data
        input_path = Path(args.input)
        df = load_simulation_data(input_path)

        # Run sensitivity sweep
        thresholds = [0.1, 0.3, 0.5, 0.7, 0.9]
        results = run_sensitivity_sweep(df, thresholds)

        # Verify results
        if not verify_sensitivity_results(results):
            raise SensitivityError("Sensitivity sweep verification failed")

        # Save results
        output_path = Path(args.output) / "analysis" / "sensitivity_sweep.json"
        save_sensitivity_results(results, output_path)

        logger.info("Sensitivity sweep completed successfully")

    except Exception as e:
        logger.error(f"Sensitivity sweep failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
