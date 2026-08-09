"""
Verification module for User Story 1 (Energy Component Calculation).

This module implements an independent test to verify the energy calculation
logic in code/ingestion.py. It generates a synthetic dataset with known
ground-truth velocities and positions, calculates expected energies manually,
runs the ingestion pipeline on this data, and compares the results.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
import argparse
import logging
import hashlib

# Add parent directory to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion import compute_derivatives, calculate_energy_components, load_and_sample

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_synthetic_ground_truth(output_dir: str, n_particles: int = 5, n_frames: int = 100, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate a synthetic dataset with known ground-truth velocities and positions.
    
    Creates:
    1. A tracking CSV with positions and orientations (known ground truth)
    2. A baseline CSV with manually calculated expected energies
    
    Args:
        output_dir: Directory to save the generated files
        n_particles: Number of particles to simulate
        n_frames: Number of time frames
        seed: Random seed for reproducibility
    
    Returns:
        Tuple of (tracking_df, baseline_df)
    """
    np.random.seed(seed)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Parameters for synthetic data
    mass = 0.001  # kg (1 gram)
    inertia = 1e-7  # kg*m^2 (simplified sphere)
    dt = 0.01  # seconds
    time = np.arange(n_frames) * dt
    
    # Generate ground truth trajectories
    # We create smooth trajectories with known velocities
    tracking_data = []
    baseline_data = []
    
    for pid in range(n_particles):
        # Random initial position and velocity
        x0 = np.random.uniform(-0.01, 0.01)
        y0 = np.random.uniform(-0.01, 0.01)
        z0 = np.random.uniform(0.001, 0.005)  # Above surface
        
        vx0 = np.random.uniform(-0.1, 0.1)
        vy0 = np.random.uniform(-0.1, 0.1)
        vz0 = np.random.uniform(-0.05, 0.05)
        
        # Random angular velocity
        omega_x0 = np.random.uniform(-10, 10)
        omega_y0 = np.random.uniform(-10, 10)
        omega_z0 = np.random.uniform(-10, 10)
        
        # Create smooth trajectories with small noise
        x = x0 + vx0 * time + 0.5 * np.random.uniform(-0.001, 0.001) * time**2
        y = y0 + vy0 * time + 0.5 * np.random.uniform(-0.001, 0.001) * time**2
        z = z0 + vz0 * time + 0.5 * np.random.uniform(-0.0001, 0.0001) * time**2
        
        # Ensure z stays positive (above surface)
        z = np.maximum(z, 0.0001)
        
        # Angular positions (for rotation)
        theta_x = omega_x0 * time
        theta_y = omega_y0 * time
        theta_z = omega_z0 * time
        
        for frame_idx, t in enumerate(time):
            # Ground truth velocities (analytical derivative of the trajectory)
            vx_true = vx0 + np.random.uniform(-0.001, 0.001) * frame_idx
            vy_true = vy0 + np.random.uniform(-0.001, 0.001) * frame_idx
            vz_true = vz0 + np.random.uniform(-0.0001, 0.0001) * frame_idx
            
            # Ground truth angular velocities
            omega_x_true = omega_x0
            omega_y_true = omega_y0
            omega_z_true = omega_z0
            
            # Calculate expected energies
            # E_trans = 0.5 * m * v^2
            v_sq = vx_true**2 + vy_true**2 + vz_true**2
            E_trans_true = 0.5 * mass * v_sq
            
            # E_rot = 0.5 * I * omega^2
            omega_sq = omega_x_true**2 + omega_y_true**2 + omega_z_true**2
            E_rot_true = 0.5 * inertia * omega_sq
            
            # E_pot = m * g * h (g = 9.81 m/s^2)
            g = 9.81
            E_pot_true = mass * g * z[frame_idx]
            
            # E_vib = m * var(a) * dt^2 (provisional formula from T018b)
            # For synthetic data, we'll estimate acceleration variance from a small window
            # Since our trajectory is smooth, acceleration is near zero
            # We'll add a small random acceleration component for realism
            ax = np.random.uniform(-0.01, 0.01)
            ay = np.random.uniform(-0.01, 0.01)
            az = np.random.uniform(-0.001, 0.001)
            a_sq = ax**2 + ay**2 + az**2
            # For a single point, var(a) is 0, but we'll use the magnitude as a proxy
            # In practice, this would be calculated over a window
            E_vib_true = mass * a_sq * dt**2 * 100  # Scaled up for visibility
            
            tracking_data.append({
                'particle_id': pid,
                'timestamp': t,
                'x': x[frame_idx],
                'y': y[frame_idx],
                'z': z[frame_idx],
                'theta_x': theta_x[frame_idx],
                'theta_y': theta_y[frame_idx],
                'theta_z': theta_z[frame_idx],
                'frame_id': frame_idx
            })
            
            baseline_data.append({
                'particle_id': pid,
                'timestamp': t,
                'E_trans_expected': E_trans_true,
                'E_rot_expected': E_rot_true,
                'E_pot_expected': E_pot_true,
                'E_vib_expected': E_vib_true,
                'v_x_true': vx_true,
                'v_y_true': vy_true,
                'v_z_true': vz_true,
                'omega_x_true': omega_x_true,
                'omega_y_true': omega_y_true,
                'omega_z_true': omega_z_true
            })
    
    tracking_df = pd.DataFrame(tracking_data)
    baseline_df = pd.DataFrame(baseline_data)
    
    # Save to CSV
    tracking_path = output_path / 'synthetic_tracking.csv'
    baseline_path = output_path / 'manual_baseline.csv'
    
    tracking_df.to_csv(tracking_path, index=False)
    baseline_df.to_csv(baseline_path, index=False)
    
    logger.info(f"Generated synthetic tracking data: {tracking_path}")
    logger.info(f"Generated manual baseline: {baseline_path}")
    
    return tracking_df, baseline_df


def run_verification(tracking_path: str, baseline_path: str, config_path: str = None) -> dict:
    """
    Run the ingestion pipeline on synthetic data and compare with manual baseline.
    
    Args:
        tracking_path: Path to the synthetic tracking CSV
        baseline_path: Path to the manual baseline CSV
        config_path: Optional path to config.yaml (if None, uses defaults)
    
    Returns:
        Dictionary containing verification results
    """
    logger.info(f"Loading synthetic tracking data from: {tracking_path}")
    df = pd.read_csv(tracking_path)
    
    # Load baseline
    logger.info(f"Loading manual baseline from: {baseline_path}")
    baseline = pd.read_csv(baseline_path)
    
    # Compute derivatives (velocities and angular velocities)
    logger.info("Computing derivatives (velocities)...")
    df_with_derivs = compute_derivatives(df, dt=0.01)
    
    # Calculate energy components
    logger.info("Calculating energy components...")
    # Use default parameters if no config provided
    if config_path and os.path.exists(config_path):
        from config import load_config
        config = load_config(config_path)
        mass = config.get('mass', 0.001)
        inertia = config.get('inertia', 1e-7)
        g = config.get('gravity', 9.81)
        window_size = config.get('window_size_N', 10)
    else:
        mass = 0.001
        inertia = 1e-7
        g = 9.81
        window_size = 10
    
    df_with_energy = calculate_energy_components(df_with_derivs, mass=mass, inertia=inertia, g=g, window_size=window_size)
    
    # Merge with baseline for comparison
    comparison = pd.merge(df_with_energy, baseline, on=['particle_id', 'timestamp'], how='inner')
    
    # Calculate errors
    errors = {
        'E_trans': np.abs(comparison['E_trans'] - comparison['E_trans_expected']),
        'E_rot': np.abs(comparison['E_rot'] - comparison['E_rot_expected']),
        'E_pot': np.abs(comparison['E_pot'] - comparison['E_pot_expected']),
        'E_vib': np.abs(comparison['E_vib'] - comparison['E_vib_expected'])
    }
    
    max_errors = {key: float(err.max()) for key, err in errors.items()}
    mean_errors = {key: float(err.mean()) for key, err in errors.items()}
    
    overall_max_error = max(max_errors.values())
    repair_needed = overall_max_error > 1e-9
    
    report = {
        'max_absolute_errors': max_errors,
        'mean_absolute_errors': mean_errors,
        'overall_max_error': overall_max_error,
        'repair_needed': repair_needed,
        'n_samples': len(comparison),
        'verification_passed': not repair_needed,
        'threshold': 1e-9
    }
    
    return report


def main():
    """Main entry point for verification script."""
    parser = argparse.ArgumentParser(description='Verify energy implementation against ground truth')
    parser.add_argument('--output-dir', type=str, default='artifacts',
                      help='Directory to output verification artifacts')
    parser.add_argument('--n-particles', type=int, default=5,
                      help='Number of particles in synthetic dataset')
    parser.add_argument('--n-frames', type=int, default=100,
                      help='Number of frames per particle')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed for reproducibility')
    parser.add_argument('--config', type=str, default=None,
                      help='Path to config.yaml (optional)')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Generate synthetic ground truth
    tracking_path = output_dir / 'synthetic_tracking.csv'
    baseline_path = output_dir / 'manual_baseline.csv'
    
    if not tracking_path.exists() or not baseline_path.exists():
        logger.info("Generating synthetic ground truth data...")
        generate_synthetic_ground_truth(
            output_dir=str(output_dir),
            n_particles=args.n_particles,
            n_frames=args.n_frames,
            seed=args.seed
        )
    else:
        logger.info("Using existing synthetic data.")
    
    # Step 2: Run verification
    logger.info("Running verification pipeline...")
    report = run_verification(
        tracking_path=str(tracking_path),
        baseline_path=str(baseline_path),
        config_path=args.config
    )
    
    # Step 3: Save verification report
    report_path = output_dir / 'energy_verification_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Verification report saved to: {report_path}")
    logger.info(f"Overall max error: {report['overall_max_error']:.2e}")
    logger.info(f"Repair needed: {report['repair_needed']}")
    
    if report['repair_needed']:
        logger.warning("Max error exceeds threshold. Re-run T018 to repair energy calculation.")
        return 1
    else:
        logger.info("Verification passed. Energy calculation is accurate.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
