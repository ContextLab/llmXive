import os
import random
import zipfile
import csv
from pathlib import Path
import numpy as np

from logger import get_logger
from utils import calculate_metrics

logger = get_logger(__name__)

def set_seeds(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds set to {seed}")

def generate_xyz_content(pair_id: int, seed_offset: int = 0) -> str:
    """
    Generate a synthetic XYZ file content for an ion pair.
    The coordinates are deterministic based on pair_id and seed_offset.
    Format:
    N
    Comment line
    Element x y z
    ...
    """
    # Use a deterministic seed based on pair_id to ensure reproducibility
    local_seed = 42 + pair_id * 1000 + seed_offset
    rng = np.random.default_rng(local_seed)

    # Simulate a small ion pair: Cation (e.g., 3 atoms) + Anion (e.g., 3 atoms)
    # Total 6 atoms
    num_atoms = 6
    elements = ["C", "H", "N", "B", "F", "O"]
    
    lines = [str(num_atoms)]
    lines.append(f"Ion Pair {pair_id} - Synthetic XYZ")
    
    for i in range(num_atoms):
        # Generate coordinates within a reasonable box (Angstroms)
        x = rng.uniform(-2.0, 2.0)
        y = rng.uniform(-2.0, 2.0)
        z = rng.uniform(-2.0, 2.0)
        elem = elements[i % len(elements)]
        lines.append(f"{elem} {x:.6f} {y:.6f} {z:.6f}")
    
    return "\n".join(lines) + "\n"

def generate_reference_energy(pair_id: int, seed_offset: int = 0) -> float:
    """
    Generate a synthetic CCSD(T)/CBS reference energy (in Hartree).
    Typical interaction energies for ILs are -0.3 to -0.6 Hartree.
    """
    local_seed = 42 + pair_id * 1000 + seed_offset + 1
    rng = np.random.default_rng(local_seed)
    
    # Base energy around -0.45 Hartree with some variance
    base_energy = -0.45
    variance = rng.uniform(-0.05, 0.05)
    return base_energy + variance

def generate_bulk_properties(pair_id: int, seed_offset: int = 0) -> dict:
    """
    Generate synthetic density (g/cm3) and viscosity (cP) for an ion pair.
    Density: 1.1 - 1.6 g/cm3
    Viscosity: 10 - 500 cP (highly variable for ILs)
    """
    local_seed = 42 + pair_id * 1000 + seed_offset + 2
    rng = np.random.default_rng(local_seed)
    
    density = rng.uniform(1.1, 1.6)
    # Viscosity often follows a log-normal distribution roughly
    log_visc = rng.normal(4.0, 1.0) # mean ~4, std ~1
    viscosity = np.exp(log_visc)
    
    return {
        "pair_id": pair_id,
        "density": density,
        "viscosity": viscosity
    }

def main():
    """
    Generate the synthetic local fallback data required for CI.
    Creates:
    1. data/IL-Benchmark-local.zip containing 20 XYZ files
    2. data/experimental_bulk_properties.csv with 20 rows
    """
    set_seeds(42)
    
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    num_pairs = 20
    zip_path = data_dir / "IL-Benchmark-local.zip"
    csv_path = data_dir / "experimental_bulk_properties.csv"
    
    logger.info(f"Generating synthetic data for {num_pairs} ion pairs...")
    
    # Prepare CSV data
    csv_data = []
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for i in range(num_pairs):
            # Generate XYZ
            xyz_content = generate_xyz_content(i)
            xyz_filename = f"pair_{i:03d}.xyz"
            zipf.writestr(xyz_filename, xyz_content)
            
            # Generate Reference Energy (store in a metadata file or just rely on known generation logic)
            # For this task, we store the reference energy in a separate metadata JSON inside the zip
            # to ensure the loader can retrieve it without re-generating.
            ref_energy = generate_reference_energy(i)
            meta_filename = f"pair_{i:03d}_meta.json"
            meta_content = f'{{"pair_id": {i}, "reference_energy": {ref_energy}}}'
            zipf.writestr(meta_filename, meta_content)
            
            # Generate Bulk Properties
            props = generate_bulk_properties(i)
            csv_data.append(props)
    
    # Write CSV
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["pair_id", "density", "viscosity"])
        writer.writeheader()
        writer.writerows(csv_data)
    
    logger.info(f"Generated {zip_path}")
    logger.info(f"Generated {csv_path}")
    logger.info("Synthetic data generation complete.")

if __name__ == "__main__":
    main()
