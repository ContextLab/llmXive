"""
Script to generate code/experiment/config.yaml based on T002 power analysis results.
Reads research/power_calculation.json and writes code/experiment/config.yaml.
"""
import json
import os
import sys
from pathlib import Path
import yaml

def load_json_file(path: Path) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Required file not found: {path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

def main():
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    power_calc_path = project_root / "research" / "power_calculation.json"
    config_output_path = project_root / "code" / "experiment" / "config.yaml"

    # Ensure the output directory exists
    config_output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load power calculation results
    print(f"Loading power calculation from: {power_calc_path}")
    power_data = load_json_file(power_calc_path)

    # Extract sample_size (Required N)
    # The power_analysis.py script outputs 'required_n' in the JSON
    sample_size = power_data.get("required_n")
    if sample_size is None:
        raise ValueError("Could not find 'required_n' in power_calculation.json")

    # Construct config dictionary
    config = {
        "sample_size": sample_size,
        "alpha_level": 0.05,
        "seed": 42,
        "data_path": "data/raw/"
    }

    # Write to YAML
    print(f"Writing config to: {config_output_path}")
    with open(config_output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"Config generated successfully. Sample size set to {sample_size}.")

if __name__ == "__main__":
    main()
