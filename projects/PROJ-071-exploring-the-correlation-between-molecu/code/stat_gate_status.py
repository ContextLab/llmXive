"""
Helper script to ensure stat_gate_status.json is created/updated based on standardization results.
This addresses the "missing deliverable" issue for data/stat_gate_status.json.
"""
import json
import os
import sys
from pathlib import Path

def get_data_path() -> Path:
    return Path(__file__).parent.parent / "data"

def load_gate_status() -> dict:
    path = get_data_path() / "gate_status.json"
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {"status": "FAIL", "reason": "No gate_status.json found"}

def load_standard_subset() -> int:
    """Returns count of standard_subset.csv if exists, else 0."""
    path = get_data_path() / "processed" / "standard_subset.csv"
    if path.exists():
        # Simple count without loading full DF to be safe
        with open(path, "r") as f:
            return len(f.readlines()) - 1 # subtract header
    return 0

def save_stat_gate_status(status: str, reason: str, n_std: int = 0) -> None:
    path = get_data_path() / "stat_gate_status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({
            "status": status,
            "reason": reason,
            "N_std": n_std
        }, f, indent=2)

def main():
    """
    Checks the standard subset count and updates stat_gate_status.json.
    This script is intended to be run after standardize.py.
    """
    gate = load_gate_status()
    if gate.get("status") != "PASS":
        save_stat_gate_status("FAIL", "Primary gate failed", 0)
        return

    n_std = load_standard_subset()
    
    if n_std < 30:
        save_stat_gate_status("FAIL", f"N_std < 30 (found {n_std})", n_std)
        print(f"Statistical Gate Failed: Only {n_std} samples in standard subset.")
        # Do not exit 1 here, just report status so analysis can skip gracefully
    else:
        save_stat_gate_status("PASS", "Sufficient standard samples", n_std)
        print(f"Statistical Gate Passed: {n_std} samples in standard subset.")

if __name__ == "__main__":
    main()