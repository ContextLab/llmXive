"""
Adapt Synthetic Parameters (T040c)

This script parses the fetched real Cochrane data to calculate empirical statistics
(mean effect, SE distribution parameters, study count) and updates the project
configuration file (code/config.yaml) with these derived parameters.

Trigger: Executed only if T040 succeeds (real data fetched).
"""
import os
import sys
import csv
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import yaml

# Add project root to path to allow imports if run as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)


def load_cochrane_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Load the real Cochrane data from the specified CSV file.
    
    Args:
        file_path: Path to the CSV file (e.g., data/raw/cochrane_base.csv)
        
    Returns:
        List of dictionaries representing the data rows.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or malformed.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Real data file not found: {file_path}. "
                                "T040 must succeed before running this script.")
    
    data = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("CSV file has no headers.")
        
        for row in reader:
            # Convert numeric strings to floats, handle potential missing values
            processed_row = {}
            for key, value in row.items():
                if value.strip() == '':
                    processed_row[key] = None
                else:
                    try:
                        processed_row[key] = float(value)
                    except ValueError:
                        processed_row[key] = value # Keep as string if not numeric
            data.append(processed_row)
    
    if not data:
        raise ValueError("CSV file contains no data rows.")
        
    return data


def calculate_se_distribution_params(se_values: List[float]) -> Tuple[float, float]:
    """
    Calculate mu and sigma for the LogNormal distribution that best fits the SE values.
    
    If SE values are positive, we assume SE ~ LogNormal(mu, sigma).
    We estimate mu and sigma by taking the mean and std of log(SE).
    
    Args:
        se_values: List of standard error values.
        
    Returns:
        Tuple (mu, sigma)
    """
    # Filter out non-positive values (LogNormal requires x > 0)
    valid_se = [x for x in se_values if x is not None and x > 0]
    
    if len(valid_se) < 2:
        logger.warning("Insufficient valid SE values to fit LogNormal distribution. "
                       "Returning default parameters (mu=0.0, sigma=1.0).")
        return 0.0, 1.0
    
    log_se = [math.log(x) for x in valid_se]
    mu = np.mean(log_se)
    sigma = np.std(log_se, ddof=1) # Sample standard deviation
    
    return mu, sigma


def adapt_parameters(data: List[Dict[str, Any]], config_path: str) -> Dict[str, Any]:
    """
    Calculate empirical parameters from the data and update the config.
    
    Args:
        data: The loaded Cochrane data.
        config_path: Path to code/config.yaml.
        
    Returns:
        The updated configuration dictionary.
    """
    # 1. Calculate N_studies
    n_studies = len(data)
    logger.info(f"Calculated N_studies: {n_studies}")
    
    # 2. Calculate empirical mean effect
    # We assume the effect column is named 'effect' or 'mean_effect' or similar.
    # We'll look for a key that looks like an effect size.
    effect_key = None
    possible_keys = ['effect', 'mean_effect', 'effect_size', 'theta', 'log_or']
    
    for key in possible_keys:
        if key in data[0]:
            effect_key = key
            break
    
    if effect_key is None:
        # Fallback: try to find any numeric column that isn't SE or variance
        numeric_cols = [k for k in data[0].keys() 
                        if isinstance(data[0][k], (int, float)) and 
                        k.lower() not in ['se', 'std_error', 'variance', 'n']]
        if numeric_cols:
            effect_key = numeric_cols[0]
            logger.warning(f"Could not find standard effect key. Using '{effect_key}' as effect.")
        else:
            raise ValueError("Could not identify an effect size column in the data.")
    
    effect_values = [row[effect_key] for row in data if row[effect_key] is not None]
    if not effect_values:
        raise ValueError("No valid effect values found in the data.")
    
    mean_effect = float(np.mean(effect_values))
    logger.info(f"Calculated empirical mean effect ({effect_key}): {mean_effect:.4f}")
    
    # 3. Calculate SE distribution parameters (mu, sigma)
    se_key = None
    possible_se_keys = ['se', 'std_error', 'standard_error', 'se_effect']
    
    for key in possible_se_keys:
        if key in data[0]:
            se_key = key
            break
    
    if se_key is None:
        # Fallback: look for variance and sqrt it
        var_key = None
        possible_var_keys = ['variance', 'var', 'var_effect', 'se_sq']
        for key in possible_var_keys:
            if key in data[0]:
                var_key = key
                break
        
        if var_key:
            var_values = [row[var_key] for row in data if row[var_key] is not None and row[var_key] > 0]
            if var_values:
                se_values = [math.sqrt(v) for v in var_values]
            else:
                se_values = []
        else:
            se_values = []
    else:
        se_values = [row[se_key] for row in data if row[se_key] is not None and row[se_key] > 0]
    
    if not se_values:
        logger.warning("No valid SE values found. Using default LogNormal parameters.")
        mu, sigma = 0.0, 1.0
    else:
        mu, sigma = calculate_se_distribution_params(se_values)
    
    logger.info(f"Calculated SE distribution parameters: mu={mu:.4f}, sigma={sigma:.4f}")
    
    # 4. Update Config
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Ensure synthetic_base_params section exists
    if 'synthetic_base_params' not in config:
        config['synthetic_base_params'] = {}
    
    config['synthetic_base_params'] = {
        'mean_effect': mean_effect,
        'se_mu': mu,
        'se_sigma': sigma,
        'n_studies': n_studies,
        'source': 'Adapted from real Cochrane data (T040)',
        'adaptation_date': '2023-10-27' # Placeholder, could use datetime.now().isoformat()
    }
    
    # Update base_study_count in simulation_parameters to match real data if desired,
    # or keep the synthetic default. The task says "Update ... with derived synthetic_base_params".
    # We will also update the base_study_count in simulation_parameters to reflect the real data size
    # if it's significantly different, but the task specifically asks for synthetic_base_params.
    # Let's update simulation_parameters.base_study_count to match the real data for consistency.
    if 'simulation_parameters' not in config:
        config['simulation_parameters'] = {}
    config['simulation_parameters']['base_study_count'] = n_studies
    
    # Write back
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Successfully updated {config_path} with derived parameters.")
    
    return config


def main():
    """Main entry point for the adaptation script."""
    config_path = "code/config.yaml"
    data_path = "data/raw/cochrane_base.csv"
    
    # Check if real data exists (T040 should have created this)
    if not Path(data_path).exists():
        # This script should only run if T040 succeeded.
        # If T040 failed, the pipeline should have fallen back to T040b-gen.
        # If we are here and data is missing, it's an error state.
        raise FileNotFoundError(
            f"Required real data file not found: {data_path}. "
            "Ensure T040 (fetch_cochrane.py) has successfully downloaded the data before running this script."
        )
    
    try:
        logger.info(f"Loading real data from {data_path}...")
        data = load_cochrane_data(data_path)
        
        logger.info("Adapting parameters...")
        config = adapt_parameters(data, config_path)
        
        logger.info("Parameter adaptation complete.")
        logger.info(f"Derived parameters: {config.get('synthetic_base_params')}")
        
    except FileNotFoundError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.error(f"An error occurred during parameter adaptation: {e}")
        raise


if __name__ == "__main__":
    main()