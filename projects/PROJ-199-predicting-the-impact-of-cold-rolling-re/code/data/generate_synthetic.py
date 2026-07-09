"""
Synthetic EBSD Data Generator (Fallback Mechanism).

This module generates synthetic EBSD datasets for FCC metals (Al, Cu, Ni)
as a fallback when real data download fails. It strictly reads reduction
levels from `code/config.py` and raises a `ConfigurationError` if they are missing.

Usage:
    python code/data/generate_synthetic.py
"""
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_reductions, get_seed, ConfigurationError
from data.models import MaterialType, Symmetry
from utils.logging import get_logger

logger = get_logger(__name__)

# Constants for FCC metals
# Approximate lattice parameters (Angstroms) - used for simulation logic if needed
LATTICE_PARAMS = {
    "Al": 4.05,
    "Cu": 3.61,
    "Ni": 3.52
}

# Euler angle ranges for typical FCC texture components (Bunge notation)
# These are used to bias the synthetic data towards realistic textures
TEXTURE_COMPONENTS = {
    "Copper": {"phi1": (35, 45), "Phi": (35, 45), "phi2": (35, 45)},
    "Brass": {"phi1": (25, 35), "Phi": (35, 45), "phi2": (40, 55)},
    "S": {"phi1": (35, 45), "Phi": (35, 45), "phi2": (35, 45)},
    "Goss": {"phi1": (0, 10), "Phi": (40, 50), "phi2": (40, 50)},
    "Cube": {"phi1": (0, 10), "Phi": (0, 10), "phi2": (0, 10)}
}

def _generate_euler_angles(n_points: int, material: str, reduction: int, seed: int) -> np.ndarray:
    """
    Generates synthetic Euler angles biased towards FCC rolling textures.

    The bias increases with reduction level to simulate texture evolution.
    """
    rng = np.random.default_rng(seed)

    # Base random distribution (random orientation)
    phi1 = rng.uniform(0, 360, n_points)
    Phi = rng.uniform(0, 90, n_points)
    phi2 = rng.uniform(0, 90, n_points)

    # Determine texture intensity based on reduction level
    # Higher reduction -> stronger texture (less random)
    intensity_factor = min(0.8, reduction / 100.0)

    # Select a dominant component based on material and reduction
    # Simplified physics model:
    # Al: Copper -> S -> Brass
    # Cu: Copper -> S
    # Ni: Copper -> S
    dominant_component = "Copper"
    if reduction > 60 and material == "Al":
        dominant_component = "Brass"

    comp = TEXTURE_COMPONENTS[dominant_component]
    
    # Create biased distribution
    # We blend random with a Gaussian centered on the component
    for i, (key, (low, high)) in enumerate(comp.items()):
        center = (low + high) / 2.0
        width = (high - low) / 4.0
        
        if key == "phi1":
            target = phi1
        elif key == "Phi":
            target = Phi
        else:
            target = phi2

        # Generate component-oriented angles
        component_angles = rng.normal(center, width, n_points)
        
        # Blend with random
        mask = rng.random(n_points) < intensity_factor
        target[mask] = component_angles[mask]

    return np.column_stack((phi1, Phi, phi2))

def _generate_confidence_indices(n_points: int, seed: int) -> np.ndarray:
    """
    Generates confidence indices.
    Most points have high confidence (> 0.9), with a tail of lower confidence.
    """
    rng = np.random.default_rng(seed + 1)
    # Beta distribution to skew towards 1.0
    conf = rng.beta(5, 1, n_points)
    # Ensure minimum threshold for "valid" data simulation, but allow some noise
    return np.clip(conf, 0.05, 1.0)

def generate_synthetic_dataset(
    materials: List[str] = ["Al", "Cu", "Ni"],
    output_dir: Path = None
) -> None:
    """
    Generates the full synthetic EBSD dataset.

    Args:
        materials: List of material symbols to generate.
        output_dir: Directory to save the output Parquet file. Defaults to data/processed.
    """
    if output_dir is None:
        output_dir = PROJECT_ROOT / "data" / "processed"
    
    output_dir.mkdir(parents=True, exist_ok=True)

    # CRITICAL: Read reduction levels from config
    try:
        reductions = get_reductions()
    except ConfigurationError as e:
        logger.critical(f"Configuration Error: {e}")
        raise
    
    if not reductions:
        raise ConfigurationError("No reduction levels configured. Cannot generate synthetic data.")

    seed = get_seed()
    logger.info(f"Generating synthetic data for materials: {materials}, reductions: {reductions}, seed: {seed}")

    all_records = []

    for material in materials:
        for reduction in reductions:
            # Determine sample size (simulate EBSD scan size)
            # Typical scan might be 100x100 points
            n_points = 10000 
            
            # Generate Euler angles
            eulers = _generate_euler_angles(n_points, material, reduction, seed)
            
            # Generate confidence indices
            conf_indices = _generate_confidence_indices(n_points, seed)
            
            # Generate grain IDs (simplified: 100 grains)
            rng = np.random.default_rng(seed + 2)
            grain_ids = rng.integers(0, 100, n_points)

            for i in range(n_points):
                record = {
                    "sample_id": f"{material}_{reduction}pct_synthetic",
                    "material": material,
                    "reduction": reduction,
                    "phi1": eulers[i, 0],
                    "Phi": eulers[i, 1],
                    "phi2": eulers[i, 2],
                    "confidence_index": conf_indices[i],
                    "grain_id": int(grain_ids[i]),
                    "is_synthetic": True
                }
                all_records.append(record)

    # Create DataFrame
    df = pd.DataFrame(all_records)
    
    # Save to Parquet
    output_path = output_dir / "synthetic_ebsd_fallback.parquet"
    df.to_parquet(output_path, index=False)
    
    logger.info(f"Successfully generated synthetic dataset: {output_path}")
    logger.info(f"Total records: {len(df)}")
    logger.info(f"Materials: {materials}, Reductions: {reductions}")

def main():
    """Entry point for script execution."""
    try:
        generate_synthetic_dataset()
        logger.info("Synthetic data generation completed successfully.")
    except ConfigurationError as e:
        logger.error(f"Failed to generate synthetic data due to configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during synthetic data generation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
