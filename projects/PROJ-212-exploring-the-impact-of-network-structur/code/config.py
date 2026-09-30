import yaml
import os
from pathlib import Path

def load_config(config_path: str = "config.yaml") -> dict:
    """
    Loads the configuration from a YAML file.
    """
    if not os.path.exists(config_path):
        # Return default config if file doesn't exist
        return {
            "random_seed": 42,
            "thresholds": {
                "r": 0.8,
                "t": 100
            },
            "simulation": {
                "n_oscillators": 200,
                "k_range": [0, 5],
                "tolerance": 0.001,
                "dt": 0.01
            }
        }
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_paths() -> dict:
    """
    Returns a dictionary of paths relative to the project root.
    """
    base = Path(__file__).parent
    return {
        "project_root": base,
        "data_raw": base / "data" / "raw",
        "data_processed": base / "data" / "processed",
        "results_dir": base / "results",
        "state_dir": base / "state",
        "figures_dir": base / "figures"
    }
