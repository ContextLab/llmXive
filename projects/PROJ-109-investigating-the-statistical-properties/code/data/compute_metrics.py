import os
import logging
import json
import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import curve_fit
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import get_rho_critical_at_z, get_simulation_box_size
from utils.logging import get_logger
from data.streaming import subsample_particles

logger = get_logger(__name__)

# Constants for NFW fitting
G = 4.302e-6  # (km/s)^2 kpc/Msun
Mpc_to_kpc = 1000.0

def nfw_profile(r, rs, rho_s):
    """
    NFW density profile function.
    r: radius in kpc
    rs: scale radius in kpc
    rho_s: characteristic density in Msun/kpc^3
    """
    x = r / rs
    # Avoid division by zero
    x = np.where(x == 0, 1e-10, x)
    return rho_s / (x * (1 + x)**2)

def calculate_local_overdensity(positions, box_size: float, rho_critical: float) -> np.ndarray:
    """
    Calculate local overdensity for each halo using cKDTree with periodic boundaries.
    Uses a spherical top-hat of 5 Mpc h^-1 radius.
    """
    R_TOP_HAT = 5.0  # Mpc h^-1
    # Convert to kpc for consistency if needed, but assuming positions are in kpc
    # If positions are in Mpc, convert R_TOP_HAT to kpc
    R_TOP_HAT_kpc = R_TOP_HAT * Mpc_to_kpc

    overdensities = []
    tree = cKDTree(positions, boxsize=box_size)

    for i, pos in enumerate(positions):
        # Find neighbors within R_TOP_HAT
        neighbors = tree.query_ball_point(pos, R_TOP_HAT_kpc)
        # Exclude self
        neighbors = [n for n in neighbors if n != i]
        
        if len(neighbors) == 0:
            # If no neighbors, assume background density
            delta = 0.0
        else:
            # Calculate local density
            # Volume of sphere
            volume = (4.0/3.0) * np.pi * (R_TOP_HAT_kpc**3)
            # Assume unit mass for simplicity or use actual masses if available
            # For now, assume 1 Msun per particle for counting
            local_density = len(neighbors) / volume
            delta = (local_density / rho_critical) - 1.0
        
        overdensities.append(delta)
    
    return np.array(overdensities)

def compute_shape_from_inertia_tensor(positions: np.ndarray, masses: np.ndarray) -> float:
    """
    Compute shape parameter s = c/a from inertia tensor.
    positions: Nx3 array of particle positions
    masses: Nx1 array of particle masses
    Returns: s (c/a ratio), where 0 < s <= 1
    """
    if len(positions) < 3:
        raise ValueError("Need at least 3 particles to compute inertia tensor")
    
    # Center positions
    center = np.average(positions, axis=0, weights=masses)
    centered_positions = positions - center
    
    # Compute inertia tensor
    # I_ij = sum_k m_k (r_k^2 delta_ij - r_ki r_kj)
    I = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            if i == j:
                I[i, j] = np.sum(masses * np.sum(centered_positions**2, axis=1) - masses * centered_positions[:, i]**2)
            else:
                I[i, j] = -np.sum(masses * centered_positions[:, i] * centered_positions[:, j])
    
    # Eigenvalues
    eigenvalues = np.linalg.eigvalsh(I)
    eigenvalues = np.sort(eigenvalues)
    
    # s = c/a, where c is smallest axis, a is largest
    # Inertia tensor eigenvalues are proportional to a^2+b^2, a^2+c^2, b^2+c^2
    # For a triaxial ellipsoid, we can approximate axes lengths from eigenvalues
    # Simplified approach: s = min(eigenvalues) / max(eigenvalues)
    # This is a rough approximation; more sophisticated methods exist
    if eigenvalues[-1] == 0:
        return 1.0
    
    s = eigenvalues[0] / eigenvalues[-1]
    # Ensure s is in valid range [0, 1]
    s = np.clip(s, 0.0, 1.0)
    
    return s

def compute_spin_parameter(positions: np.ndarray, velocities: np.ndarray, masses: np.ndarray, halo_radius: float) -> float:
    """
    Compute spin parameter lambda using subsampled Plummer-softened potential.
    Implements a subsample of N=500 particles to approximate total energy E.
    """
    N_SUBSAMPLE = 500
    n_particles = len(positions)
    
    if n_particles == 0:
        raise ValueError("No particles to compute spin parameter")
    
    # Subsample particles
    if n_particles > N_SUBSAMPLE:
        indices = np.random.choice(n_particles, N_SUBSAMPLE, replace=False)
        pos_sub = positions[indices]
        vel_sub = velocities[indices]
        mass_sub = masses[indices]
    else:
        pos_sub = positions
        vel_sub = velocities
        mass_sub = masses
    
    n_sub = len(pos_sub)
    
    # Calculate angular momentum J
    # J = sum_i m_i (r_i x v_i)
    center_pos = np.average(pos_sub, axis=0, weights=mass_sub)
    center_vel = np.average(vel_sub, axis=0, weights=mass_sub)
    
    r_rel = pos_sub - center_pos
    v_rel = vel_sub - center_vel
    
    J_vec = np.zeros(3)
    for i in range(n_sub):
        J_vec += mass_sub[i] * np.cross(r_rel[i], v_rel[i])
    
    J = np.linalg.norm(J_vec)
    
    # Calculate kinetic energy E_kin
    E_kin = 0.5 * np.sum(mass_sub * np.sum(vel_rel**2, axis=1))
    
    # Calculate potential energy E_pot using Plummer-softened formula
    # E_pot = -G * sum_i sum_j (m_i * m_j) / sqrt(r_ij^2 + epsilon^2)
    epsilon = 0.01 * halo_radius  # Softening length
    
    E_pot = 0.0
    for i in range(n_sub):
        for j in range(i+1, n_sub):
            r_ij = np.linalg.norm(pos_sub[i] - pos_sub[j])
            E_pot -= G * mass_sub[i] * mass_sub[j] / np.sqrt(r_ij**2 + epsilon**2)
    
    E_pot *= 2.0  # Account for double counting
    
    # Total energy
    E = E_kin + E_pot
    
    if E == 0:
        return 0.0
    
    # Total mass
    M = np.sum(mass_sub)
    
    # Spin parameter lambda = J * |E|^(1/2) / (G * M^(5/2))
    lambda_param = J * np.sqrt(np.abs(E)) / (G * (M ** 2.5))
    
    return lambda_param

def compute_concentration_from_nfw_fit(r: np.ndarray, density: np.ndarray, r_max: float) -> Tuple[Optional[float], bool]:
    """
    Fit NFW profile to density data and return concentration c = r_vir / rs.
    Returns (concentration, success_flag)
    """
    if len(r) < 3:
        return None, False
    
    # Initial guesses
    rs_guess = r_max / 10.0
    rho_s_guess = np.max(density)
    
    try:
        popt, pcov = curve_fit(
            nfw_profile, 
            r, 
            density, 
            p0=[rs_guess, rho_s_guess],
            bounds=([1e-3, 1e-10], [r_max, 1e20]),
            maxfev=5000
        )
        
        rs_fit = popt[0]
        # Concentration c = r_vir / rs
        # Assuming r_vir is approximately r_max for this fit
        c = r_max / rs_fit
        
        # Check if fit is reasonable
        if c <= 0 or c > 100:
            return None, False
        
        return c, True
    except Exception as e:
        logger.warning(f"NFW fit failed: {e}")
        return None, False

def compute_halo_metrics(halo_data: Dict[str, Any], box_size: float, rho_critical: float) -> Dict[str, Any]:
    """
    Compute all structural metrics for a single halo.
    Returns dictionary with shape, spin, concentration, and fit success status.
    """
    positions = halo_data['particle_positions']
    velocities = halo_data.get('particle_velocities', np.zeros_like(positions))
    masses = halo_data.get('particle_masses', np.ones(len(positions)))
    
    # Calculate halo radius (approximate as radius containing 50% of mass)
    # Simplified: use max distance from center
    center = np.average(positions, axis=0, weights=masses)
    distances = np.linalg.norm(positions - center, axis=1)
    halo_radius = np.max(distances)
    
    metrics = {}
    
    # Shape
    try:
        metrics['shape'] = compute_shape_from_inertia_tensor(positions, masses)
    except Exception as e:
        logger.warning(f"Shape calculation failed: {e}")
        metrics['shape'] = None
    
    # Spin
    try:
        metrics['spin'] = compute_spin_parameter(positions, velocities, masses, halo_radius)
    except Exception as e:
        logger.warning(f"Spin calculation failed: {e}")
        metrics['spin'] = None
    
    # Concentration (requires radial density profile)
    # For this implementation, we assume radial bins are provided or calculated
    # Simplified: return None if not enough data
    if 'radial_bins' in halo_data and 'density_profile' in halo_data:
        r = halo_data['radial_bins']
        density = halo_data['density_profile']
        c, success = compute_concentration_from_nfw_fit(r, density, halo_radius)
        metrics['concentration'] = c
        metrics['nfw_fit_success'] = success
    else:
        metrics['concentration'] = None
        metrics['nfw_fit_success'] = False
    
    return metrics

def run_compute_metrics_pipeline(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run the full metrics computation pipeline on a dataset.
    Tracks convergence rates and failed fits, saving results to JSON.
    """
    logger.info(f"Starting metrics computation pipeline for {input_path}")
    
    # Load data (assuming parquet format from T014)
    import pandas as pd
    df = pd.read_parquet(input_path)
    
    # Initialize counters for convergence tracking
    total_halos = 0
    successful_fits = 0
    failed_fits = 0
    
    results = []
    
    # Process each halo
    for idx, row in df.iterrows():
        total_halos += 1
        
        # Reconstruct halo data from row
        # This assumes the parquet file contains the necessary columns
        # In a real implementation, this would be more complex
        halo_data = {
            'particle_positions': row.get('particle_positions', None),
            'particle_velocities': row.get('particle_velocities', None),
            'particle_masses': row.get('particle_masses', None)
        }
        
        if halo_data['particle_positions'] is None:
            logger.warning(f"Halo {idx} missing positions, skipping")
            failed_fits += 1
            continue
        
        metrics = compute_halo_metrics(
            halo_data, 
            get_simulation_box_size(), 
            get_rho_critical_at_z(0.0)
        )
        
        # Track NFW fit success
        if metrics.get('nfw_fit_success', False):
            successful_fits += 1
        else:
            failed_fits += 1
        
        results.append({
            'halo_id': idx,
            'shape': metrics.get('shape'),
            'spin': metrics.get('spin'),
            'concentration': metrics.get('concentration'),
            'nfw_fit_success': metrics.get('nfw_fit_success', False)
        })
    
    # Calculate convergence statistics
    if total_halos > 0:
        success_rate = (successful_fits / total_halos) * 100
        failure_rate = (failed_fits / total_halos) * 100
    else:
        success_rate = 0.0
        failure_rate = 0.0
    
    convergence_message = f"CONVERGENCE: {success_rate:.1f}% success, {failed_fits} failed fits"
    logger.info(convergence_message)
    
    # Save convergence stats to JSON
    convergence_stats = {
        'total_halos': total_halos,
        'successful_fits': successful_fits,
        'failed_fits': failed_fits,
        'success_rate_percent': success_rate,
        'failure_rate_percent': failure_rate,
        'message': convergence_message
    }
    
    # Ensure results directory exists
    results_dir = Path(output_path).parent
    results_dir.mkdir(parents=True, exist_ok=True)
    
    stats_path = results_dir / 'convergence_stats.json'
    with open(stats_path, 'w') as f:
        json.dump(convergence_stats, f, indent=2)
    
    logger.info(f"Convergence stats saved to {stats_path}")
    
    # Save detailed results
    results_df = pd.DataFrame(results)
    results_df.to_parquet(output_path, index=False)
    
    logger.info(f"Metrics computation pipeline completed. Results saved to {output_path}")
    
    return convergence_stats

# Main entry point for direct execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Compute halo structural metrics")
    parser.add_argument("--input", type=str, required=True, help="Input parquet file path")
    parser.add_argument("--output", type=str, required=True, help="Output parquet file path")
    
    args = parser.parse_args()
    
    run_compute_metrics_pipeline(args.input, args.output)
