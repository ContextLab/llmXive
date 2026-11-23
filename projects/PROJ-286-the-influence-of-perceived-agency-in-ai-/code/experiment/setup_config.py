import json
import os
import sys
from pathlib import Path
import yaml

def load_json_file(path: Path) -> dict:
    """Load a JSON file and return its contents as a dictionary."""
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    """
    Main entry point for T008: Setup environment configuration management.
    Reads research/power_calculation.json and writes code/experiment/config.yaml.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    power_calc_path = project_root / "research" / "power_calculation.json"
    config_output_path = project_root / "code" / "experiment" / "config.yaml"

    if not power_calc_path.exists():
        print(f"Error: Required input file not found: {power_calc_path}", file=sys.stderr)
        print("Dependency T002 (Power Analysis) must be completed first.", file=sys.stderr)
        sys.exit(1)

    try:
        power_data = load_json_file(power_calc_path)
        
        # Validate structure
        if "results" not in power_data or "required_n" not in power_data["results"]:
            raise KeyError("Missing 'results.required_n' in power_calculation.json")
        
        sample_size = power_data["results"]["required_n"]
        
        # Default values as per task spec
        alpha_level = 0.05
        seed = 42
        data_path = "data/raw/"

        config = {
            "sample_size": sample_size,
            "alpha_level": alpha_level,
            "seed": seed,
            "data_path": data_path
        }

        # Ensure output directory exists
        config_output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write YAML
        with open(config_output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print(f"Configuration written to: {config_output_path}")
        print(f"Sample size loaded from power analysis: {sample_size}")

    except Exception as e:
        print(f"Error generating config: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
