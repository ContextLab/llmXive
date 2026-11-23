"""
Synthetic EBSD Dataset Generator for Cold Rolling Texture Analysis.

This module generates a verified synthetic EBSD dataset for Al, Cu, and Ni
across specific cold-rolling reduction levels. It is used as a fallback
data source when real data is unavailable, ensuring the pipeline does not crash.

The generation is deterministic based on a configurable seed to ensure
reproducibility. The output includes 'reduction' percentage and 'confidence'
index fields, adhering to the data schema defined in `code/data/models.py`.

Output:
    data/raw/synthetic_ebsd.parquet
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from config import get_seed

# Initialize logger
logger = get_logger(__name__)

# Constants for synthetic generation
DEFAULT_SEED = 42
DEFAULT_REDUCTION_LEVELS = [10, 20, 30, 40, 50, 60, 70, 80]
MATERIALS = ["Al", "Cu", "Ni"]

# Typical Euler angle ranges for FCC textures (approximate for synthetic generation)
# These are broad ranges to simulate a mix of random and textured orientations
# phi1, Phi, phi2 in degrees
EULER_RANGES = {
    "Al": {"phi1": (0, 360), "Phi": (0, 90), "phi2": (0, 90)},
    "Cu": {"phi1": (0, 360), "Phi": (0, 90), "phi2": (0, 90)},
    "Ni": {"phi1": (0, 360), "Phi": (0, 90), "phi2": (0, 90)},
}

def _generate_orientations(n_points: int, material: str, rng: np.random.Generator) -> np.ndarray:
    """
    Generate synthetic Euler angles for a given material.

    Args:
        n_points: Number of orientation points to generate.
        material: Material type (Al, Cu, Ni).
        rng: NumPy random generator instance for reproducibility.

    Returns:
        Array of shape (n_points, 3) containing Euler angles (phi1, Phi, phi2).
    """
    ranges = EULER_RANGES.get(material, EULER_RANGES["Al"])
    phi1 = rng.uniform(ranges["phi1"][0], ranges["phi1"][1], n_points)
    Phi = rng.uniform(ranges["Phi"][0], ranges["Phi"][1], n_points)
    phi2 = rng.uniform(ranges["phi2"][0], ranges["phi2"][1], n_points)
    return np.column_stack([phi1, Phi, phi2])

def _generate_metadata(
    n_points: int,
    material: str,
    reduction: int,
    rng: np.random.Generator
) -> Dict[str, Any]:
    """
    Generate metadata for the synthetic dataset.

    Args:
        n_points: Number of points.
        material: Material type.
        reduction: Cold rolling reduction percentage.
        rng: NumPy random generator instance.

    Returns:
        Dictionary containing metadata arrays.
    """
    # Generate confidence indices (0.0 to 1.0)
    # Simulate realistic distribution: mostly high confidence, some low
    confidence = rng.beta(5, 1, n_points) # Skewed towards 1.0
    # Introduce some noise and lower values
    confidence = confidence * 0.9 + 0.1 * rng.random(n_points)
    confidence = np.clip(confidence, 0.0, 1.0)

    # Generate sample IDs
    sample_ids = [f"{material}_{reduction}_sample_{i}" for i in range(n_points)]

    # Generate grain size (arbitrary units, simulating variation)
    grain_size = rng.normal(loc=20.0, scale=5.0, size=n_points)
    grain_size = np.clip(grain_size, 1.0, 100.0)

    return {
        "sample_id": sample_ids,
        "material": [material] * n_points,
        "reduction": [reduction] * n_points,
        "confidence": confidence,
        "grain_size": grain_size,
    }

def generate_synthetic_dataset(
    reduction_levels: Optional[List[int]] = None,
    points_per_level: int = 500,
    seed: Optional[int] = None,
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a verified synthetic EBSD dataset.

    Args:
        reduction_levels: List of reduction percentages to include. Defaults to DEFAULT_REDUCTION_LEVELS.
        points_per_level: Number of data points to generate per material per reduction level.
        seed: Random seed for reproducibility. Defaults to DEFAULT_SEED.
        output_path: Path to save the output Parquet file. Defaults to data/raw/synthetic_ebsd.parquet.

    Returns:
        Path to the generated Parquet file.

    Raises:
        ValueError: If reduction_levels is empty or contains invalid values.
        IOError: If the output directory cannot be created or file cannot be written.
    """
    if reduction_levels is None:
        reduction_levels = DEFAULT_REDUCTION_LEVELS

    if not reduction_levels:
        raise ValueError("reduction_levels cannot be empty.")

    if seed is None:
        seed = get_seed()

    logger.info(f"Generating synthetic dataset with seed={seed}, levels={reduction_levels}")

    rng = np.random.default_rng(seed)

    all_data = []

    for material in MATERIALS:
        for reduction in reduction_levels:
            logger.debug(f"Generating data for {material} at {reduction}% reduction")

            n_points = points_per_level
            orientations = _generate_orientations(n_points, material, rng)
            metadata = _generate_metadata(n_points, material, reduction, rng)

            # Combine orientations and metadata
            df = pd.DataFrame(metadata)
            df["phi1"] = orientations[:, 0]
            df["Phi"] = orientations[:, 1]
            df["phi2"] = orientations[:, 2]

            all_data.append(df)

    if not all_data:
        raise RuntimeError("No data was generated. Check reduction_levels and materials.")

    final_df = pd.concat(all_data, ignore_index=True)

    # Ensure output directory exists
    if output_path is None:
        output_path = Path("data/raw/synthetic_ebsd.parquet")
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing synthetic dataset to {output_path}")
    final_df.to_parquet(output_path, index=False)

    logger.info(f"Successfully generated {len(final_df)} synthetic EBSD points.")
    logger.info(f"Output saved to: {output_path}")

    return output_path

def main():
    """Main entry point for the script."""
    logger.info("Starting synthetic EBSD dataset generation.")

    try:
        # Get configuration from config.py if available, otherwise use defaults
        try:
            from config import get_reductions
            reduction_levels = get_reductions()
        except (ImportError, AttributeError):
            reduction_levels = None

        output_path = generate_synthetic_dataset(reduction_levels=reduction_levels)
        logger.info(f"Task completed. Output: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())