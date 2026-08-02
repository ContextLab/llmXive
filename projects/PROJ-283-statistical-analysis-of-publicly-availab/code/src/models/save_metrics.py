import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    return obj

def save_single_model_metrics(metrics: Dict[str, Any], output_path: str):
    """Save metrics for a single model to a JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    clean_metrics = convert_numpy_types(metrics)
    
    with open(output_file, 'w') as f:
        json.dump(clean_metrics, f, indent=2)
    
    logger.info(f"Saved model metrics to {output_path}")

def save_model_metrics(beta_metrics: Dict[str, Any], ridge_metrics: Dict[str, Any], output_path: str):
    """Save metrics for both Beta and Ridge models to a single JSON file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Combine metrics into a list
    all_metrics = [
        convert_numpy_types(beta_metrics),
        convert_numpy_types(ridge_metrics)
    ]
    
    with open(output_file, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    logger.info(f"Saved combined model metrics to {output_path}")

def main():
    """Main entry point for saving metrics (placeholder if called directly)."""
    logger.warning("save_metrics.py main() called without arguments. Use fit.py main() for full pipeline.")
    logger.warning("This file is intended to be imported by fit.py.")

if __name__ == "__main__":
    main()
