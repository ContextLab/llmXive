import os
import logging
import json
import numpy as np
from scipy.spatial import cKDTree
from scipy.optimize import curve_fit
from pathlib import Path
from typing import Dict, Any, Optional, Generator, Tuple, List

from utils.logging import get_logger
from config import BOX_SIZE, RHO_CRITICAL, BULLOCK_C200, BULLOCK_ALPHA

# Configure logger
logger = get_logger(__name__)

# Constants for NFW fitting
G = 4.302e-6  # kpc km^2 s^-2 Msol^-1

def nfw_profile(r, rs, vrs):
    """
    NFW profile function for fitting.
    r: radius
    rs: scale radius
    vrs: velocity scale at rs
    """
    x = r / rs
    return vrs / (x * (1 + x)**2)

def calculate_local_overdensity(positions: np.ndarray, particle_masses: np.ndarray, 
                                center: Optional[np.ndarray] = None) -> Dict[str, float]:
    """
    Calculate local overdensity using cKDTree with periodic boundary wrapping.
    """
    if center is None:
        center = np.mean(positions, axis=0)
    
    # Wrap positions relative to center
    wrapped_positions = (positions - center + BOX_SIZE/2) % BOX_SIZE - BOX_SIZE/2
    
    tree = cKDTree(wrapped_positions, boxsize=BOX_SIZE)
    
    # Find neighbors within 5 Mpc/h
    radius = 5.0
    indices = tree.query_ball_point(np.zeros(3), radius)
    
    total_mass = 0.0
    for idx in indices:
        total_mass += particle_masses[idx]
    
    volume = (4.0/3.0) * np.pi * (radius**3)
    local_density = total_mass / volume
    overdensity = local_density / RHO_CRITICAL
    
    return {"overdensity": overdensity, "local_density": local_density}

def compute_shape_from_inertia_tensor(particle_positions: np.ndarray, 
                                      particle_masses: np.ndarray) -> float:
    """
    Compute shape parameter s = c/a from inertia tensor.
    """
    if len(particle_positions) < 3:
        raise ValueError("Need at least 3 particles to compute inertia tensor")
    
    # Center the positions
    center = np.average(particle_positions, axis=0, weights=particle_masses)
    centered_positions = particle_positions - center
    
    # Compute inertia tensor
    I = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            sum_term = 0.0
            for k, pos in enumerate(centered_positions):
                sum_term += particle_masses[k] * pos[i] * pos[j]
            I[i, j] = sum_term
    
    # Eigenvalues
    eigenvalues = np.linalg.eigvalsh(I)
    eigenvalues = np.sort(eigenvalues)
    
    # s = c/a (smallest / largest)
    if eigenvalues[-1] == 0:
        return 0.0
    
    s = eigenvalues[0] / eigenvalues[-1]
    return float(np.clip(s, 0.0, 1.0))

def compute_spin_parameter(particle_positions: np.ndarray, 
                           particle_masses: np.ndarray,
                           particle_velocities: np.ndarray) -> float:
    """
    Compute spin parameter λ using subsampled Plummer-softened potential.
    """
    n_particles = len(particle_positions)
    if n_particles == 0:
        raise ValueError("No particles to compute spin parameter")
    
    # Subsample if necessary
    n_sample = min(500, n_particles)
    indices = np.random.choice(n_particles, size=n_sample, replace=False)
    
    pos = particle_positions[indices]
    mass = particle_masses[indices]
    vel = particle_velocities[indices]
    
    # Center of mass
    center_mass = np.average(pos, axis=0, weights=mass)
    pos_centered = pos - center_mass
    
    # Total mass
    M = np.sum(mass)
    
    # Angular momentum J
    J = 0.0
    for i in range(n_sample):
        r = pos_centered[i]
        v = vel[i]
        J += mass[i] * np.linalg.norm(np.cross(r, v))
    
    # Kinetic energy
    E_kin = 0.5 * np.sum(mass * np.sum(vel**2, axis=1))
    
    # Potential energy (subsampled Plummer)
    epsilon = 0.01 * np.std(np.linalg.norm(pos_centered, axis=1))
    E_pot = 0.0
    for i in range(n_sample):
        for j in range(i+1, n_sample):
            r_ij = np.linalg.norm(pos_centered[i] - pos_centered[j])
            E_pot -= G * mass[i] * mass[j] / np.sqrt(r_ij**2 + epsilon**2)
    
    E_total = E_kin + E_pot
    
    if E_total == 0:
        return 0.0
    
    # Spin parameter
    lambda_val = J * np.sqrt(np.abs(E_total)) / (G * M**2.5)
    return float(np.clip(lambda_val, 0.0, 1.0))

def compute_concentration_from_nfw_fit(radii: np.ndarray, 
                                       density_profile: np.ndarray) -> Optional[float]:
    """
    Fit NFW profile and return concentration parameter.
    """
    if len(radii) < 3:
        return None
    
    # Filter out zero or negative radii
    valid = (radii > 0) & (density_profile > 0)
    if np.sum(valid) < 3:
        return None
    
    r_fit = radii[valid]
    rho_fit = density_profile[valid]
    
    try:
        # Initial guess for rs and vrs
        p0 = [0.5 * np.median(r_fit), np.median(rho_fit)]
        
        bounds = ([1e-3, 1e-3], [100.0, 1e6])
        
        popt, pcov = curve_fit(nfw_profile, r_fit, rho_fit, p0=p0, bounds=bounds, maxfev=5000)
        
        rs = popt[0]
        # Concentration c = R_vir / rs (assume R_vir ~ 1.0 for normalized units)
        c = 1.0 / rs if rs > 0 else None
        
        return float(c) if c is not None and c > 0 else None
    except Exception as e:
        logger.warning(f"NFW fit failed: {e}")
        return None

def compute_halo_metrics(halo_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute all structural metrics for a single halo.
    """
    results = {
        "halo_id": halo_data.get("halo_id", "unknown"),
        "shape": None,
        "spin": None,
        "concentration": None,
        "overdensity": None,
        "fit_success": False
    }
    
    try:
        positions = halo_data.get("particle_positions")
        masses = halo_data.get("particle_masses")
        velocities = halo_data.get("particle_velocities")
        
        if positions is None or masses is None:
            logger.warning(f"Missing particle data for halo {results['halo_id']}")
            return results
        
        # Shape
        results["shape"] = compute_shape_from_inertia_tensor(positions, masses)
        
        # Spin
        if velocities is not None:
            results["spin"] = compute_spin_parameter(positions, masses, velocities)
        
        # Overdensity
        center = np.average(positions, axis=0, weights=masses)
        overdensity_result = calculate_local_overdensity(positions, masses, center)
        results["overdensity"] = overdensity_result["overdensity"]
        
        # Concentration (NFW fit)
        if "radii" in halo_data and "density_profile" in halo_data:
            c = compute_concentration_from_nfw_fit(
                halo_data["radii"], 
                halo_data["density_profile"]
            )
            results["concentration"] = c
            results["fit_success"] = (c is not None)
        
    except Exception as e:
        logger.error(f"Error computing metrics for halo {results['halo_id']}: {e}")
    
    return results

def run_compute_metrics_pipeline(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main pipeline to compute metrics for all halos in input file.
    Logs convergence statistics and saves to results/convergence_stats.json.
    """
    logger.info(f"Starting metrics computation pipeline for {input_path}")
    
    # Ensure results directory exists
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    stats_path = results_dir / "convergence_stats.json"
    
    total_halos = 0
    successful_fits = 0
    failed_fits = 0
    
    # Process input (assuming parquet or similar structured format)
    try:
        import pandas as pd
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to read input file {input_path}: {e}")
        raise
    
    metrics_results = []
    
    for idx, row in df.iterrows():
        total_halos += 1
        
        # Construct halo data dict
        halo_data = {
            "halo_id": row.get("halo_id", idx),
            "particle_positions": row.get("particle_positions"),
            "particle_masses": row.get("particle_masses"),
            "particle_velocities": row.get("particle_velocities"),
            "radii": row.get("radii"),
            "density_profile": row.get("density_profile")
        }
        
        metrics = compute_halo_metrics(halo_data)
        metrics_results.append(metrics)
        
        if metrics["fit_success"]:
            successful_fits += 1
        else:
            failed_fits += 1
        
        # Log every 1000 halos
        if total_halos % 1000 == 0:
            logger.info(f"Processed {total_halos} halos...")
    
    # Calculate and log convergence stats
    success_rate = (successful_fits / total_halos * 100) if total_halos > 0 else 0.0
    logger.info(f"CONVERGENCE: {success_rate:.2f}% success, {failed_fits} failed fits")
    
    # Save stats to JSON
    stats = {
        "total_halos": total_halos,
        "successful_fits": successful_fits,
        "failed_fits": failed_fits,
        "success_rate_percent": round(success_rate, 2)
    }
    
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Convergence stats saved to {stats_path}")
    
    # Save full metrics results
    try:
        metrics_df = pd.DataFrame(metrics_results)
        metrics_df.to_parquet(output_path, index=False)
        logger.info(f"Metrics saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")
        raise
    
    return stats

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python compute_metrics.py <input_parquet> <output_parquet>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    run_compute_metrics_pipeline(input_file, output_file)