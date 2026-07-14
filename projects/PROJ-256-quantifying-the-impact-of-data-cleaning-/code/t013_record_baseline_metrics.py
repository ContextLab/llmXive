import os
import sys
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

from analysis import run_baseline_analysis
from config import Config
from utils import setup_logging, compute_file_checksum

logger = logging.getLogger(__name__)

def format_metric_value(val: Any) -> Any:
    """Format metric values to required precision (>= 3 decimals)."""
    if val is None:
        return None
    if isinstance(val, float):
        # Round to 6 decimals to ensure >= 3 precision, avoid floating point noise
        return round(val, 6)
    if isinstance(val, list):
        return [format_metric_value(v) for v in val]
    return val

def log_metrics_summary(metrics: Dict[str, Any]):
    """Log a summary of the metrics."""
    logger.info("=== Baseline Metrics Summary ===")
    if 'datasets' in metrics:
        for ds in metrics['datasets']:
            name = ds.get('dataset_name', 'Unknown')
            logger.info(f"Dataset: {name}")
            if 'tests' in ds:
                tests = ds['tests']
                if 't_test' in tests:
                    p_val = tests['t_test'].get('p_value')
                    logger.info(f"  T-Test P-Value: {p_val}")
                if 'regression' in tests:
                    r_sq = tests['regression'].get('r_squared')
                    logger.info(f"  Regression R-Squared: {r_sq}")
    logger.info("================================")

def process_dataset_for_baseline(
    input_path: str, 
    output_path: str, 
    config: Optional[Dict] = None
) -> bool:
    """
    Process a dataset to generate baseline metrics.
    Ensures output is written to disk with correct precision.
    """
    if config is None:
        config = {}
    
    logger.info(f"Processing dataset from {input_path}")
    
    # Run analysis
    # run_baseline_analysis handles both file loading and returning dict
    # We force it to return a dict by passing a DataFrame or handling the string path carefully
    # Since input_path is a string (directory), we rely on the function to load and write
    # But we want to ensure precision. The function writes directly.
    # Let's intercept the write or post-process.
    # Simpler: Call run_baseline_analysis, which writes the file.
    # Then read it back, format, and write again? Or modify run_baseline_analysis?
    # The task says "Record ... to ... with >= 3 decimal precision".
    # The analysis.py write_output uses default json.dump which might truncate.
    # We will post-process the file written by run_baseline_analysis to ensure precision.
    
    # 1. Run the analysis (this writes a file)
    success = run_baseline_analysis(input_path, output_path, config)
    if not success:
        logger.error("Analysis failed to run.")
        return False
    
    # 2. Read, Format, Rewrite
    try:
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # Recursively format floats
        def fmt(obj):
            if isinstance(obj, dict):
                return {k: fmt(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [fmt(v) for v in obj]
            elif isinstance(obj, float):
                return round(obj, 6) # Ensure >= 3 decimals
            return obj
        
        formatted_data = fmt(data)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(formatted_data, f, indent=2)
        
        logger.info(f"Metrics recorded to {output_path} with precision.")
        return True
    except Exception as e:
        logger.error(f"Failed to format/write metrics: {e}")
        return False

def main():
    """Main entry point for T013."""
    setup_logging("INFO")
    config_obj = Config()
    
    # Convert Config object to dict for the helper
    cfg_dict = {}
    if hasattr(config_obj, 'get'):
        for key in ['RAW_DATA_PATH', 'PROCESSED_DATA_PATH', 'RANDOM_SEED', 'TARGET_COLUMN']:
            val = config_obj.get(key)
            if val is not None:
                cfg_dict[key] = val
    
    raw_dir = cfg_dict.get('RAW_DATA_PATH', 'data/raw')
    processed_dir = cfg_dict.get('PROCESSED_DATA_PATH', 'data/processed')
    output_file = os.path.join(processed_dir, 'baseline_metrics.json')
    
    os.makedirs(processed_dir, exist_ok=True)
    
    success = process_dataset_for_baseline(raw_dir, output_file, cfg_dict)
    
    if success:
        # Load and log summary
        try:
            with open(output_file, 'r') as f:
                metrics = json.load(f)
            log_metrics_summary(metrics)
        except Exception as e:
            logger.error(f"Could not log summary: {e}")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
