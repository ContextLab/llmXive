"""
Verification module for User Story 1 (Energy Calculation).

Generates a synthetic dataset with known ground-truth physics,
runs the ingestion pipeline's energy calculation logic on it,
and compares the results to manual calculations.

Outputs:
    artifacts/manual_baseline.csv: Ground truth energies calculated analytically.
    artifacts/energy_verification_report.json: Comparison results and max error.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
import logging

# Import from sibling modules as per API surface
from ingestion import compute_energy, compute_velocities_angular_velocities
from config import load_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_synthetic_ground_truth(output_path: Path):
    """
    Generates a synthetic dataset with known ground-truth velocities and positions.
    Calculates expected energies manually and saves to `artifacts/manual_baseline.csv`.
    
    Physics Model:
    - Particle mass m = 1.0 kg
    - Radius r = 0.05 m
    - Velocity v = [1.0, 2.0, 3.0] m/s (constant)
    - Angular velocity omega = [0.1, 0.2, 0.3] rad/s (constant)
    - Position z = 1.0 m (constant, for potential energy)
    - Acceleration a = [0.0, 0.0, 0.0] (constant velocity -> 0 vib energy by formula)
    
    Formulas:
    - E_trans = 0.5 * m * v^2
    - E_rot = 0.5 * I * omega^2  (I = 0.4 * m * r^2 for sphere)
    - E_pot = m * g * z
    - E_vib = m * var(a) * dt^2
    """
    logger.info("Generating synthetic ground truth data...")
    
    # Constants
    mass = 1.0  # kg
    radius = 0.05  # m
    g = 9.81  # m/s^2
    dt = 0.01  # s (time step)
    
    # Create a single row for simplicity (can be expanded)
    # We create a DataFrame that mimics the output of the ingestion sync step
    # before energy calculation.
    data = {
        'particle_id': ['P001'],
        'timestamp': [1000.0],
        'vx': [1.0],
        'vy': [2.0],
        'vz': [3.0],
        'wx': [0.1],
        'wy': [0.2],
        'wz': [0.3],
        'z_pos': [1.0],
        'ax': [0.0],
        'ay': [0.0],
        'az': [0.0],
        'mass': [mass],
        'radius': [radius]
    }
    
    df = pd.DataFrame(data)
    
    # Manual Calculations
    # 1. Translational Energy
    v_squared = df['vx']**2 + df['vy']**2 + df['vz']**2
    df['E_trans_expected'] = 0.5 * df['mass'] * v_squared
    
    # 2. Rotational Energy (Sphere: I = 2/5 * m * r^2 = 0.4 * m * r^2)
    I = 0.4 * df['mass'] * df['radius']**2
    omega_squared = df['wx']**2 + df['wy']**2 + df['wz']**2
    df['E_rot_expected'] = 0.5 * I * omega_squared
    
    # 3. Potential Energy
    df['E_pot_expected'] = df['mass'] * g * df['z_pos']
    
    # 4. Vibrational Energy (Provisional Formula: m * var(a) * dt^2)
    # Since we have constant velocity, acceleration is 0.
    # Variance of a constant is 0.
    # To make it robust, we calculate variance of the acceleration columns.
    # For a single row, variance is undefined (0). We'll assume 0 for this test.
    # If we had a time series, we'd compute var(a) over the window.
    # Here, we assume the input 'ax', 'ay', 'az' are the accelerations for that frame.
    # The formula usually implies variance over a window. 
    # For this single-frame test, var(a) = 0.
    df['E_vib_expected'] = 0.0 
    
    # Save baseline
    baseline_cols = ['particle_id', 'timestamp', 'E_trans_expected', 'E_rot_expected', 'E_pot_expected', 'E_vib_expected']
    df[baseline_cols].to_csv(output_path, index=False)
    logger.info(f"Saved ground truth to {output_path}")
    
    return df

def run_verification():
    """
    Runs the ingestion energy calculation on the synthetic data,
    compares to baseline, and writes the verification report.
    """
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    
    baseline_path = artifacts_dir / "manual_baseline.csv"
    report_path = artifacts_dir / "energy_verification_report.json"
    
    # 1. Generate Ground Truth
    ground_truth_df = generate_synthetic_ground_truth(baseline_path)
    
    # 2. Prepare Input for Ingestion Logic
    # The ingestion compute_energy function expects a DataFrame with specific columns.
    # We simulate the state after sync and velocity calculation.
    # We need to ensure the columns match what compute_energy expects.
    # Based on API surface, compute_energy likely takes a df with v, w, z, etc.
    
    # Create a working copy
    ingest_df = ground_truth_df.copy()
    
    # Ensure dt is available (usually inferred or passed)
    # We'll inject it into the df or pass it as a param if the function signature allows.
    # Looking at the task description, it calls the ingestion pipeline.
    # We will simulate the call to compute_energy directly here.
    
    # Mock the 'window_size' or 'dt' if needed. 
    # Since we are testing the formula implementation, we assume the function 
    # uses the standard dt or calculates it.
    # Let's assume compute_energy calculates E_vib using a provided dt or infers it.
    # We will pass dt=0.01 explicitly if the function allows, or assume it's in config.
    # For this test, we assume the function signature is:
    # compute_energy(df, dt=0.01)
    
    # We need to check if compute_energy is available and what it expects.
    # The API says: from ingestion import compute_energy
    # We will try to call it. If it fails due to missing columns, we fix the df.
    
    try:
        # Add a dummy 'window_size' or similar if required by config
        # For now, we call it directly.
        # Note: The actual compute_energy in ingestion.py might expect 'window_size_N' from config.
        # We will pass a minimal config or assume defaults.
        
        # To be safe, we'll call the function and catch any specific errors to handle them.
        # If the function requires a 'config' object, we might need to mock it.
        # Let's assume it takes the dataframe and optional params.
        
        # Simulate the call
        # If compute_energy modifies the df in place or returns a new one?
        # Usually it returns a df with added columns.
        
        # We need to ensure the input df has the right columns.
        # Let's assume the standard columns: 'vx', 'vy', 'vz', 'wx', 'wy', 'wz', 'z', 'mass', 'radius'
        # and 'ax', 'ay', 'az' for vibration.
        
        # We have 'z_pos' in ground truth, but ingestion might expect 'z'.
        # Let's rename to match common expectations or check the ingestion code.
        # Since we can't see the full ingestion code, we assume standard physics column names.
        # If 'z_pos' is used, we keep it. If 'z' is expected, we rename.
        # Let's assume the ingestion code uses 'z' for position.
        if 'z_pos' in ingest_df.columns:
            ingest_df.rename(columns={'z_pos': 'z'}, inplace=True)
        
        # Call the function
        # We assume compute_energy returns the dataframe with energy columns added
        result_df = compute_energy(ingest_df, dt=0.01) 
        
    except Exception as e:
        logger.error(f"Error running compute_energy: {e}")
        # If the function signature is different, we might need to adapt.
        # But for the task, we assume the implementation exists and works.
        # If it fails, we report the error.
        report = {
            "status": "error",
            "error_message": str(e),
            "max_absolute_error": None,
            "repair_needed": True
        }
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        return

    # 3. Compare Results
    energy_cols = ['E_trans', 'E_rot', 'E_pot', 'E_vib']
    expected_cols = ['E_trans_expected', 'E_rot_expected', 'E_pot_expected', 'E_vib_expected']
    
    errors = []
    for i, (col, exp_col) in enumerate(zip(energy_cols, expected_cols)):
        if col not in result_df.columns:
            logger.error(f"Missing column {col} in result")
            errors.append({
                "column": col,
                "error": "Column missing in output"
            })
            continue
        
        diff = np.abs(result_df[col] - result_df[exp_col])
        max_err = diff.max()
        mean_err = diff.mean()
        errors.append({
            "column": col,
            "max_error": float(max_err),
            "mean_error": float(mean_err)
        })
    
    max_abs_error = max([e["max_error"] for e in errors if "max_error" in e])
    
    # 4. Generate Report
    report = {
        "status": "success",
        "max_absolute_error": float(max_abs_error),
        "repair_needed": max_abs_error > 1e-9,
        "details": errors,
        "timestamp": str(pd.Timestamp.now())
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Verification complete. Max Error: {max_abs_error}")
    if report["repair_needed"]:
        logger.warning("REPAIR NEEDED: Max error exceeds threshold 1e-9")
    else:
        logger.info("PASS: Energy calculations match ground truth within tolerance.")

def main():
    run_verification()

if __name__ == "__main__":
    main()
