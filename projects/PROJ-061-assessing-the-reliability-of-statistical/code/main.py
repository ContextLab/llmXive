import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

from config import ensure_directories, DATASET_LIST, RANDOM_SEED
from loaders import load_all_datasets, get_dataset_info
from power_theory import calculate_theoretical_power
from power_empirical import run_bootstrap_power_simulation
from perturbations import (
    inject_heavy_tailed_noise,
    inject_ar1_autocorrelation,
    inject_effect_size_heterogeneity,
)
from sweep_generator import get_sweep_configs
from validators import bootstrap_validity_check, should_exclude_dataset, verify_achieved_magnitude
from utils import safe_json_save, setup_logging

# Configure logging
logger = setup_logging("main")

def load_dataset_info() -> List[Dict[str, Any]]:
    """Load dataset metadata from config."""
    return DATASET_LIST

def get_data_for_dataset(dataset_config: Dict[str, Any]) -> Optional[np.ndarray]:
    """
    Load a specific dataset by name/ID from the loaders.
    Returns the target column (outcome) or the full array if binary classification target is implied.
    """
    try:
        # Load all datasets once or cache them. For this task, we load specifically.
        # The loader returns a dict of datasets.
        all_data = load_all_datasets()
        ds_name = dataset_config.get("name") or dataset_config.get("id")
        
        if ds_name not in all_data:
            logger.warning(f"Dataset {ds_name} not found in loaded data.")
            return None
        
        data = all_data[ds_name]
        # If it's a tuple (X, y), extract y if it exists, else use X
        if isinstance(data, tuple):
            return data[1] if len(data) > 1 else data[0]
        return data
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_config.get('name')}: {e}")
        return None

def clean_data_listwise(data: np.ndarray) -> Optional[np.ndarray]:
    """
    Remove rows with missing values (listwise deletion).
    """
    if data is None:
        return None
    # Handle 1D and 2D arrays
    if data.ndim == 1:
        clean_data = data[~np.isnan(data)]
    else:
        # Drop rows where any column is NaN
        clean_data = data[~np.any(np.isnan(data), axis=1)]
    
    if len(clean_data) == 0:
        return None
    return clean_data

def run_baseline_analysis(data: np.ndarray, dataset_name: str) -> Dict[str, Any]:
    """Run theoretical and empirical power calculation without violations."""
    logger.info(f"Running baseline analysis for {dataset_name}")
    
    # Theoretical power (assuming two-sample t-test, effect size 0.5)
    # We pass n as the length of the data, assuming it's one group or we split it.
    # For simplicity in this context, we assume the data represents the total N for the test.
    # In a real two-sample scenario, we'd need group labels. 
    # Based on existing API, calculate_theoretical_power likely handles n and effect_size.
    theoretical = calculate_theoretical_power(n=len(data), effect_size=0.5, alpha=0.05)
    
    # Empirical power via bootstrap
    empirical = run_bootstrap_power_simulation(data, effect_size=0.5, alpha=0.05)
    
    return {
        "dataset": dataset_name,
        "type": "baseline",
        "theoretical_power": theoretical,
        "empirical_power": empirical,
        "absolute_error": abs(theoretical - empirical),
        "n": len(data)
    }

def run_violation_analysis(
    data: np.ndarray, 
    dataset_name: str, 
    violation_type: str, 
    violation_params: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Inject a specific violation, run power analysis, and record results.
    """
    logger.info(f"Running violation analysis for {dataset_name}: {violation_type} with {violation_params}")
    
    # 1. Inject Violation
    injected_data = None
    if violation_type == "heavy_tailed":
        injected_data = inject_heavy_tailed_noise(data, **violation_params)
    elif violation_type == "ar1":
        injected_data = inject_ar1_autocorrelation(data, **violation_params)
    elif violation_type == "heterogeneity":
        injected_data = inject_effect_size_heterogeneity(data, **violation_params)
    else:
        logger.error(f"Unknown violation type: {violation_type}")
        return None

    if injected_data is None:
        logger.warning(f"Injection failed for {violation_type} on {dataset_name}")
        return None

    # 2. Verify achieved magnitude (FR-009)
    achieved_magnitude = {}
    if violation_type == "ar1":
        achieved_magnitude["ar_coefficient"] = verify_achieved_magnitude(injected_data, violation_params.get("ar_coef", 0))
    
    # 3. Run Power Analysis on Injected Data
    # Theoretical power is usually based on the nominal parameters, but empirical changes.
    # We calculate theoretical based on original N and nominal effect size, 
    # but empirical reflects the violated data.
    theoretical = calculate_theoretical_power(n=len(injected_data), effect_size=0.5, alpha=0.05)
    empirical = run_bootstrap_power_simulation(injected_data, effect_size=0.5, alpha=0.05)
    
    # 4. Validation Check (FR-010)
    if not bootstrap_validity_check(empirical, theoretical):
        logger.warning(f"Bootstrap validity check failed for {dataset_name} ({violation_type}). Excluding from bias calc.")
        # Per FR-010, exclude unreliable estimates. We mark it but still record the attempt.
        # The task asks to append results, so we record the exclusion flag.
        return {
            "dataset": dataset_name,
            "type": "violation",
            "violation_type": violation_type,
            "params": violation_params,
            "theoretical_power": theoretical,
            "empirical_power": empirical,
            "absolute_error": abs(theoretical - empirical),
            "excluded": True,
            "reason": "bootstrap_validity_check_failed"
        }

    return {
        "dataset": dataset_name,
        "type": "violation",
        "violation_type": violation_type,
        "params": violation_params,
        "theoretical_power": theoretical,
        "empirical_power": empirical,
        "absolute_error": abs(theoretical - empirical),
        "achieved_magnitude": achieved_magnitude,
        "excluded": False,
        "n": len(injected_data)
    }

def main():
    """
    Main entry point for the full pipeline including violation sweeps.
    Iterates over datasets and violation configurations, appending results to data/results/violations.json.
    """
    ensure_directories()
    logger.info("Starting Violation Analysis Pipeline (T022)")

    # 1. Load Datasets
    datasets = load_dataset_info()
    if not datasets:
        logger.error("No datasets found in configuration.")
        sys.exit(1)

    # 2. Get Violation Sweep Configurations (from T021b)
    # This function returns a list of dicts with 'type' and 'params'
    violation_configs = get_sweep_configs()
    if not violation_configs:
        logger.warning("No violation configurations found. Skipping violation analysis.")
        # Still run baseline if needed, but task is specifically about violations
        sys.exit(0)

    results = []
    output_path = Path("data/results/violations.json")

    for ds_config in datasets:
        ds_name = ds_config.get("name") or ds_config.get("id")
        raw_data = get_data_for_dataset(ds_config)
        
        if raw_data is None:
            logger.warning(f"Skipping {ds_name}: Data not found.")
            continue

        # T015: Check sample size
        if len(raw_data) < 30:
            logger.info(f"Skipping {ds_name}: insufficient sample size (N={len(raw_data)} < 30).")
            continue

        # T016: Listwise deletion
        clean_data = clean_data_listwise(raw_data)
        if clean_data is None or len(clean_data) < 30:
            logger.info(f"Skipping {ds_name}: insufficient sample size after listwise deletion.")
            continue

        logger.info(f"Processing {ds_name} (N={len(clean_data)})")

        # 3. Iterate over Violation Configurations
        for config in violation_configs:
            v_type = config.get("type")
            v_params = config.get("params", {})
            
            result_entry = run_violation_analysis(
                clean_data, 
                ds_name, 
                v_type, 
                v_params
            )
            
            if result_entry:
                results.append(result_entry)

    # 4. Save Results
    if results:
        safe_json_save(results, output_path)
        logger.info(f"Saved {len(results)} violation analysis results to {output_path}")
    else:
        logger.warning("No results generated. Output file not created.")

    return results

if __name__ == "__main__":
    main()