"""
Task T016: Write clean trajectories to data/raw/ with naming convention
{system_type}_clean_{seed}.csv and sidecar checksum file.

This script generates clean trajectories using the generators module,
saves them to CSV, and creates a sidecar JSON file containing a SHA256
checksum and generation metadata.
"""
import os
import sys
import json
import hashlib
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generators import generate_lorenz_trajectory, generate_rossler_trajectory
from config import get_seeds, get_system_params, NoiseType
from utils.io import compute_file_checksum, write_json_artifact

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_trajectory_to_csv(trajectory: Dict[str, Any], output_path: Path) -> None:
    """
    Save a trajectory dictionary to a CSV file.

    Args:
        trajectory: Dictionary containing 'time', 'x', 'y', 'z' arrays.
        output_path: Path to the output CSV file.
    """
    import csv

    logger.info(f"Saving trajectory to {output_path}")

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(['time', 'x', 'y', 'z'])
        # Write data rows
        for t, x, y, z in zip(trajectory['time'], trajectory['x'], trajectory['y'], trajectory['z']):
            writer.writerow([t, x, y, z])

    logger.info(f"Saved {len(trajectory['time'])} points to {output_path}")

def write_sidecar_checksum(
    csv_path: Path,
    system_type: str,
    seed: int,
    params: Dict[str, Any],
    output_dir: Path
) -> Path:
    """
    Write a sidecar JSON file containing the SHA256 checksum of the CSV
    and generation metadata.

    Args:
        csv_path: Path to the generated CSV file.
        system_type: Name of the dynamical system (e.g., 'lorenz', 'rossler').
        seed: Random seed used for generation.
        params: System parameters used for generation.
        output_dir: Directory to write the sidecar file.

    Returns:
        Path to the created sidecar file.
    """
    checksum = compute_file_checksum(csv_path)

    sidecar_data = {
        "file": csv_path.name,
        "checksum_algorithm": "sha256",
        "checksum": checksum,
        "system_type": system_type,
        "seed": seed,
        "parameters": params,
        "point_count": len(params.get('n_points', 0))
    }

    sidecar_path = output_dir / f"{system_type}_clean_{seed}_meta.json"

    write_json_artifact(sidecar_data, sidecar_path)
    logger.info(f"Created sidecar metadata at {sidecar_path}")

    return sidecar_path

def run_t016_pipeline() -> List[Dict[str, str]]:
    """
    Run the T016 pipeline: generate clean trajectories for all seeds and
    systems, save to data/raw/, and create sidecar checksums.

    Returns:
        List of dictionaries containing paths to generated artifacts.
    """
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    seeds = get_seeds()
    system_params = get_system_params()

    results = []

    for system_name, params in system_params.items():
        logger.info(f"Processing system: {system_name}")

        for seed in seeds:
            logger.info(f"  Generating trajectory for seed {seed}")

            # Generate trajectory based on system type
            if system_name == "lorenz":
                trajectory = generate_lorenz_trajectory(seed=seed, **params)
            elif system_name == "rossler":
                trajectory = generate_rossler_trajectory(seed=seed, **params)
            else:
                logger.error(f"Unknown system type: {system_name}")
                continue

            # Validate trajectory (basic check)
            if trajectory is None or len(trajectory['time']) == 0:
                logger.error(f"Failed to generate valid trajectory for {system_name}, seed {seed}")
                continue

            # Define output paths
            csv_filename = f"{system_name}_clean_{seed}.csv"
            csv_path = output_dir / csv_filename

            # Save CSV
            save_trajectory_to_csv(trajectory, csv_path)

            # Write sidecar checksum
            sidecar_path = write_sidecar_checksum(
                csv_path=csv_path,
                system_type=system_name,
                seed=seed,
                params=params,
                output_dir=output_dir
            )

            results.append({
                "system": system_name,
                "seed": seed,
                "csv_path": str(csv_path),
                "sidecar_path": str(sidecar_path)
            })

            logger.info(f"  Completed: {csv_filename}")

    return results

def main():
    """Main entry point for T016."""
    parser = argparse.ArgumentParser(description="Task T016: Write clean trajectories to data/raw/")
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Starting T016 pipeline")
    results = run_t016_pipeline()
    logger.info(f"Completed T016 pipeline. Generated {len(results)} artifacts.")

    # Print summary
    for r in results:
        print(f"  {r['system']} (seed={r['seed']}): {r['csv_path']}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
