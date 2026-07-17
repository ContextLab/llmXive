"""
Sensitivity analysis module for clustering coefficient thresholds.

Implements sensitivity sweeps to analyze how simulation results vary
across different clustering coefficient thresholds.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from code.src.utils.config import load_config, get_config_value
from code.src.utils.logging import log_metric
from code.src.utils.reproducibility import ensure_data_directory

logger = logging.getLogger(__name__)

# Default thresholds for sensitivity sweep
DEFAULT_THRESHOLDS = [0.1, 0.3, 0.5, 0.7, 0.9]

class SensitivityError(Exception):
    """Custom exception for sensitivity analysis errors."""
    pass

def load_simulation_data(
    results_path: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Load simulation results from the analysis directory.
    
    Args:
        results_path: Path to simulation_results.json. If None, uses default.
        config: Configuration dictionary. If None, loads from default config.
        
    Returns:
        DataFrame containing simulation results.
        
    Raises:
        SensitivityError: If data cannot be loaded or is invalid.
    """
    if config is None:
        config = load_config()
        
    if results_path is None:
        results_path = Path(config.get("paths", {}).get(
            "analysis_results", "data/analysis/simulation_results.json"
        ))
    
    if not results_path.exists():
        raise SensitivityError(
            f"Simulation results file not found: {results_path}. "
            "Run simulation first."
        )
    
    try:
        with open(results_path, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            if "results" in data:
                df = pd.DataFrame(data["results"])
            else:
                df = pd.DataFrame([data])
        else:
            raise SensitivityError("Invalid data format in simulation results")
        
        required_columns = ["network_id", "diffusion_rate", "clustering_coefficient", "topology_class"]
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise SensitivityError(f"Missing required columns: {missing_cols}")
        
        logger.info(f"Loaded {len(df)} simulation results from {results_path}")
        return df
        
    except json.JSONDecodeError as e:
        raise SensitivityError(f"Failed to parse simulation results JSON: {e}")
    except Exception as e:
        raise SensitivityError(f"Error loading simulation data: {e}")

def filter_by_clustering_threshold(
    df: pd.DataFrame,
    threshold: float,
    column: str = "clustering_coefficient"
) -> pd.DataFrame:
    """
    Filter simulation results by clustering coefficient threshold.
    
    Args:
        df: DataFrame of simulation results.
        threshold: Minimum clustering coefficient to include.
        column: Name of the clustering coefficient column.
        
    Returns:
        Filtered DataFrame.
    """
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found, returning empty DataFrame")
        return pd.DataFrame()
    
    filtered = df[df[column] >= threshold].copy()
    logger.debug(f"Filtered to {len(filtered)} results with {column} >= {threshold}")
    return filtered

def compute_sensitivity_metrics(
    df: pd.DataFrame,
    threshold: float
) -> Dict[str, Any]:
    """
    Compute sensitivity metrics for a given threshold.
    
    Args:
        df: Filtered DataFrame of simulation results.
        threshold: The threshold used for filtering.
        
    Returns:
        Dictionary containing computed metrics.
    """
    if len(df) == 0:
        return {
            "threshold": threshold,
            "sample_size": 0,
            "mean_diffusion_rate": None,
            "std_diffusion_rate": None,
            "min_diffusion_rate": None,
            "max_diffusion_rate": None,
            "topology_distribution": {},
            "valid": False
        }
    
    diffusion_rates = df["diffusion_rate"].dropna()
    
    metrics = {
        "threshold": threshold,
        "sample_size": len(df),
        "mean_diffusion_rate": float(diffusion_rates.mean()) if len(diffusion_rates) > 0 else None,
        "std_diffusion_rate": float(diffusion_rates.std()) if len(diffusion_rates) > 1 else None,
        "min_diffusion_rate": float(diffusion_rates.min()) if len(diffusion_rates) > 0 else None,
        "max_diffusion_rate": float(diffusion_rates.max()) if len(diffusion_rates) > 0 else None,
        "topology_distribution": {},
        "valid": True
    }
    
    # Compute topology distribution
    if "topology_class" in df.columns:
        topology_counts = df["topology_class"].value_counts().to_dict()
        total = sum(topology_counts.values())
        metrics["topology_distribution"] = {
            k: {"count": int(v), "percentage": float(v / total * 100)}
            for k, v in topology_counts.items()
        }
    
    return metrics

def run_sensitivity_sweep(
    df: pd.DataFrame,
    thresholds: Optional[List[float]] = None,
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Run sensitivity sweep across multiple clustering coefficient thresholds.
    
    Args:
        df: DataFrame of simulation results.
        thresholds: List of thresholds to test. If None, uses defaults from config.
        config: Configuration dictionary. If None, loads from default config.
        
    Returns:
        List of metric dictionaries, one per threshold.
    """
    if config is None:
        config = load_config()
    
    if thresholds is None:
        # Try to get thresholds from config
        thresholds = get_config_value(
            config,
            ["analysis", "sensitivity", "thresholds"],
            DEFAULT_THRESHOLDS
        )
    
    if not isinstance(thresholds, list) or len(thresholds) == 0:
        raise SensitivityError("Thresholds must be a non-empty list")
    
    # Validate thresholds
    for t in thresholds:
        if not isinstance(t, (int, float)) or t < 0 or t > 1:
            raise SensitivityError(
                f"Invalid threshold value: {t}. Must be between 0 and 1."
            )
    
    logger.info(f"Running sensitivity sweep with {len(thresholds)} thresholds: {thresholds}")
    
    results = []
    for threshold in sorted(thresholds):
        filtered_df = filter_by_clustering_threshold(df, threshold)
        metrics = compute_sensitivity_metrics(filtered_df, threshold)
        results.append(metrics)
        
        # Log progress
        log_metric(
            "sensitivity_sweep_step",
            {
                "threshold": threshold,
                "sample_size": metrics["sample_size"],
                "valid": metrics["valid"]
            }
        )
    
    logger.info(f"Sensitivity sweep complete. {len(results)} thresholds tested.")
    return results

def save_sensitivity_results(
    results: List[Dict[str, Any]],
    output_path: Optional[Path] = None,
    config: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Save sensitivity sweep results to JSON file.
    
    Args:
        results: List of metric dictionaries from run_sensitivity_sweep.
        output_path: Path to output file. If None, uses default.
        config: Configuration dictionary. If None, loads from default config.
        
    Returns:
        Path to the saved file.
        
    Raises:
        SensitivityError: If results cannot be saved.
    """
    if config is None:
        config = load_config()
    
    if output_path is None:
        output_path = Path(config.get("paths", {}).get(
            "sensitivity_results", "data/analysis/sensitivity_sweep.json"
        ))
    
    ensure_data_directory(output_path.parent)
    
    try:
        output_data = {
            "metadata": {
                "num_thresholds": len(results),
                "thresholds_tested": [r["threshold"] for r in results],
                "generated_at": str(pd.Timestamp.now()),
                "config_used": {
                    "thresholds": [r["threshold"] for r in results]
                }
            },
            "results": results,
            "summary": {
                "total_thresholds": len(results),
                "valid_thresholds": sum(1 for r in results if r["valid"]),
                "min_sample_size": min(r["sample_size"] for r in results) if results else 0,
                "max_sample_size": max(r["sample_size"] for r in results) if results else 0
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Sensitivity results saved to {output_path}")
        log_metric(
            "sensitivity_results_saved",
            {
                "path": str(output_path),
                "num_results": len(results)
            }
        )
        
        return output_path
        
    except Exception as e:
        raise SensitivityError(f"Failed to save sensitivity results: {e}")

def verify_sensitivity_results(
    results_path: Path,
    expected_thresholds: Optional[List[float]] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify that sensitivity results file meets SC-005 requirements.
    
    Args:
        results_path: Path to sensitivity_sweep.json.
        expected_thresholds: Optional list of expected thresholds.
        
    Returns:
        Tuple of (success, details_dict).
    """
    details = {
        "file_exists": False,
        "valid_json": False,
        "has_results": False,
        "has_metadata": False,
        "thresholds_valid": False,
        "all_thresholds_present": False,
        "errors": []
    }
    
    if not results_path.exists():
        details["errors"].append(f"File not found: {results_path}")
        return False, details
    
    details["file_exists"] = True
    
    try:
        with open(results_path, 'r') as f:
            data = json.load(f)
        details["valid_json"] = True
    except json.JSONDecodeError as e:
        details["errors"].append(f"Invalid JSON: {e}")
        return False, details
    
    if "results" not in data:
        details["errors"].append("Missing 'results' key")
        return False, details
    details["has_results"] = True
    
    if "metadata" not in data:
        details["errors"].append("Missing 'metadata' key")
        return False, details
    details["has_metadata"] = True
    
    results = data["results"]
    if not isinstance(results, list) or len(results) == 0:
        details["errors"].append("'results' must be a non-empty list")
        return False, details
    
    # Check threshold validity
    thresholds = []
    for r in results:
        if "threshold" not in r:
            details["errors"].append("Missing 'threshold' in result entry")
            return False, details
        t = r["threshold"]
        if not isinstance(t, (int, float)) or t < 0 or t > 1:
            details["errors"].append(f"Invalid threshold value: {t}")
            return False, details
        thresholds.append(t)
    
    details["thresholds_valid"] = True
    
    # Check expected thresholds
    if expected_thresholds is not None:
        expected_set = set(expected_thresholds)
        actual_set = set(thresholds)
        if expected_set != actual_set:
            details["errors"].append(
                f"Threshold mismatch. Expected: {expected_set}, Got: {actual_set}"
            )
            return False, details
    
    details["all_thresholds_present"] = True
    details["errors"] = []
    
    logger.info("Sensitivity results verification passed")
    return True, details

def main() -> int:
    """
    Main entry point for sensitivity sweep analysis.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Load configuration
        config = load_config()
        
        # Load simulation data
        logger.info("Loading simulation data...")
        df = load_simulation_data(config=config)
        
        # Get thresholds from config
        thresholds = get_config_value(
            config,
            ["analysis", "sensitivity", "thresholds"],
            DEFAULT_THRESHOLDS
        )
        
        # Run sensitivity sweep
        logger.info("Running sensitivity sweep...")
        results = run_sensitivity_sweep(df, thresholds, config)
        
        # Save results
        output_path = Path(config.get("paths", {}).get(
            "sensitivity_results", "data/analysis/sensitivity_sweep.json"
        ))
        save_sensitivity_results(results, output_path, config)
        
        # Verify results
        success, details = verify_sensitivity_results(output_path, thresholds)
        
        if not success:
            logger.error(f"Verification failed: {details['errors']}")
            return 1
        
        logger.info("Sensitivity sweep completed successfully")
        return 0
        
    except SensitivityError as e:
        logger.error(f"Sensitivity analysis error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
if __name__ == "__main__":
    import sys
    sys.exit(main())
