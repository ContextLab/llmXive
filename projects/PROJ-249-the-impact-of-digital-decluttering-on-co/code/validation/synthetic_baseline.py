"""
Synthetic Baseline Data Generator.

Generates synthetic baseline data for validation purposes.
Outputs to data/raw/synthetic_baseline.csv.

This script is required by T010 (Contract Test) to ensure the schema is valid.
It implements the distributions described in T017:
- SART errors ~ N(10, 3)
- PSS-10 ~ N(20, 5)
- Ospan ~ N(15, 3)
- PANAS ~ N(30, 5)

Note: This generates synthetic data strictly for SCHEMATIC VALIDATION and
INSTRUMENT LOGIC TESTING (US1). It does NOT replace real data collection (T019.1).
"""

import os
import csv
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

# Import from project utils
from utils.random_seed import set_global_seed, get_rng

# Configuration
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "synthetic_baseline.csv"
NUM_PARTICIPANTS = 20
SEED = 42

# Metric distributions (mean, std_dev)
# Based on typical psychometric ranges
METRIC_CONFIG = {
    "SART": {"mean": 10.0, "std": 3.0, "min": 0, "max": 50},
    "Ospan": {"mean": 15.0, "std": 3.0, "min": 0, "max": 25},
    "PSS-10": {"mean": 20.0, "std": 5.0, "min": 0, "max": 50},
    "PANAS": {"mean": 30.0, "std": 5.0, "min": 10, "max": 50}
}

def generate_participant_id(index: int) -> str:
    """Generate a pseudonymous ID in P\\d{3} format."""
    return f"P{index:03d}"

def clip_value(value: float, min_val: float, max_val: float) -> float:
    """Clip value to plausible range."""
    return max(min_val, min(max_val, value))

def generate_synthetic_data(rng: np.random.Generator) -> list:
    """Generate synthetic rows for all participants and metrics."""
    rows = []
    base_time = datetime(2023, 10, 1, 9, 0, 0)

    for i in range(1, NUM_PARTICIPANTS + 1):
        pid = generate_participant_id(i)
        timestamp = base_time + timedelta(hours=i)

        for metric_name, config in METRIC_CONFIG.items():
            # Generate value from normal distribution
            val = rng.normal(config["mean"], config["std"])
            # Clip to valid range
            val = clip_value(val, config["min"], config["max"])
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
    print(f"Generating synthetic baseline data with seed {SEED}...")
    set_global_seed(SEED)
    rng = get_rng()

    data = generate_synthetic_data(rng)
    write_csv(data, OUTPUT_FILE)

    print(f"Successfully wrote {len(data)} records to {OUTPUT_FILE}")
    print("Schema validation ready for T010.")

if __name__ == "__main__":
    main()