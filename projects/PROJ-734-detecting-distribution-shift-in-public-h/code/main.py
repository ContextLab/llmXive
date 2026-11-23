"""
Main pipeline entry point.
Orchestrates data download, preprocessing, detection, evaluation, and sensitivity analysis.
"""
import os
import sys
import json
import subprocess
import logging
import yaml
from typing import Any, Dict, Optional

from download_data import fetch_cdc_data
from preprocess import preprocess_pipeline
from mmd_detector import detect_shifts
from evaluate import evaluate_pipeline
from sensitivity import run_grid_search, generate_grid, save_grid_results
from logging_setup import setup_logging
from exceptions import E_NO_DATA

logger = setup_logging("main")

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def validate_config_schema(config: Dict[str, Any]) -> bool:
    """
    Validate config against expected schema.
    Checks for required keys and types.
    """
    required_keys = ['seed', 'permutations', 'window_size', 'stride', 'alpha', 'min_permutations', 'time_budget_minutes']
    for key in required_keys:
        if key not in config:
            logger.error(f"Missing required config key: {key}")
            return False
    # Basic type checks
    if not isinstance(config['seed'], int): return False
    if not isinstance(config['permutations'], int): return False
    if not isinstance(config['window_size'], int): return False
    if not isinstance(config['stride'], int): return False
    if not isinstance(config['alpha'], float): return False
    if not isinstance(config['min_permutations'], int): return False
    if not isinstance(config['time_budget_minutes'], int): return False
    return True

def get_git_commit_hash() -> str:
    """Get the current git commit hash."""
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except Exception:
        return "unknown"

def get_requirements_content() -> str:
    """Read requirements.txt content."""
    try:
        with open('requirements.txt', 'r') as f:
            return f.read()
    except Exception:
        return "requirements.txt not found"

def get_data_download_urls() -> Dict[str, str]:
    """Return the URLs used for data download."""
    from download_data import ILI_DATA_URL
    return {
        "ili_data": ILI_DATA_URL
    }

def generate_reproducibility_manifest(config: Dict[str, Any]):
    """Generate a manifest for reproducibility."""
    manifest = {
        "git_commit": get_git_commit_hash(),
        "requirements": get_requirements_content(),
        "random_seed": config.get('seed'),
        "data_urls": get_data_download_urls(),
        "config_snapshot": config
    }
    output_path = "data/processed/reproducibility_manifest.json"
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved reproducibility manifest to {output_path}")

def run_pipeline():
    """Run the full pipeline."""
    logger.info("Starting pipeline.")

    # 1. Download Data
    if not os.path.exists("data/raw/fluview_ili.csv") or not os.path.exists("data/raw/ground_truth_events.csv"):
        logger.info("Data missing. Running download.")
        fetch_cdc_data()

    # 2. Preprocess
    preprocess_pipeline()

    # 3. Detect Shifts (MMD)
    # This is handled in evaluate_pipeline which calls detect_shifts

    # 4. Evaluate
    evaluate_pipeline()

    # 5. Sensitivity Analysis
    run_sensitivity_analysis()

    logger.info("Pipeline complete.")

def run_sensitivity_analysis():
    """Run sensitivity analysis grid search."""
    logger.info("Starting sensitivity analysis.")

    config = load_config()
    timeout_minutes = config.get('sensitivity', {}).get('timeout_minutes', 5)

    # Load data (reuse processed data)
    from preprocess import load_ili_data, remove_missing_weeks, log_transform, standardize
    raw_df = load_ili_data("data/raw/fluview_ili.csv")
    processed_df = remove_missing_weeks(raw_df)
    processed_df = log_transform(processed_df)
    processed_df = standardize(processed_df)
    processed_data = processed_df['ili_percent'].values

    # Load ground truth
    from evaluate import load_ground_truth
    if os.path.exists("data/raw/ground_truth_events.csv"):
        ground_truth_events = load_ground_truth("data/raw/ground_truth_events.csv")
    else:
        ground_truth_events = []

    # Generate grid
    grid = generate_grid()

    # Run grid search
    results = run_grid_search(grid, processed_data, ground_truth_events, timeout_minutes)

    # Save results
    save_grid_results(results, "data/processed/sensitivity.csv")

    logger.info("Sensitivity analysis complete.")

def main():
    config = load_config()
    if not validate_config_schema(config):
        raise ValueError("Invalid configuration schema")

    generate_reproducibility_manifest(config)
    run_pipeline()

if __name__ == "__main__":
    main()
