"""
Sensitivity analysis module for clustering coefficient thresholds.

Implements sensitivity sweep for clustering coefficient thresholds as per T035b.
Reads thresholds from config.yaml under stratification_params.bins.
Runs simulation/analysis for each threshold and records results.
Outputs: data/analysis/sensitivity_sweep.json
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from code.src.utils.config import load_config
from code.src.simulation.run_simulation import main as run_simulation_main
from code.src.analysis.aggregate_results import load_simulation_results

logger = logging.getLogger(__name__)

class SensitivityError(Exception):
    """Custom exception for sensitivity analysis errors."""
    pass

def load_simulation_data(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """
    Load simulation results from data/analysis/simulation_results.json.
    
    Args:
        config_path: Path to the configuration file.
        
    Returns:
        Dictionary containing simulation results.
        
    Raises:
        SensitivityError: If simulation results file is missing or invalid.
    """
    config = load_config(config_path)
    results_path = Path(config.get("simulation_params", {}).get("results_output", "data/analysis/simulation_results.json"))
    
    if not results_path.exists():
        raise SensitivityError(f"Simulation results file not found: {results_path}")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def filter_by_clustering_threshold(
    simulation_data: Dict[str, Any], 
    threshold: float, 
    tolerance: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Filter simulation results by clustering coefficient threshold.
    
    Args:
        simulation_data: Dictionary containing simulation results.
        threshold: Clustering coefficient threshold value.
        tolerance: Tolerance for matching the threshold.
        
    Returns:
        List of simulation results matching the threshold.
    """
    filtered = []
    
    if isinstance(simulation_data, dict) and "results" in simulation_data:
        results = simulation_data["results"]
    elif isinstance(simulation_data, list):
        results = simulation_data
    else:
        results = [simulation_data]
    
    for result in results:
        if isinstance(result, dict):
            clustering = result.get("clustering_coefficient", 0.0)
            if abs(clustering - threshold) <= tolerance:
                filtered.append(result)
    
    return filtered

def compute_sensitivity_metrics(
    filtered_results: List[Dict[str, Any]], 
    threshold: float
) -> Dict[str, Any]:
    """
    Compute sensitivity metrics for a given threshold.
    
    Args:
        filtered_results: List of filtered simulation results.
        threshold: The clustering coefficient threshold used.
        
    Returns:
        Dictionary containing sensitivity metrics.
    """
    if not filtered_results:
        return {
            "threshold": threshold,
            "count": 0,
            "mean_diffusion_rate": None,
            "std_diffusion_rate": None,
            "min_diffusion_rate": None,
            "max_diffusion_rate": None,
            "status": "no_data"
        }
    
    diffusion_rates = [r.get("diffusion_rate", 0.0) for r in filtered_results if "diffusion_rate" in r]
    
    if not diffusion_rates:
        return {
            "threshold": threshold,
            "count": len(filtered_results),
            "mean_diffusion_rate": None,
            "std_diffusion_rate": None,
            "min_diffusion_rate": None,
            "max_diffusion_rate": None,
            "status": "no_diffusion_data"
        }
    
    return {
        "threshold": threshold,
        "count": len(filtered_results),
        "mean_diffusion_rate": float(np.mean(diffusion_rates)),
        "std_diffusion_rate": float(np.std(diffusion_rates)),
        "min_diffusion_rate": float(np.min(diffusion_rates)),
        "max_diffusion_rate": float(np.max(diffusion_rates)),
        "status": "success"
    }

def run_sensitivity_sweep(
    config_path: str = "code/config.yaml",
    output_path: str = "data/analysis/sensitivity_sweep.json"
) -> Dict[str, Any]:
    """
    Run sensitivity sweep for clustering coefficient thresholds.
    
    This function:
    1. Reads thresholds from config.yaml under stratification_params.bins
    2. For each threshold, filters simulation results and computes metrics
    3. Aggregates results and saves to output_path
    
    Args:
        config_path: Path to the configuration file.
        output_path: Path to save the sensitivity sweep results.
        
    Returns:
        Dictionary containing the sensitivity sweep results.
        
    Raises:
        SensitivityError: If configuration is invalid or simulation data is missing.
    """
    logger.info("Starting sensitivity sweep analysis")
    
    # Load configuration
    config = load_config(config_path)
    
    # Get thresholds from config
    strat_params = config.get("stratification_params", {})
    thresholds = strat_params.get("bins", [0.1, 0.2, 0.3, 0.4, 0.5])
    tolerance = strat_params.get("tolerance", 0.05)
    
    if not isinstance(thresholds, list) or len(thresholds) == 0:
        raise SensitivityError("No thresholds found in config.yaml under stratification_params.bins")
    
    logger.info(f"Found {len(thresholds)} thresholds to sweep: {thresholds}")
    
    # Load simulation data
    try:
        simulation_data = load_simulation_data(config_path)
    except SensitivityError as e:
        logger.warning(f"Could not load existing simulation data: {e}")
        logger.info("Running simulation to generate required data...")
        
        # Run simulation to generate data
        run_simulation_main(config_path=config_path)
        simulation_data = load_simulation_data(config_path)
    
    # Process each threshold
    results = []
    for threshold in thresholds:
        logger.info(f"Processing threshold: {threshold}")
        
        filtered = filter_by_clustering_threshold(simulation_data, threshold, tolerance)
        metrics = compute_sensitivity_metrics(filtered, threshold)
        results.append(metrics)
        
        logger.info(f"  -> Found {metrics['count']} matching runs, status: {metrics['status']}")
    
    # Compile final results
    sweep_results = {
        "config_path": config_path,
        "thresholds_analyzed": thresholds,
        "tolerance_used": tolerance,
        "results": results,
        "summary": {
            "total_thresholds": len(thresholds),
            "successful_thresholds": sum(1 for r in results if r["status"] == "success"),
            "thresholds_with_data": sum(1 for r in results if r["count"] > 0)
        }
    }
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(sweep_results, f, indent=2)
    
    logger.info(f"Sensitivity sweep results saved to {output_path}")
    return sweep_results

def save_sensitivity_results(
    results: Dict[str, Any], 
    output_path: str = "data/analysis/sensitivity_sweep.json"
) -> None:
    """
    Save sensitivity analysis results to a JSON file.
    
    Args:
        results: Dictionary containing sensitivity analysis results.
        output_path: Path to save the results.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def verify_sensitivity_results(
    results: Dict[str, Any], 
    min_thresholds: int = 3
) -> Tuple[bool, List[str]]:
    """
    Verify that sensitivity analysis results meet minimum requirements.
    
    Args:
        results: Dictionary containing sensitivity analysis results.
        min_thresholds: Minimum number of thresholds that must have data.
        
    Returns:
        Tuple of (is_valid, list of validation messages)
    """
    messages = []
    is_valid = True
    
    if not results:
        messages.append("No results provided")
        return False, messages
    
    if "results" not in results:
        messages.append("Missing 'results' key in results")
        return False, messages
    
    threshold_results = results.get("results", [])
    
    if len(threshold_results) < min_thresholds:
        messages.append(f"Insufficient thresholds analyzed: {len(threshold_results)} < {min_thresholds}")
        is_valid = False
    
    successful = sum(1 for r in threshold_results if r.get("status") == "success")
    if successful < min_thresholds:
        messages.append(f"Insufficient successful threshold analyses: {successful} < {min_thresholds}")
        is_valid = False
    
    if is_valid:
        messages.append("All validation checks passed")
    
    return is_valid, messages

def main(config_path: str = "code/config.yaml", output_path: str = "data/analysis/sensitivity_sweep.json") -> None:
    """
    Main entry point for sensitivity sweep analysis.
    
    Args:
        config_path: Path to the configuration file.
        output_path: Path to save the sensitivity sweep results.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        results = run_sensitivity_sweep(config_path, output_path)
        
        # Verify results
        is_valid, messages = verify_sensitivity_results(results)
        
        for msg in messages:
            if "passed" in msg:
                logger.info(msg)
            else:
                logger.warning(msg)
        
        if not is_valid:
            logger.error("Sensitivity sweep validation failed")
            raise SensitivityError("Validation failed")
        
        logger.info("Sensitivity sweep completed successfully")
        
    except SensitivityError as e:
        logger.error(f"Sensitivity analysis error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during sensitivity analysis: {e}")
        raise