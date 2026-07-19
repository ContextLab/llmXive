"""
Sensitivity analysis for clustering coefficient thresholds.
Implements FR-008: Vary thresholds and report diffusion rate variations.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class SensitivityError(Exception):
    """Custom exception for sensitivity analysis errors."""
    pass

def load_simulation_data(simulation_results_path: str) -> pd.DataFrame:
    """Load simulation results from JSON file."""
    path = Path(simulation_results_path)
    if not path.exists():
        raise FileNotFoundError(f"Simulation results not found: {simulation_results_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return pd.DataFrame(data)
    elif isinstance(data, dict) and "results" in data:
        return pd.DataFrame(data["results"])
    else:
        raise ValueError("Unexpected data format in simulation results")

def filter_by_clustering_threshold(df: pd.DataFrame, threshold: float, operator: str = '>=') -> pd.DataFrame:
    """
    Filter dataframe by clustering coefficient threshold.
    
    Args:
        df: DataFrame with 'clustering_coefficient_actual' column
        threshold: Threshold value
        operator: Comparison operator ('>=', '<=', '>', '<', '==')
        
    Returns:
        Filtered DataFrame
    """
    if 'clustering_coefficient_actual' not in df.columns:
        logger.warning("Column 'clustering_coefficient_actual' not found. Using all rows.")
        return df
        
    if operator == '>=':
        return df[df['clustering_coefficient_actual'] >= threshold]
    elif operator == '<=':
        return df[df['clustering_coefficient_actual'] <= threshold]
    elif operator == '>':
        return df[df['clustering_coefficient_actual'] > threshold]
    elif operator == '<':
        return df[df['clustering_coefficient_actual'] < threshold]
    elif operator == '==':
        # Allow small tolerance for floating point
        return df[np.abs(df['clustering_coefficient_actual'] - threshold) < 1e-6]
    else:
        raise ValueError(f"Unsupported operator: {operator}")

def compute_sensitivity_metrics(df: pd.DataFrame, threshold: float) -> Dict[str, Any]:
    """
    Compute sensitivity metrics for a given threshold.
    
    Args:
        df: Filtered DataFrame
        threshold: The threshold used
        
    Returns:
        Dictionary with metrics
    """
    if df.empty:
        return {
            "threshold": threshold,
            "count": 0,
            "mean_diffusion_rate": None,
            "std_diffusion_rate": None,
            "min_diffusion_rate": None,
            "max_diffusion_rate": None
        }
        
    diffusion_rates = df['diffusion_rate'].dropna()
    
    return {
        "threshold": threshold,
        "count": len(df),
        "mean_diffusion_rate": float(diffusion_rates.mean()) if len(diffusion_rates) > 0 else None,
        "std_diffusion_rate": float(diffusion_rates.std()) if len(diffusion_rates) > 0 else None,
        "min_diffusion_rate": float(diffusion_rates.min()) if len(diffusion_rates) > 0 else None,
        "max_diffusion_rate": float(diffusion_rates.max()) if len(diffusion_rates) > 0 else None
    }

def run_sensitivity_sweep(simulation_results_path: str, thresholds: List[float]) -> List[Dict[str, Any]]:
    """
    Run sensitivity analysis across multiple thresholds.
    
    Args:
        simulation_results_path: Path to simulation results JSON
        thresholds: List of clustering coefficient thresholds to test
        
    Returns:
        List of metric dictionaries for each threshold
    """
    df = load_simulation_data(simulation_results_path)
    results = []
    
    for threshold in thresholds:
        filtered_df = filter_by_clustering_threshold(df, threshold)
        metrics = compute_sensitivity_metrics(filtered_df, threshold)
        results.append(metrics)
        logger.info(f"Threshold {threshold}: {metrics['count']} samples")
        
    return results

def save_sensitivity_results(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save sensitivity results to JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "sweep_parameters": {
            "thresholds": [r["threshold"] for r in results]
        },
        "results": results,
        "record_count": len(results)
    }
    
    with open(path, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    logger.info(f"Sensitivity sweep results saved to {output_path}")

def verify_sensitivity_results(results: List[Dict[str, Any]], min_thresholds: int = 5) -> bool:
    """
    Verify that the sensitivity sweep meets minimum requirements.
    
    Args:
        results: List of result dictionaries
        min_thresholds: Minimum number of distinct thresholds required
        
    Returns:
        True if requirements are met
    """
    thresholds = [r["threshold"] for r in results]
    distinct_count = len(set(thresholds))
    
    if distinct_count < min_thresholds:
        logger.warning(f"Only {distinct_count} distinct thresholds found, need {min_thresholds}")
        return False
        
    return True

def main():
    """Main entry point for sensitivity analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run sensitivity sweep analysis")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    # Load thresholds from config
    from code.src.utils.config import load_config
    config = load_config(args.config)
    thresholds = config.get("analysis_params", {}).get("sensitivity_thresholds", [0.0, 0.2, 0.4, 0.6, 0.8])
    
    # Ensure at least 5 thresholds
    if len(thresholds) < 5:
        logger.warning(f"Only {len(thresholds)} thresholds in config, extending to 5")
        thresholds = [0.0, 0.2, 0.4, 0.6, 0.8]
        
    simulation_path = Path(args.output) / "analysis" / "simulation_results.json"
    output_path = Path(args.output) / "analysis" / "sensitivity_sweep.json"
    
    if not simulation_path.exists():
        logger.error(f"Simulation results not found at {simulation_path}")
        # Create empty result to allow pipeline to continue
        save_sensitivity_results([], str(output_path))
        return
        
    results = run_sensitivity_sweep(str(simulation_path), thresholds)
    save_sensitivity_results(results, str(output_path))
    
    if verify_sensitivity_results(results):
        logger.info("Sensitivity sweep verification PASSED")
    else:
        logger.error("Sensitivity sweep verification FAILED")

if __name__ == "__main__":
    main()
