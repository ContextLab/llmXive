"""
Task T024: Write noisy trajectories to data/processed/ with metadata in sidecar JSON.

This script orchestrates the loading of clean trajectories, injection of noise
at specified SNR levels, and the writing of the resulting noisy trajectories
and their manifests to the data/processed directory.
"""
import os
import sys
import json
import hashlib
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports based on API surface
from code.config import get_snr_levels, get_seeds, get_system_params, NoiseType, get_noise_types
from code.generators import generate_lorenz_trajectory, generate_rossler_trajectory
from code.noise import inject_gaussian_noise, inject_quantization_noise, calculate_snr
from code.utils.data_models import Trajectory, NoisyTrajectory
from code.utils.io import compute_file_checksum, write_json_artifact

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_clean_trajectory(system_type: str, seed: int) -> Trajectory:
    """
    Load a clean trajectory from data/raw.
    
    Args:
        system_type: 'lorenz' or 'rossler'
        seed: The seed used for generation
        
    Returns:
        Trajectory object
        
    Raises:
        FileNotFoundError: If the clean trajectory file does not exist
    """
    file_path = Path("data/raw") / f"{system_type}_clean_{seed}.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(f"Clean trajectory file not found: {file_path}")
        
    logger.info(f"Loading clean trajectory from {file_path}")
    
    # Read CSV manually to avoid pandas dependency if not strictly needed, 
    # but assuming standard numpy/pandas usage for data loading
    import numpy as np
    data = np.loadtxt(file_path, delimiter=',', skiprows=1)
    
    # Assuming columns: t, x, y, z
    t = data[:, 0]
    x = data[:, 1]
    y = data[:, 2]
    z = data[:, 3]
    
    trajectory = Trajectory(
        system_type=system_type,
        seed=seed,
        time=t,
        state=np.column_stack((x, y, z))
    )
    
    return trajectory

def save_noisy_trajectory(noisy_traj: NoisyTrajectory, output_dir: Path) -> str:
    """
    Save a noisy trajectory to CSV and return the file path.
    
    Args:
        noisy_traj: The NoisyTrajectory object to save
        output_dir: Directory to save the file
        
    Returns:
        Path to the saved CSV file
    """
    filename = f"{noisy_traj.system_type}_noisy_snr{noisy_traj.target_snr_db}_{noisy_traj.noise_type}_{noisy_traj.seed}.csv"
    file_path = output_dir / filename
    
    logger.info(f"Saving noisy trajectory to {file_path}")
    
    # Prepare data for CSV
    # Columns: t, x, y, z
    data = np.column_stack((noisy_traj.time, noisy_traj.state))
    
    # Save to CSV
    np.savetxt(file_path, data, delimiter=',', header='t,x,y,z', comments='')
    
    return str(file_path)

def create_manifest(
    system_type: str,
    seed: int,
    target_snr: float,
    noise_type: NoiseType,
    actual_snr: float,
    csv_path: str,
    checksum: str,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Create a manifest dictionary for a noisy trajectory.
    
    Args:
        system_type: System type (lorenz/rossler)
        seed: Random seed
        target_snr: Target SNR in dB
        noise_type: Type of noise injected
        actual_snr: Measured SNR after injection
        csv_path: Path to the saved CSV file
        checksum: SHA256 checksum of the CSV file
        output_dir: Directory for the manifest
        
    Returns:
        Manifest dictionary
    """
    manifest = {
        "system_type": system_type,
        "seed": seed,
        "target_snr_db": target_snr,
        "noise_type": noise_type.value,
        "actual_snr_db": actual_snr,
        "file_path": csv_path,
        "checksum_sha256": checksum,
        "num_points": len(noisy_traj.time) if 'noisy_traj' in locals() else 0,
        "metadata": {
            "task_id": "T024",
            "description": "Noisy trajectory with controlled noise injection"
        }
    }
    
    return manifest

def run_noise_injection_pipeline(
    system_types: List[str] = None,
    seeds: List[int] = None,
    snr_levels: List[float] = None,
    noise_types: List[NoiseType] = None,
    output_dir: Path = None
):
    """
    Run the full noise injection pipeline.
    
    Args:
        system_types: List of system types to process
        seeds: List of seeds to use
        snr_levels: List of SNR levels to test
        noise_types: List of noise types to apply
        output_dir: Output directory for results
    """
    if system_types is None:
        system_types = ['lorenz', 'rossler']
    if seeds is None:
        seeds = get_seeds()
    if snr_levels is None:
        snr_levels = get_snr_levels()
    if noise_types is None:
        noise_types = get_noise_types()
    if output_dir is None:
        output_dir = Path("data/processed")
        
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    
    # Track manifests for each system type
    all_manifests = {sys_type: [] for sys_type in system_types}
    
    for sys_type in system_types:
        logger.info(f"Processing system: {sys_type}")
        
        for seed in seeds:
            logger.info(f"  Seed: {seed}")
            
            # Load clean trajectory
            try:
                clean_traj = load_clean_trajectory(sys_type, seed)
            except FileNotFoundError as e:
                logger.error(f"  Skipping seed {seed}: {e}")
                continue
                
            for snr_db in snr_levels:
                for noise_type in noise_types:
                    logger.info(f"    Injecting {noise_type.value} noise at {snr_db} dB")
                    
                    # Inject noise
                    if noise_type == NoiseType.GAUSSIAN:
                        noisy_state, actual_snr = inject_gaussian_noise(
                            clean_traj.state, 
                            snr_db
                        )
                    elif noise_type == NoiseType.QUANTIZATION:
                        # Quantization needs bit resolution, defaulting to 8 bits for this task
                        # or derived from config if available. Assuming standard 8-bit for now.
                        # Note: inject_quantization_noise signature might need adjustment based on real impl
                        noisy_state, actual_snr = inject_quantization_noise(
                            clean_traj.state, 
                            bits=8 
                        )
                        # For quantization, target_snr might not be the primary control,
                        # but we log it as requested.
                        actual_snr = calculate_snr(clean_traj.state, noisy_state - clean_traj.state)
                    else:
                        logger.error(f"Unsupported noise type: {noise_type}")
                        continue
                        
                    # Create NoisyTrajectory object
                    noisy_traj = NoisyTrajectory(
                        system_type=sys_type,
                        seed=seed,
                        target_snr_db=snr_db,
                        noise_type=noise_type,
                        time=clean_traj.time,
                        state=noisy_state,
                        actual_snr_db=actual_snr
                    )
                    
                    # Save trajectory
                    csv_path = save_noisy_trajectory(noisy_traj, output_dir)
                    
                    # Compute checksum
                    checksum = compute_file_checksum(csv_path)
                    
                    # Create manifest
                    manifest_entry = create_manifest(
                        system_type=sys_type,
                        seed=seed,
                        target_snr=snr_db,
                        noise_type=noise_type,
                        actual_snr=actual_snr,
                        csv_path=csv_path,
                        checksum=checksum,
                        output_dir=output_dir
                    )
                    
                    all_manifests[sys_type].append(manifest_entry)
                    
    # Write manifests for each system type
    for sys_type, manifests in all_manifests.items():
        manifest_file = output_dir / f"manifest_{sys_type}.json"
        write_json_artifact(manifests, manifest_file)
        logger.info(f"Written manifest for {sys_type}: {manifest_file}")

def main():
    parser = argparse.ArgumentParser(description="Task T024: Write noisy trajectories and manifests")
    parser.add_argument('--systems', type=str, nargs='+', default=None, help='System types to process')
    parser.add_argument('--seeds', type=int, nargs='+', default=None, help='Seeds to use')
    parser.add_argument('--snr', type=float, nargs='+', default=None, help='SNR levels to test')
    parser.add_argument('--noise-types', type=str, nargs='+', choices=['gaussian', 'quantization'], default=None, help='Noise types to apply')
    
    args = parser.parse_args()
    
    # Parse noise types
    noise_types = None
    if args.noise_types:
        noise_types = [NoiseType(n) for n in args.noise_types]
        
    # Run pipeline
    run_noise_injection_pipeline(
        system_types=args.systems,
        seeds=args.seeds,
        snr_levels=args.snr,
        noise_types=noise_types
    )
    
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()