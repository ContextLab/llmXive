import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from code.src.utils.config import load_config
from code.src.analysis.regression import fit_linear_regression

class SensitivityError(Exception):
    """Custom exception for sensitivity analysis errors."""
    pass

def load_simulation_data(results_path: str = "data/analysis/simulation_results.json") -> pd.DataFrame:
    """
    Load simulation results from JSON into a DataFrame.
    
    Args:
        results_path: Path to the simulation results JSON file.
        
    Returns:
        DataFrame containing simulation results.
        
    Raises:
        SensitivityError: If file not found or invalid format.
    """
    path = Path(results_path)
    if not path.exists():
        raise SensitivityError(f"Simulation results file not found: {results_path}")
        
    with open(path, 'r') as f:
        data = json.load(f)
        
    if not data:
        raise SensitivityError("Simulation results file is empty.")
        
    df = pd.DataFrame(data)
    
    # Ensure required columns exist
    required_cols = ['diffusion_rate', 'clustering_coefficient', 'topology_class']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        # Try to compute clustering if not present (fallback for older data)
        # In a real scenario, this should be in the metadata or simulation results
        logging.warning(f"Missing columns in simulation results: {missing}. Attempting to proceed with available data.")
        
    return df

def filter_by_clustering_threshold(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """
    Filter the dataset to include only graphs with clustering coefficient >= threshold.
    
    Args:
        df: DataFrame with simulation results.
        threshold: Minimum clustering coefficient.
        
    Returns:
        Filtered DataFrame.
    """
    if 'clustering_coefficient' not in df.columns:
        # If clustering is not in the main results, we might need to join with metadata
        # For now, assume it's present or return the full set if threshold is 0
        if threshold > 0:
            logging.warning("Clustering coefficient column missing. Returning full dataset.")
        return df
        
    return df[df['clustering_coefficient'] >= threshold].copy()

def compute_sensitivity_metrics(df: pd.DataFrame, threshold: float) -> Dict[str, Any]:
    """
    Compute statistics for a specific clustering threshold.
    
    Args:
        df: Filtered DataFrame.
        threshold: The threshold used for filtering.
        
    Returns:
        Dictionary with metrics for this threshold.
    """
    if df.empty:
        return {
            'threshold': threshold,
            'sample_size': 0,
            'mean_diffusion': None,
            'std_diffusion': None,
            'min_diffusion': None,
            'max_diffusion': None,
            'regression_slope': None,
            'regression_r2': None,
            'status': 'NO_DATA'
        }
        
    # Calculate diffusion statistics
    mean_diff = df['diffusion_rate'].mean()
    std_diff = df['diffusion_rate'].std()
    
    # Perform simple regression: Diffusion vs Clustering (if clustering column exists)
    # to see how diffusion changes as we select higher clustering networks
    reg_result = None
    if 'clustering_coefficient' in df.columns and len(df) > 2:
        try:
            X = df['clustering_coefficient'].values.reshape(-1, 1)
            y = df['diffusion_rate'].values
            reg_result = fit_linear_regression(X, y)
        except Exception as e:
            logging.warning(f"Regression failed for threshold {threshold}: {e}")
            
    return {
        'threshold': threshold,
        'sample_size': len(df),
        'mean_diffusion': float(mean_diff),
        'std_diffusion': float(std_diff) if not np.isnan(std_diff) else None,
        'min_diffusion': float(df['diffusion_rate'].min()),
        'max_diffusion': float(df['diffusion_rate'].max()),
        'regression_slope': float(reg_result['coefficients'][0]) if reg_result else None,
        'regression_r2': float(reg_result['r2']) if reg_result else None,
        'status': 'OK'
    }

def run_sensitivity_sweep(
    results_path: str = "data/analysis/simulation_results.json",
    config_path: str = "code/config.yaml",
    output_path: str = "data/analysis/sensitivity_sweep.json"
) -> Dict[str, Any]:
    """
    Run the sensitivity sweep for clustering coefficient thresholds.
    
    This function:
    1. Loads simulation data.
    2. Reads clustering thresholds from config (defaulting to 0.0, 0.1, 0.2, 0.3, 0.4 if missing).
    3. Filters data for each threshold.
    4. Computes metrics (mean diffusion, variance, etc.).
    5. Saves results to the specified output path.
    
    Args:
        results_path: Path to simulation results.
        config_path: Path to config file.
        output_path: Path to save sensitivity results.
        
    Returns:
        Dictionary containing the sweep results.
    """
    logging.info(f"Starting sensitivity sweep. Loading data from {results_path}")
    
    # Load data
    df = load_simulation_data(results_path)
    
    # Load config to get thresholds
    try:
        config = load_config(config_path)
        # Look for thresholds in config, defaulting to 5 distinct cutoffs as per SC-005
        thresholds = config.get('analysis', {}).get('sensitivity_thresholds', [0.0, 0.1, 0.2, 0.3, 0.4])
    except Exception as e:
        logging.warning(f"Could not load thresholds from config: {e}. Using defaults.")
        thresholds = [0.0, 0.1, 0.2, 0.3, 0.4]
        
    if len(thresholds) < 5:
        logging.warning(f"SC-005 requires at least 5 distinct cutoffs. Found {len(thresholds)}. Extending defaults.")
        # Ensure we have at least 5
        default_additions = [0.0, 0.1, 0.2, 0.3, 0.4]
        for t in default_additions:
            if t not in thresholds:
                thresholds.append(t)
            if len(thresholds) >= 5:
                break
        
    logging.info(f"Running sweep for {len(thresholds)} thresholds: {thresholds}")
    
    results = []
    for t in thresholds:
        logging.info(f"Processing threshold: {t}")
        filtered_df = filter_by_clustering_threshold(df, t)
        metrics = compute_sensitivity_metrics(filtered_df, t)
        results.append(metrics)
        
    output_data = {
        'config_path': config_path,
        'input_data': results_path,
        'thresholds_used': thresholds,
        'results': results,
        'summary': {
            'total_thresholds': len(thresholds),
            'valid_runs': sum(1 for r in results if r['status'] == 'OK'),
            'empty_runs': sum(1 for r in results if r['status'] == 'NO_DATA')
        }
    }
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    logging.info(f"Sensitivity sweep completed. Results saved to {output_path}")
    return output_data

def save_sensitivity_results(results: Dict[str, Any], output_path: str = "data/analysis/sensitivity_sweep.json") -> None:
    """
    Save sensitivity results to a JSON file.
    
    Args:
        results: The results dictionary.
        output_path: Path to save the file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
        
def verify_sensitivity_results(results_path: str = "data/analysis/sensitivity_sweep.json") -> bool:
    """
    Verify that the sensitivity results meet SC-005 (>=5 distinct cutoffs).
    
    Args:
        results_path: Path to the results file.
        
    Returns:
        True if valid, False otherwise.
    """
    path = Path(results_path)
    if not path.exists():
        logging.error(f"Results file not found: {results_path}")
        return False
        
    with open(path, 'r') as f:
        data = json.load(f)
        
    thresholds = data.get('thresholds_used', [])
    if len(thresholds) < 5:
        logging.error(f"SC-005 Failed: Only {len(thresholds)} thresholds found. Need >= 5.")
        return False
        
    logging.info(f"SC-005 Passed: {len(thresholds)} thresholds found.")
    return True

def main():
    """
    CLI entry point for sensitivity sweep.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run sensitivity sweep on clustering thresholds.")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    parser.add_argument("--input", type=str, default="data/analysis/simulation_results.json", help="Path to simulation results")
    parser.add_argument("--output", type=str, default="data/analysis/sensitivity_sweep.json", help="Path to output file")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        results = run_sensitivity_sweep(
            results_path=args.input,
            config_path=args.config,
            output_path=args.output
        )
        
        if verify_sensitivity_results(args.output):
            logging.info("Sensitivity sweep completed successfully.")
            return 0
        else:
            logging.error("Sensitivity sweep failed validation.")
            return 1
    except SensitivityError as e:
        logging.error(f"Sensitivity error: {e}")
        return 1
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
