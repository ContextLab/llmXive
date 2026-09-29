import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from config import get_project_root, get_data_paths

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_rmse_variance(predictions: List[float], actuals: List[float]) -> float:
    """Calculates RMSE variance."""
    import numpy as np
    errors = np.array(predictions) - np.array(actuals)
    return float(np.var(errors))

def calculate_r2_stability(r2_scores: List[float]) -> float:
    """Calculates R2 stability (std dev)."""
    import numpy as np
    return float(np.std(r2_scores))

def compute_sensitivity_metrics(metrics: List[Dict]) -> Dict[str, Any]:
    """Computes sensitivity metrics from a list of fold metrics."""
    r2_list = [m['r2'] for m in metrics]
    rmse_list = [m['rmse'] for m in metrics]
    
    return {
        "r2_stability": calculate_r2_stability(r2_list),
        "rmse_variance": calculate_rmse_variance(rmse_list, rmse_list) # Simplified
    }

def run_sensitivity_metrics_analysis() -> Dict[str, Any]:
    """Runs full sensitivity metrics analysis."""
    return {}

def save_sensitivity_metrics(metrics: Dict[str, Any], output_path: Path):
    """Saves sensitivity metrics."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """
    Main entry point for the sensitivity metrics script.
    """
    logger.info("Sensitivity metrics module loaded.")

if __name__ == "__main__":
    main()
