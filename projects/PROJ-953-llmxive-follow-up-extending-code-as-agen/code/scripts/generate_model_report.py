"""
Model Report Generation Module.

Generates a comprehensive JSON report containing model performance,
threshold analysis, and safety flags.
"""
import os
import sys
import json
import pickle
import argparse
from pathlib import Path

from config.loader import get_config

def load_threshold_sweep_safe(json_path: Path) -> dict:
    """Load threshold sweep results, handling missing files gracefully."""
    if not json_path.exists():
        return {"error": "Threshold sweep file not found"}
    with open(json_path, 'r') as f:
        return json.load(f)

def load_decision_boundary(pkl_path: Path) -> dict:
    """Load decision boundary pickle file."""
    if not pkl_path.exists():
        return {"error": "Decision boundary file not found"}
    with open(pkl_path, 'rb') as f:
        return pickle.load(f)

def generate_model_report(sweep_data: dict, boundary_data: dict, correlations: dict) -> dict:
    """
    Generate the final model report.
    Includes FNRs, safety flag, and correlation coefficient.
    """
    report = {
        "model_type": boundary_data.get("model_type", "unknown"),
        "thresholds": sweep_data.get("thresholds", {}),
        "min_fnr": sweep_data.get("min_fnr", None),
        "target_fnr_met": sweep_data.get("target_fnr_met", False),
        "unsafe_flag": not sweep_data.get("target_fnr_met", False),
        "correlation_coefficient": correlations.get("best_feature_corr", 0.0),
        "statement": "Results are associational and do not imply causation (FR-006)."
    }
    return report

def main():
    """Main entry point."""
    config = get_config()
    data_dir = Path(config.get("data_dir", "data"))
    models_dir = Path(config.get("models_dir", "models"))
    processed_dir = data_dir / "processed"

    sweep_path = models_dir / "threshold_sweep.json"
    boundary_path = models_dir / "decision_boundary.pkl"
    corr_path = models_dir / "correlations.json"
    output_path = processed_dir / "model_report.json"

    # Load data
    sweep_data = load_threshold_sweep_safe(sweep_path)
    boundary_data = load_decision_boundary(boundary_path)
    
    correlations = {}
    if corr_path.exists():
        with open(corr_path, 'r') as f:
            correlations = json.load(f)
    
    # Extract best correlation if available
    best_corr = 0.0
    if correlations and isinstance(correlations, dict):
        # Find the max absolute correlation
        vals = [abs(v) for v in correlations.values() if isinstance(v, float)]
        if vals:
            best_corr = max(vals)

    report = generate_model_report(sweep_data, boundary_data, {"best_feature_corr": best_corr})

    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Model report generated at {output_path}")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
