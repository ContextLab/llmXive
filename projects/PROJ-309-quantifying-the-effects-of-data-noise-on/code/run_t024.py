"""
Task T024: Write noisy trajectories to data/processed/ with metadata in sidecar JSON.

This script orchestrates the generation of noisy trajectories from clean data
(assumed to exist in data/raw/ from T016) and writes them to data/processed/.
It creates a manifest file for each system type containing metadata about
the noise injection process.
"""
import os
import sys
import json
import hashlib
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.config import NoiseType, get_snr_levels, get_seeds, get_system_params, get_noise_types
from code.generators import generate_lorenz_trajectory, generate_rossler_trajectory, validate_trajectory
from code.noise import inject_gaussian_noise, inject_quantization_noise, calculate_snr, verify_snr_accuracy
from code.utils.io import compute_file_checksum, write_json_artifact
from code.utils.data_models import NoisyTrajectory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_clean_trajectory(system_type: str, seed: int) -> np.ndarray:
    """Load a clean trajectory from data/raw/."""
    filepath = project_root / "data" / "raw" / f"{system_type}_clean_{seed}.csv"
    if not filepath.exists():
        raise FileNotFoundError(f"Clean trajectory not found: {filepath}")
    
    # Load CSV data (assuming columns: t, x, y, z)
    data = np.loadtxt(filepath, delimiter=',', skiprows=1)
    logger.info(f"Loaded clean trajectory {system_type} seed {seed}: shape {data.shape}")
    return data

def save_noisy_trajectory(
    system_type: str, 
    seed: int, 
    snr_db: float, 
    noise_type: NoiseType,
    noisy_data: np.ndarray,
    clean_data: np.ndarray
) -> Dict[str, Any]:
    """Save a noisy trajectory and return metadata."""
    # Define output paths
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{system_type}_snr_{snr_db}dB_{noise_type.value}_seed_{seed}.csv"
    filepath = output_dir / filename
    
    # Save noisy data to CSV
    np.savetxt(filepath, noisy_data, delimiter=',', header='t,x,y,z', comments='')
    
    # Compute checksum
    checksum = compute_file_checksum(filepath)
    
    # Calculate actual SNR
    actual_snr = calculate_snr(clean_data, noisy_data)
    
    # Verify SNR accuracy
    snr_error = abs(actual_snr - snr_db)
    snr_valid = snr_error < 0.5  # ±0.5dB tolerance per T020 requirements
    
    metadata = {
        "system_type": system_type,
        "seed": seed,
        "target_snr_db": snr_db,
        "actual_snr_db": float(actual_snr),
        "snr_error_db": float(snr_error),
        "snr_valid": snr_valid,
        "noise_type": noise_type.value,
        "output_file": str(filepath.relative_to(project_root)),
        "checksum": checksum,
        "data_shape": list(noisy_data.shape),
        "timestamp": None  # Will be set by write_json_artifact if needed
    }
    
    logger.info(f"Saved noisy trajectory: {filepath.name}, actual SNR: {actual_snr:.2f}dB")
    return metadata

def run_noise_injection_pipeline(system_type: str, seed: int, snr_db: float, noise_type: NoiseType) -> Dict[str, Any]:
    """Run noise injection for a single configuration."""
    logger.info(f"Processing {system_type} seed {seed} SNR {snr_db}dB {noise_type.value}")
    
    # Load clean trajectory
    clean_data = load_clean_trajectory(system_type, seed)
    
    # Validate clean trajectory
    if not validate_trajectory(clean_data):
        raise ValueError(f"Invalid clean trajectory for {system_type} seed {seed}")
    
    # Inject noise
    if noise_type == NoiseType.GAUSSIAN:
        noisy_data = inject_gaussian_noise(clean_data, snr_db)
    elif noise_type == NoiseType.QUANTIZATION:
        # For quantization, we use a default bit depth (8-bit as per common practice)
        noisy_data = inject_quantization_noise(clean_data, bits=8)
    else:
        raise ValueError(f"Unsupported noise type: {noise_type}")
    
    # Validate noisy trajectory
    if not validate_trajectory(noisy_data):
        raise ValueError(f"Invalid noisy trajectory for {system_type} seed {seed}")
    
    # Save and return metadata
    metadata = save_noisy_trajectory(system_type, seed, snr_db, noise_type, noisy_data, clean_data)
    return metadata

def create_manifest(system_type: str, metadata_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Create a manifest file for a system type."""
    manifest = {
        "system_type": system_type,
        "generated_at": None,  # Will be set by write_json_artifact
        "total_trajectories": len(metadata_list),
        "configurations": metadata_list
    }
    return manifest

def main(args: Optional[argparse.Namespace] = None):
    """Main entry point for T024."""
    if args is None:
        parser = argparse.ArgumentParser(description="Write noisy trajectories to data/processed/")
        parser.add_argument("--system", type=str, choices=["lorenz", "rossler"], 
                          help="System type to process")
        parser.add_argument("--seed", type=int, help="Specific seed to process")
        parser.add_argument("--snr", type=float, help="Specific SNR level to process")
        parser.add_argument("--noise", type=str, choices=["gaussian", "quantization"],
                          help="Specific noise type to process")
        args = parser.parse_args()

    logger.info("Starting T024: Write noisy trajectories to data/processed/")
    
    # Determine configurations to process
    system_types = [args.system] if args.system else ["lorenz", "rossler"]
    seeds = [args.seed] if args.seed else get_seeds()
    snr_levels = [args.snr] if args.snr is not None else get_snr_levels()
    noise_types = [NoiseType(args.noise)] if args.noise else get_noise_types()
    
    manifest_data: Dict[str, List[Dict[str, Any]]] = {
        system: [] for system in system_types
    }
    
    # Process all configurations
    for system_type in system_types:
        for seed in seeds:
            for snr_db in snr_levels:
                for noise_type in noise_types:
                    try:
                        metadata = run_noise_injection_pipeline(
                            system_type, seed, snr_db, noise_type
                        )
                        manifest_data[system_type].append(metadata)
                    except Exception as e:
                        logger.error(f"Failed to process {system_type} seed {seed} SNR {snr_db}dB {noise_type.value}: {e}")
                        # Continue with other configurations
                        continue
        
        # Create and save manifest for this system type
        if manifest_data[system_type]:
            manifest = create_manifest(system_type, manifest_data[system_type])
            manifest_path = project_root / "data" / "processed" / f"manifest_{system_type}.json"
            write_json_artifact(manifest, manifest_path)
            logger.info(f"Created manifest: {manifest_path}")
        else:
            logger.warning(f"No trajectories generated for {system_type}")
    
    logger.info("T024 completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
