"""
Standardization module for T020.
Handles unit standardization, stratification, and statistical gating.
"""
from __future__ import annotations

import csv
import json
import logging
import math
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_data_path() -> Path:
    return PROJECT_ROOT / "data"

def load_config() -> Dict[str, Any]:
    config_file = get_data_path() / "config.yaml"
    if not config_file.exists():
        logger.error(f"Config file not found: {config_file}")
        return {}
    try:
        import yaml
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

def load_gate_status() -> Dict[str, Any]:
    gate_file = get_data_path() / "gate_status.json"
    if not gate_file.exists():
        logger.error(f"Gate status file not found: {gate_file}")
        return {"status": "FAIL", "reason": "File missing"}
    with open(gate_file, 'r') as f:
        return json.load(f)

def save_stat_gate_status(status: Dict[str, Any]) -> None:
    stat_gate_file = get_data_path() / "stat_gate_status.json"
    stat_gate_file.parent.mkdir(parents=True, exist_ok=True)
    with open(stat_gate_file, 'w') as f:
        json.dump(status, f, indent=2)
    logger.info(f"Statistical gate status saved to {stat_gate_file}")

def standardize_and_stratify() -> None:
    """
    1. Check Gate Status.
    2. Load merged_drugs.csv.
    3. Standardize units (time to hours, k to t1/2).
    4. Create full dataset and standard subset.
    5. Apply statistical gate (N_std >= 30).
    """
    # 1. Check Gate
    gate_status = load_gate_status()
    if gate_status.get("status") != "PASS":
        logger.error("Data Availability Gate failed. Stopping standardization.")
        stat_status = {
            "status": "FAIL",
            "reason": "Data Availability Gate Failed",
            "N_std": 0
        }
        save_stat_gate_status(stat_status)
        # Generate insufficiency report logic could be here or in a separate script
        return

    # 2. Load Data
    merged_file = get_data_path() / "processed" / "merged_drugs.csv"
    if not merged_file.exists():
        logger.error(f"Merged drugs file not found: {merged_file}")
        stat_status = {"status": "FAIL", "reason": "Merged file missing", "N_std": 0}
        save_stat_gate_status(stat_status)
        return

    df = pd.read_csv(merged_file)
    logger.info(f"Loaded {len(df)} records from merged_drugs.csv")

    # 3. Standardize
    # Convert time units to hours (assuming input is in days or seconds, logic depends on data)
    # For this task, we assume 'time_unit' column exists or default to hours.
    # Convert k to t1/2: t1/2 = ln(2) / k
    if 'rate_constant' in df.columns:
        df['half_life'] = math.log(2) / df['rate_constant']
    elif 'half_life' not in df.columns:
        logger.error("No rate_constant or half_life column found.")
        stat_status = {"status": "FAIL", "reason": "No degradation column", "N_std": 0}
        save_stat_gate_status(stat_status)
        return

    # 4. Create Datasets
    # Full dataset
    full_file = get_data_path() / "processed" / "full_dataset_with_covariates.csv"
    df.to_csv(full_file, index=False)
    logger.info(f"Saved full dataset to {full_file}")

    # Standard subset: Temp 20-30, pH 7.35-7.45
    config = load_config()
    temp_min = config.get("temp_min", 20.0)
    temp_max = config.get("temp_max", 30.0)
    ph_min = config.get("ph_min", 7.35)
    ph_max = config.get("ph_max", 7.45)

    mask = (
        (df['temperature'] >= temp_min) & (df['temperature'] <= temp_max) &
        (df['ph'] >= ph_min) & (df['ph'] <= ph_max)
    )
    standard_df = df[mask]
    
    standard_file = get_data_path() / "processed" / "standard_subset.csv"
    standard_df.to_csv(standard_file, index=False)
    logger.info(f"Saved standard subset to {standard_file} ({len(standard_df)} records)")

    # 5. Statistical Gate
    N_std = len(standard_df)
    if N_std < 30:
        logger.warning(f"Statistical Gate Failed: N_std={N_std} < 30")
        stat_status = {
            "status": "FAIL",
            "reason": "N_std < 30",
            "N_std": N_std
        }
        save_stat_gate_status(stat_status)
        # Generate data insufficiency report
        insuff_file = get_data_path() / "data_insufficiency_report.md"
        with open(insuff_file, 'w') as f:
            f.write(f"# Data Insufficiency Report\n\n")
            f.write(f"## Statistical Gate Failure\n\n")
            f.write(f"The number of records under standard conditions ({N_std}) is less than the required minimum of 30.\n")
        logger.info(f"Generated insufficiency report: {insuff_file}")
    else:
        logger.info(f"Statistical Gate Passed: N_std={N_std} >= 30")
        stat_status = {
            "status": "PASS",
            "N_std": N_std
        }
        save_stat_gate_status(stat_status)

def main():
    """Main entry point."""
    logger.info("Starting Standardization Module...")
    standardize_and_stratify()
    logger.info("Standardization complete.")

if __name__ == '__main__':
    main()
