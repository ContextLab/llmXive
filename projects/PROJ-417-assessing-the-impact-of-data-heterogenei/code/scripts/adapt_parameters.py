import os
import sys
import csv
import math
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import yaml

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

def load_cochrane_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Load the fetched Cochrane data from a CSV file.
    
    Args:
        file_path: Path to the CSV file containing Cochrane data.
        
    Returns:
        List of dictionaries representing the rows of the CSV.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no data rows.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Cochrane data file not found: {file_path}")
        raise FileNotFoundError(f"REAL_DATA_FETCH_FAILED: {file_path}")
    
    data = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    if not data:
        logger.error("Cochrane data file is empty or has no data rows.")
        raise ValueError("REAL_DATA_FETCH_FAILED: No data rows in file.")
    
    logger.info(f"Loaded {len(data)} rows from Cochrane data file.")
    return data

def calculate_se_distribution_params(effect_sizes: List[float], se_values: List[float]) -> Tuple[float, float]:
    """
    Calculate the distribution parameters (mu, sigma) for the standard errors.
    This assumes a log-normal distribution for SEs as per common meta-analysis practices.
    
    Args:
        effect_sizes: List of effect sizes.
        se_values: List of standard errors corresponding to the effect sizes.
        
    Returns:
        Tuple of (mu, sigma) for the log-normal distribution of SEs.
    """
    if not se_values or len(se_values) == 0:
        logger.warning("No SE values provided. Returning default mu=0.0, sigma=1.0")
        return 0.0, 1.0
    
    # Filter out non-positive SEs for log transformation
    valid_se = [se for se in se_values if se > 0]
    if not valid_se:
        logger.warning("No valid positive SE values. Returning default mu=0.0, sigma=1.0")
        return 0.0, 1.0
    
    log_se = [math.log(se) for se in valid_se]
    mu = float(np.mean(log_se))
    sigma = float(np.std(log_se))
    
    logger.info(f"Calculated SE distribution params: mu={mu:.4f}, sigma={sigma:.4f}")
    return mu, sigma

def adapt_parameters(cochrane_data: List[Dict[str, Any]], config_path: str) -> Dict[str, Any]:
    """
    Parse the fetched Cochrane data to calculate empirical mean effect, 
    SE distribution parameters (mu, sigma), and N_studies. 
    Update the config.yaml with these derived synthetic_base_params.
    
    Args:
        cochrane_data: List of dictionaries containing the Cochrane data.
        config_path: Path to the config.yaml file.
        
    Returns:
        The updated configuration dictionary.
        
    Raises:
        FileNotFoundError: If config_path does not exist.
        yaml.YAMLError: If config_path is not valid YAML.
    """
    if not cochrane_data:
        raise ValueError("No data provided to adapt_parameters.")
    
    # Extract effect sizes and standard errors
    # Assuming the CSV has columns 'effect_size' and 'se' based on typical Cochrane data
    # If column names differ, this might need adjustment, but we assume standard naming
    effect_sizes = []
    se_values = []
    
    # Inspect keys of the first row to determine column names if necessary
    first_row_keys = list(cochrane_data[0].keys())
    logger.info(f"Columns in Cochrane data: {first_row_keys}")
    
    # Heuristic to find columns
    effect_col = None
    se_col = None
    
    for key in first_row_keys:
        lower_key = key.lower()
        if 'effect' in lower_key and 'size' in lower_key:
            effect_col = key
        elif 'effect' in lower_key and 'se' not in lower_key:
            effect_col = key
        elif 'se' in lower_key or 'std_err' in lower_key:
            se_col = key
    
    # Fallback to common names if heuristic fails
    if effect_col is None:
        for key in ['effect_size', 'effect', 'log_odds_ratio', 'mean_diff']:
            if key in first_row_keys:
                effect_col = key
                break
    if se_col is None:
        for key in ['se', 'std_err', 'standard_error', 'se_effect']:
            if key in first_row_keys:
                se_col = key
                break
    
    if effect_col is None or se_col is None:
        logger.warning(f"Could not identify effect or SE columns. Using defaults. Found: {first_row_keys}")
        # If we can't find them, we'll use defaults for the params, but still count N_studies
        mu, sigma = 0.0, 1.0
        mean_effect = 0.0
    else:
        for row in cochrane_data:
            try:
                val_eff = float(row.get(effect_col, 0.0))
                val_se = float(row.get(se_col, 1.0))
                effect_sizes.append(val_eff)
                se_values.append(val_se)
            except (ValueError, TypeError):
                continue # Skip rows with invalid numeric data
        
        if not effect_sizes:
            mean_effect = 0.0
            logger.warning("No valid effect sizes found. Defaulting to 0.0")
        else:
            mean_effect = float(np.mean(effect_sizes))
        
        mu, sigma = calculate_se_distribution_params(effect_sizes, se_values)
    
    n_studies = len(effect_sizes)
    if n_studies == 0:
        n_studies = len(cochrane_data) # Fallback to total rows if no numeric data found
    
    logger.info(f"Derived parameters: mean_effect={mean_effect:.4f}, mu={mu:.4f}, sigma={sigma:.4f}, N_studies={n_studies}")
    
    # Load config
    config_path_obj = Path(config_path)
    if not config_path_obj.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path_obj, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Update synthetic_base_params
    if 'synthetic_base_params' not in config:
        config['synthetic_base_params'] = {}
    
    config['synthetic_base_params']['mean_effect'] = mean_effect
    config['synthetic_base_params']['se_distribution']['mu'] = mu
    config['synthetic_base_params']['se_distribution']['sigma'] = sigma
    config['synthetic_base_params']['study_count'] = n_studies
    config['synthetic_base_params']['source_citation'] = "Adapted from Cochrane Data (Zenodo 10.5281/zenodo.10286623)"
    
    # Write back to config
    with open(config_path_obj, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated config.yaml at {config_path} with adapted parameters.")
    return config

def main():
    """
    Main entry point for the adapt_parameters script.
    """
    # Determine paths
    project_root = Path(__file__).resolve().parent.parent
    data_path = project_root / "data" / "raw" / "cochrane_base.csv"
    config_path = project_root / "code" / "config.yaml"
    
    # Check if real data exists (T040 success path)
    # The script is only supposed to run if T040 succeeded.
    # If the file doesn't exist, we should fail loudly as per constraints.
    if not data_path.exists():
        logger.error(f"Real Cochrane data not found at {data_path}. "
                     "This script should only run if T040 (fetch_cochrane.py) succeeded.")
        # Raise an error to indicate failure in the pipeline flow
        raise FileNotFoundError("REAL_DATA_FETCH_FAILED: cochrane_base.csv not found. "
                                "T040c requires T040 success.")
    
    try:
        data = load_cochrane_data(str(data_path))
        config = adapt_parameters(data, str(config_path))
        logger.info("Parameter adaptation completed successfully.")
        
        # Log the updated params for verification
        print(json.dumps(config.get('synthetic_base_params', {}), indent=2))
        
    except Exception as e:
        logger.error(f"Parameter adaptation failed: {e}")
        raise

if __name__ == "__main__":
    main()
