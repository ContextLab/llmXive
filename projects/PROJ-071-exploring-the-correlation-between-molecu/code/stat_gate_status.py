"""
Module to handle statistical gate status.
Writes data/stat_gate_status.json based on standard subset filtering.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from config import get_config

def get_data_path() -> str:
    """Return the project data directory."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

def load_gate_status() -> Dict[str, Any]:
    """Load main gate status."""
    gate_path = os.path.join(get_data_path(), 'gate_status.json')
    if not os.path.exists(gate_path):
        return {"status": "FAIL", "reason": "Main gate file not found"}
    with open(gate_path, 'r') as f:
        return json.load(f)

def load_standard_subset() -> pd.DataFrame:
    """Load the standard subset dataset."""
    subset_path = os.path.join(get_data_path(), 'processed', 'standard_subset.csv')
    if not os.path.exists(subset_path):
        raise FileNotFoundError(f"Standard subset file not found: {subset_path}")
    return pd.read_csv(subset_path)

def save_stat_gate_status(status: Dict[str, Any]) -> None:
    """Save statistical gate status to data/stat_gate_status.json."""
    output_path = os.path.join(get_data_path(), 'stat_gate_status.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(status, f, indent=2)
    print(f"Statistical gate status saved to {output_path}")

def main() -> None:
    """
    Main entry point to compute and save statistical gate status.
    This script is invoked by the pipeline to ensure stat_gate_status.json exists.
    """
    print("Computing statistical gate status...")

    # Check main gate
    gate_status = load_gate_status()
    if gate_status.get('status') != 'PASS':
        print("Main gate failed. Skipping statistical gate check.")
        save_stat_gate_status({
            "status": "FAIL",
            "reason": "Main gate failed",
            "N_std": 0
        })
        sys.exit(1)

    # Load standard subset
    try:
        df = load_standard_subset()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        save_stat_gate_status({
            "status": "FAIL",
            "reason": "Standard subset not found",
            "N_std": 0
        })
        sys.exit(1)

    # Count valid records
    n_std = len(df)

    # Gate logic: N_std >= 30
    if n_std < 30:
        status = {
            "status": "FAIL",
            "reason": "N_std < 30",
            "N_std": n_std
        }
        save_stat_gate_status(status)
        print(f"Statistical gate FAILED: N_std = {n_std} (< 30)")
        sys.exit(1)
    else:
        status = {
            "status": "PASS",
            "reason": "Sufficient data",
            "N_std": n_std
        }
        save_stat_gate_status(status)
        print(f"Statistical gate PASSED: N_std = {n_std}")

if __name__ == '__main__':
    main()