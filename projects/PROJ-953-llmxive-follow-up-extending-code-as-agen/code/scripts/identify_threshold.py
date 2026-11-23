"""
Threshold Identification Module.

Identifies the optimal decision threshold based on False Negative Rate (FNR)
constraints.
"""
import os
import json
import pickle
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from config.loader import get_config

def load_threshold_sweep(json_path: Path) -> Dict[str, Any]:
    """Load threshold sweep results."""
    if not json_path.exists():
        raise FileNotFoundError(f"Threshold sweep file not found: {json_path}")
    with open(json_path, 'r') as f:
        return json.load(f)

def identify_optimal_threshold(sweep_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Identify the optimal threshold that meets the FNR <= 0.1% target.
    If none meet it, return the one with the lowest FNR.
    """
    thresholds = sweep_data.get("thresholds", {})
    target_fnr = 0.001 # 0.1%

    valid_thresholds = [
        (t, data.get("fnr", 1.0)) 
        for t, data in thresholds.items() 
        if data.get("fnr", 1.0) <= target_fnr
    ]

    if valid_thresholds:
        # Choose the one with the lowest FNR
        best = min(valid_thresholds, key=lambda x: x[1])
        return {
            "optimal_threshold": float(best[0]),
            "fnr": best[1],
            "target_met": True
        }
    else:
        # Choose the one with the lowest FNR overall
        all_thresholds = [
            (t, data.get("fnr", 1.0)) 
            for t, data in thresholds.items()
        ]
        if not all_thresholds:
            return {"optimal_threshold": 0.5, "fnr": 1.0, "target_met": False}
        
        worst = min(all_thresholds, key=lambda x: x[1])
        return {
            "optimal_threshold": float(worst[0]),
            "fnr": worst[1],
            "target_met": False,
            "min_achievable_fnr": worst[1]
        }

def save_decision_boundary(optimal_data: Dict[str, Any], model_artifacts: dict, output_path: Path) -> None:
    """Save the decision boundary and model artifacts."""
    boundary_data = {
        "optimal_threshold": optimal_data["optimal_threshold"],
        "target_met": optimal_data["target_met"],
        "model_type": model_artifacts.get("best_model", "unknown")
    }
    with open(output_path, 'wb') as f:
        pickle.dump(boundary_data, f)

def main():
    """Main entry point."""
    config = get_config()
    models_dir = Path(config.get("models_dir", "models"))
    sweep_path = models_dir / "threshold_sweep.json"

    if not sweep_path.exists():
        print("Error: Threshold sweep file not found. Run sensitivity analysis first.")
        sys.exit(1)

    sweep_data = load_threshold_sweep(sweep_path)
    optimal = identify_optimal_threshold(sweep_data)

    # Load model artifacts to determine model type
    model_path = models_dir / "trained_models.pkl"
    model_artifacts = {}
    if model_path.exists():
        with open(model_path, 'rb') as f:
            model_artifacts = pickle.load(f)

    boundary_path = models_dir / "decision_boundary.pkl"
    save_decision_boundary(optimal, model_artifacts, boundary_path)

    print(f"Optimal threshold identified: {optimal['optimal_threshold']}")
    print(f"Target met: {optimal['target_met']}")
    print(f"FNR: {optimal['fnr']}")

if __name__ == "__main__":
    main()
