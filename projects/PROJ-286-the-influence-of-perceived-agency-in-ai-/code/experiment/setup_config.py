"""
Configuration setup module for the experiment.

This module handles the generation of environment configuration (config.yaml)
by reading parameters from the power analysis results (research/power_calculation.json).

It ensures that the sample_size is dynamically loaded from the power calculation
rather than being hardcoded, satisfying the dependency on T002.
"""
import json
import os
import sys
from pathlib import Path
import yaml

def load_json_file(path: Path) -> dict:
    """Load and parse a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    """
    Main entry point to generate config.yaml from power_calculation.json.
    
    This script reads the calculated sample size from T002's output and writes
    a valid config.yaml file for the experiment runner.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    power_calc_path = project_root / "research" / "power_calculation.json"
    config_output_path = project_root / "code" / "experiment" / "config.yaml"
    
    print(f"Reading power calculation from: {power_calc_path}")
    
    if not power_calc_path.exists():
        print(f"ERROR: {power_calc_path} not found. Please run T002 (power_analysis.py) first.")
        sys.exit(1)
    
    try:
        power_data = load_json_file(power_calc_path)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {power_calc_path}: {e}")
        sys.exit(1)
    
    # Extract sample size based on the expected schema from T002
    # The task description specifies reading from key: results.sample_size
    sample_size = None
    if "results" in power_data and "sample_size" in power_data["results"]:
        sample_size = power_data["results"]["sample_size"]
    elif "sample_size" in power_data:
        # Fallback if the schema is flat
        sample_size = power_data["sample_size"]
    
    if sample_size is None:
        print("ERROR: Could not find 'sample_size' in power_calculation.json")
        print(f"Available keys: {list(power_data.keys())}")
        sys.exit(1)
    
    # Construct the configuration dictionary
    config = {
        "sample_size": int(sample_size),
        "alpha_level": 0.05,
        "seed": 42,
        "data_path": "data/raw/"
    }
    
    print(f"Generated config with sample_size: {sample_size}")
    
    # Ensure the output directory exists
    config_output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the YAML file
    with open(config_output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"Configuration written to: {config_output_path}")

if __name__ == "__main__":
    main()
