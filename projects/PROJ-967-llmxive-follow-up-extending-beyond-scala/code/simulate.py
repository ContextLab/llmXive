import argparse
import json
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd

def setup_logging() -> logging.Logger:
    """Configure and return the logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)

def derive_primary_dimension(species_id: int) -> int:
    """Derive primary dimension using hash(species_id) % 4."""
    return hash(species_id) % 4

def generate_teacher_scores(rng: np.random.Generator) -> Dict[str, float]:
    """Generate synthetic teacher scores for 4 rubric dimensions."""
    return {
        "dimension_0": float(rng.uniform(0.0, 1.0)),
        "dimension_1": float(rng.uniform(0.0, 1.0)),
        "dimension_2": float(rng.uniform(0.0, 1.0)),
        "dimension_3": float(rng.uniform(0.0, 1.0)),
    }

def generate_student_scalar(rng: np.random.Generator) -> float:
    """Generate synthetic student scalar output."""
    return float(rng.uniform(0.0, 1.0))

def generate_human_annotations(rng: np.random.Generator) -> Dict[str, float]:
    """Generate synthetic human annotations for 4 rubric dimensions."""
    return {
        "dimension_0": float(rng.uniform(0.0, 1.0)),
        "dimension_1": float(rng.uniform(0.0, 1.0)),
        "dimension_2": float(rng.uniform(0.0, 1.0)),
        "dimension_3": float(rng.uniform(0.0, 1.0)),
    }

def generate_sample(
    sample_id: int, rng: np.random.Generator, species_id: int
) -> Dict[str, Any]:
    """Generate a single sample record."""
    primary_dim = derive_primary_dimension(species_id)
    return {
        "sample_id": sample_id,
        "image_path": f"/images/pets/sample_{sample_id}.jpg",
        "species_id": species_id,
        "teacher_scores": generate_teacher_scores(rng),
        "student_scalar": generate_student_scalar(rng),
        "human_annotations": generate_human_annotations(rng),
        "primary_dimension": primary_dim,
    }

def run_simulation(n_samples: int, seed: int) -> pd.DataFrame:
    """Run the full simulation and return a DataFrame."""
    rng = np.random.default_rng(seed)
    records = []
    for i in range(n_samples):
        # Generate a deterministic species_id based on sample_id and seed
        species_id = (seed * 1000 + i) % 37  # 37 species in OxfordPets
        records.append(generate_sample(i, rng, species_id))
    return pd.DataFrame(records)

def save_dataset(df: pd.DataFrame, output_path: str) -> None:
    """Save the generated dataset to a parquet file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logging.info(f"Saved dataset to {output_path}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for testing.")
    parser.add_argument(
        "--n-samples",
        type=int,
        default=50,
        help="Number of samples to generate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/mock_oxford_pets.parquet",
        help="Output path for the generated dataset.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    logger = setup_logging()
    logger.info(f"Generating {args.n_samples} samples with seed {args.seed}")

    df = run_simulation(args.n_samples, args.seed)
    save_dataset(df, args.output)

    logger.info("Simulation complete.")

if __name__ == "__main__":
    main()
