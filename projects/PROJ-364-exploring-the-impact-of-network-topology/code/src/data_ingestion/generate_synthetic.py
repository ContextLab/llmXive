"""
Synthetic Data Generator for Validation Only.

This module generates seeded, versioned, and checksummed synthetic datasets
strictly for pipeline validation (T017). It is explicitly NOT for scientific
hypothesis testing.

Per Plan Section 5 and Constitution III:
- All outputs must be deterministic given a seed.
- A checksum manifest must be generated for auditability.
- A specific warning must be logged to indicate synthetic data usage.
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd

from src.logging_config import get_data_ingestion_logger
from src.utils.checksum import compute_file_sha256, generate_checksum_manifest, load_checksum_manifest

# Constants
SYNTHETIC_VERSION = "1.0.0"
SYNTHETIC_WARNING_LOG = "results/synthetic_warning.log"

def _get_logger() -> logging.Logger:
    """Get the data ingestion logger."""
    return get_data_ingestion_logger()

def _generate_defect_coordinates(
    n_samples: int,
    grid_size: int,
    n_defects_per_sample: int,
    seed: int
) -> List[pd.DataFrame]:
    """
    Generate deterministic synthetic defect coordinates.

    Args:
        n_samples: Number of samples to generate.
        grid_size: Size of the 2D grid (e.g., 500x500).
        n_defects_per_sample: Number of defects per sample.
        seed: Random seed for reproducibility.

    Returns:
        List of DataFrames, each containing 'x', 'y', 'sample_id'.
    """
    logger = _get_logger()
    logger.info(f"Generating {n_samples} synthetic samples with {n_defects_per_sample} defects each.")

    rng = np.random.default_rng(seed)
    samples = []

    for i in range(n_samples):
        sample_id = f"synthetic_{i:04d}"
        # Uniform distribution on [0, grid_size)
        coords = rng.uniform(0, grid_size, size=(n_defects_per_sample, 2))
        df = pd.DataFrame(coords, columns=['x', 'y'])
        df['sample_id'] = sample_id
        samples.append(df)

    return samples

def _create_metadata(
    n_samples: int,
    grid_size: int,
    n_defects_per_sample: int,
    seed: int,
    version: str
) -> Dict[str, Any]:
    """Create metadata dictionary for the synthetic dataset."""
    return {
        "dataset_type": "synthetic",
        "version": version,
        "generation_seed": seed,
        "parameters": {
            "n_samples": n_samples,
            "grid_size": grid_size,
            "n_defects_per_sample": n_defects_per_sample
        },
        "generated_at": "validation_mode",
        "note": "This data is synthetic and MUST NOT be used for scientific hypothesis testing."
    }

def generate_synthetic_dataset(
    output_dir: str,
    n_samples: int = 10,
    grid_size: int = 500,
    n_defects_per_sample: int = 100,
    seed: int = 42
) -> Dict[str, str]:
    """
    Generate a synthetic dataset for validation purposes.

    This function creates:
    1. A CSV file with all defect coordinates.
    2. A JSON metadata file.
    3. A checksum manifest file.
    4. A warning log entry.

    Args:
        output_dir: Directory to save the generated files.
        n_samples: Number of samples to generate.
        grid_size: Grid size for coordinates.
        n_defects_per_sample: Defects per sample.
        seed: Random seed.

    Returns:
        Dictionary mapping file types to their relative paths.
    """
    logger = _get_logger()
    logger.warning("=== SYNTHETIC DATA GENERATION MODE ===")
    logger.warning("This dataset is generated for pipeline validation ONLY.")
    logger.warning("Do not use for scientific hypothesis testing.")

    # Ensure output directory exists
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Generate coordinates
    samples = _generate_defect_coordinates(n_samples, grid_size, n_defects_per_sample, seed)
    combined_df = pd.concat(samples, ignore_index=True)

    # Save CSV
    csv_filename = "synthetic_defects.csv"
    csv_path = out_path / csv_filename
    combined_df.to_csv(csv_path, index=False)
    logger.info(f"Saved synthetic coordinates to {csv_path}")

    # Save Metadata
    metadata = _create_metadata(n_samples, grid_size, n_defects_per_sample, seed, SYNTHETIC_VERSION)
    meta_filename = "synthetic_metadata.json"
    meta_path = out_path / meta_filename
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved metadata to {meta_path}")

    # Generate Checksum Manifest
    files_to_hash = [csv_path, meta_path]
    manifest_data = generate_checksum_manifest(files_to_hash, root_dir=out_path)
    manifest_filename = "checksum_manifest.json"
    manifest_path = out_path / manifest_filename
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    logger.info(f"Saved checksum manifest to {manifest_path}")

    # Write specific synthetic warning log (Constitution III requirement)
    warning_log_path = Path("results") / SYNTHETIC_WARNING_LOG
    warning_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(warning_log_path, 'a') as f:
        f.write(f"[SYNTHETIC] Generated dataset at {out_path} with seed {seed}.\n")
        f.write(f"[SYNTHETIC] This data is for validation only. No hypothesis testing allowed.\n")
    logger.info(f"Appended synthetic warning to {warning_log_path}")

    return {
        "coordinates": str(csv_path),
        "metadata": str(meta_path),
        "manifest": str(manifest_path),
        "warning_log": str(warning_log_path)
    }

def main():
    """Entry point for CLI execution."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Generate synthetic validation dataset.")
    parser.add_argument("--output-dir", type=str, default="data/processed/synthetic",
                        help="Output directory for synthetic data.")
    parser.add_argument("--n-samples", type=int, default=10, help="Number of samples.")
    parser.add_argument("--grid-size", type=int, default=500, help="Grid size.")
    parser.add_argument("--n-defects", type=int, default=100, help="Defects per sample.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")

    args = parser.parse_args()

    try:
        result = generate_synthetic_dataset(
            output_dir=args.output_dir,
            n_samples=args.n_samples,
            grid_size=args.grid_size,
            n_defects_per_sample=args.n_defects,
            seed=args.seed
        )
        print(f"Synthetic data generation complete. Artifacts written to:")
        for key, path in result.items():
            print(f"  {key}: {path}")
    except Exception as e:
        _get_logger().error(f"Failed to generate synthetic data: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
