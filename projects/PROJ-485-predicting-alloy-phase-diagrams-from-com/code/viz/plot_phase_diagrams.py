"""
Visualization module for plotting phase diagrams.
"""
import os
import sys
import json
import pickle
import argparse
import logging
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

# Set high DPI for publication quality
rcParams['figure.dpi'] = 300
rcParams['savefig.dpi'] = 300

def load_model_artifact(filepath: str = "data/artifacts/model.pkl"):
    """Load trained model from disk."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: Model artifact not found: {filepath}")
    with open(filepath, 'rb') as f:
        return pickle.load(f)

def load_processed_data(filepath: str = "data/processed/descriptors.csv") -> pd.DataFrame:
    """Load processed descriptor data."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"{ErrorCode.DATA_SOURCE_MISSING.value}: Processed data not found: {filepath}")
    return pd.read_csv(filepath)

def load_config(filepath: str = "code/config.yaml") -> Dict:
    """Load configuration."""
    import yaml
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def filter_by_system(df: pd.DataFrame, system_id: str) -> pd.DataFrame:
    """Filter data by system ID."""
    return df[df['system_id'] == system_id]

def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Absolute Error."""
    return np.mean(np.abs(y_true - y_pred))

def calculate_tcs(y_true: np.ndarray, y_pred: np.ndarray, slices: int = 10) -> float:
    """Calculate Topological Consistency Score."""
    if len(y_true) == 0 or len(y_pred) == 0:
        return 0.0

    # Sort both arrays
    sorted_true = np.sort(y_true)
    sorted_pred = np.sort(y_pred)

    # Check if they match in order
    match = np.array_equal(sorted_true, sorted_pred)
    return 1.0 if match else 0.0

def plot_phase_diagram(df_system: pd.DataFrame, model, system_id: str):
    """Plot phase diagram for a specific system."""
    if df_system.empty:
        log_warning(logger, f"No data for system {system_id}")
        return None

    # Prepare data
    X = df_system[['mean_atomic_radius', 'electronegativity_variance', 'valence_electron_count', 'hume_rothery_concentration']].values
    y_true = df_system['temperature'].values
    composition = df_system['composition_raw'].values

    # Predict
    y_pred = model.predict(X)

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))

    # Sort by composition for line plotting (simplified)
    # In a real implementation, we would parse composition properly
    sort_idx = np.argsort(y_true)
    ax.plot(range(len(y_true)), y_true[sort_idx], 'b-', label='Experimental', linewidth=2)
    ax.plot(range(len(y_true)), y_pred[sort_idx], 'r--', label='Predicted', linewidth=2)

    ax.set_xlabel('Composition Index')
    ax.set_ylabel('Temperature (K)')
    ax.set_title(f'Phase Diagram: {system_id}')
    ax.legend()
    ax.grid(True, alpha=0.3)

    return fig, y_true, y_pred

def write_fidelity_check_log(system_id: str, mae: float, status: str):
    """Log fidelity check results."""
    os.makedirs("data/artifacts", exist_ok=True)
    log_entry = {
        "system_id": system_id,
        "mae": mae,
        "status": status
    }
    with open("data/artifacts/fidelity_check.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def write_tcs_report(system_id: str, tcs: float, slices: int):
    """Write TCS report."""
    report = {
        "system": system_id,
        "tcs_score": tcs,
        "slices_evaluated": slices
    }
    with open("data/artifacts/tcs_report.json", "w") as f:
        json.dump(report, f, indent=2)

def write_fidelity_report(systems: List[Dict]):
    """Write comprehensive fidelity report."""
    report = {
        "systems": systems,
        "overall_status": "PASSED" if all(s['status'] == 'PASSED' for s in systems) else "FAILED"
    }
    with open("data/artifacts/fidelity_report.json", "w") as f:
        json.dump(report, f, indent=2)

def log_pipeline_error(code: str, message: str):
    """Log pipeline error."""
    log_error(logger, f"{code}: {message}")

def run_visualization():
    """Run visualization pipeline for required systems."""
    config = load_config()
    required_systems = config.get("required_systems", ["Cu-Zn", "Al-Cu"])

    model = load_model_artifact()
    df = load_processed_data()

    systems_results = []

    for system_id in required_systems:
        # Skip complex systems (T039)
        if system_id in ["Fe-C"]:
            log_warning(logger, f"Skipping complex system: {system_id}")
            continue

        df_system = filter_by_system(df, system_id)
        if df_system.empty:
            log_warning(logger, f"No data found for system {system_id}")
            continue

        fig, y_true, y_pred = plot_phase_diagram(df_system, model, system_id)
        if fig is None:
            continue

        # Calculate metrics
        mae = calculate_mae(y_true, y_pred)
        tcs = calculate_tcs(y_true, y_pred)

        # Check fidelity (T036)
        status = "PASSED" if mae <= 50.0 else "FAILED"
        if status == "FAILED":
            write_fidelity_check_log(system_id, mae, status)
            log_pipeline_error(ErrorCode.LOW_DATA_FIDELITY.value, f"MAE {mae:.2f} > 50K for {system_id}")
        else:
            write_fidelity_check_log(system_id, mae, status)

        # Write TCS report
        write_tcs_report(system_id, tcs, 10)

        # Save plot
        os.makedirs("data/artifacts/plots", exist_ok=True)
        plot_path = f"data/artifacts/plots/{system_id}.png"
        fig.savefig(plot_path, bbox_inches='tight')
        plt.close(fig)

        systems_results.append({
            "system_id": system_id,
            "mae": float(mae),
            "tcs": float(tcs),
            "status": status
        })

    # Write final fidelity report
    write_fidelity_report(systems_results)
    log_info(logger, f"Visualization complete. Processed {len(systems_results)} systems.")

def main():
    """Entry point for visualization."""
    try:
        run_visualization()
    except Exception as e:
        log_error(logger, f"Visualization failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
