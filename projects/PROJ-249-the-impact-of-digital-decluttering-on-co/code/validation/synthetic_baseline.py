"""
Synthetic Baseline Data Generator.

Generates synthetic baseline data for validation purposes.
Outputs to data/raw/synthetic_baseline.csv.

This script implements the distributions described in T017:
- SART errors ~ N(10, 3)
- PSS-10 ~ N(20, 5)
- Ospan ~ N(15, 3)
- PANAS ~ N(30, 5)

Note: This generates synthetic data strictly for SCHEMATIC VALIDATION and
INSTRUMENT LOGIC TESTING (US1). It does NOT replace real data collection (T019.1).
"""

import os
import csv
import yaml
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

# Import from project utils
from utils.random_seed import set_global_seed, get_rng

# Configuration paths
CONFIG_FILE = Path("code/config/synthetic_data_config.yaml")
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "synthetic_baseline.csv"

def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def generate_participant_id(index: int) -> str:
    """Generate a pseudonymous ID in P\\d{3} format."""
    return f"P{index:03d}"

def clip_value(value: float, min_val: float, max_val: float) -> float:
    """Clip value to plausible range."""
    return max(min_val, min(max_val, value))

def generate_synthetic_data(rng: np.random.Generator, config: dict) -> list:
    """Generate synthetic rows for all participants and metrics."""
    rows = []
    base_time = datetime(2023, 10, 1, 9, 0, 0)
    num_participants = config.get("num_participants", 20)

    for i in range(1, num_participants + 1):
        pid = generate_participant_id(i)
        # Offset timestamp slightly per participant to ensure uniqueness
        timestamp = base_time + timedelta(hours=i)

        for metric_name, metric_config in config["metrics"].items():
            # Generate value from normal distribution
            val = rng.normal(metric_config["mean"], metric_config["std"])
            # Clip to valid range
            val = clip_value(val, metric_config["min"], metric_config["max"])
            # Round to 2 decimal places
            val = round(val, 2)

            rows.append({
                "participant_id": pid,
                "metric_type": metric_name,
                "value": val,
                "timestamp": timestamp.isoformat()
            })

    return rows

def write_csv(rows: list, filepath: Path):
    """Write rows to CSV file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["participant_id", "metric_type", "value", "timestamp"]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def main():
    """Main entry point."""
    # Load configuration
    config = load_config(CONFIG_FILE)
    seed = config.get("seed", 42)

    print(f"Generating synthetic baseline data with seed {seed}...")
    set_global_seed(seed)
    rng = get_rng()

    data = generate_synthetic_data(rng, config)
    write_csv(data, OUTPUT_FILE)

    print(f"Successfully wrote {len(data)} records to {OUTPUT_FILE}")
    print("Schema validation ready for T010.")

if __name__ == "__main__":
    main()
