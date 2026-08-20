"""
T030a: Output correlation statistics.

Computes and saves Kendall's tau, p-values, and CI width for the water abundance
vs temperature correlation analysis.

This task depends on T025b (censored Kendall's tau) and T025c (bootstrap CI).
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

# Import existing functions from analysis.py
from analysis import compute_censored_kendall_tau, run_bootstrap_ci

# Import config
from config import get_config

logger = logging.getLogger(__name__)


def load_correlation_results(
    input_dir: Path,
    bootstrap_file: str = "bootstrap_ci.json",
    retrieval_file: str = "retrieval_results.csv",
    metadata_file: str = "metadata.csv"
) -> Dict[str, Any]:
    """
    Load necessary data to compute correlation statistics.
    
    Args:
        input_dir: Directory containing processed data files.
        bootstrap_file: Filename for bootstrap CI results.
        retrieval_file: Filename for retrieval results.
        metadata_file: Filename for metadata.
        
    Returns:
        Dictionary containing merged analysis data and bootstrap results.
    """
    # Load bootstrap CI results
    bootstrap_path = input_dir / bootstrap_file
    if not bootstrap_path.exists():
        raise FileNotFoundError(f"Bootstrap CI file not found: {bootstrap_path}")
    
    with open(bootstrap_path, 'r') as f:
        bootstrap_data = json.load(f)
    
    # Load retrieval results
    retrieval_path = input_dir / retrieval_file
    if not retrieval_path.exists():
        raise FileNotFoundError(f"Retrieval results file not found: {retrieval_path}")
    
    retrieval_df = pd.read_csv(retrieval_path)
    
    # Load metadata
    metadata_path = input_dir / metadata_file
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    metadata_df = pd.read_csv(metadata_path)
    
    # Merge retrieval results with metadata
    merged_df = pd.merge(
        retrieval_df,
        metadata_df[['planet_name', 'temperature', 'metallicity', 'snr', 'resolution', 'planet_category']],
        on='planet_name',
        how='inner'
    )
    
    return {
        'data': merged_df,
        'bootstrap': bootstrap_data
    }


def compute_ci_width(bootstrap_ci: Dict[str, Any]) -> float:
    """
    Compute the width of the confidence interval.
    
    Args:
        bootstrap_ci: Dictionary containing bootstrap CI results with 'ci_lower' and 'ci_upper'.
        
    Returns:
        Width of the confidence interval.
    """
    ci_lower = bootstrap_ci.get('ci_lower')
    ci_upper = bootstrap_ci.get('ci_upper')
    
    if ci_lower is None or ci_upper is None:
        raise ValueError("Bootstrap CI must contain 'ci_lower' and 'ci_upper' keys")
    
    return float(ci_upper) - float(ci_lower)


def save_correlation_stats(
    output_path: Path,
    tau: float,
    p_value: float,
    ci_width: float,
    bootstrap_ci: Dict[str, Any],
    sample_size: int
) -> None:
    """
    Save correlation statistics to a JSON file.
    
    Args:
        output_path: Path to save the correlation statistics JSON.
        tau: Kendall's tau coefficient.
        p_value: P-value for the correlation.
        ci_width: Width of the confidence interval.
        bootstrap_ci: Full bootstrap CI results.
        sample_size: Number of samples used in the analysis.
    """
    stats = {
        'kendall_tau': float(tau),
        'p_value': float(p_value),
        'ci_width': float(ci_width),
        'bootstrap_ci': bootstrap_ci,
        'sample_size': int(sample_size),
        'ci_lower': float(bootstrap_ci['ci_lower']),
        'ci_upper': float(bootstrap_ci['ci_upper'])
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Correlation statistics saved to {output_path}")


def main():
    """Main entry point for T030a."""
    config = get_config()
    input_dir = Path(config['processed_data_dir'])
    output_path = Path(config['processed_data_dir']) / 'correlation_stats.json'
    
    logger.info("Starting T030a: Output correlation statistics")
    
    try:
        # Load data
        data = load_correlation_results(input_dir)
        merged_df = data['data']
        bootstrap_data = data['bootstrap']
        
        # Filter out censored values for correlation computation
        # Use only detected values (is_upper_limit == False)
        uncensored_df = merged_df[merged_df['is_upper_limit'] == False]
        
        if len(uncensored_df) < 2:
            raise ValueError("Insufficient uncensored data points for correlation analysis")
        
        # Compute Kendall's tau for censored data (using all data including upper limits)
        # The function compute_censored_kendall_tau handles the censoring
        tau, p_value = compute_censored_kendall_tau(
            merged_df,
            x_col='temperature',
            y_col='water_mixing_ratio',
            censor_col='is_upper_limit'
        )
        
        # Compute CI width from bootstrap results
        ci_width = compute_ci_width(bootstrap_data)
        
        # Save results
        save_correlation_stats(
            output_path=output_path,
            tau=tau,
            p_value=p_value,
            ci_width=ci_width,
            bootstrap_ci=bootstrap_data,
            sample_size=len(merged_df)
        )
        
        logger.info(f"T030a completed successfully. Results: tau={tau:.4f}, p={p_value:.4f}, CI width={ci_width:.4f}")
        
    except Exception as e:
        logger.error(f"T030a failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    main()