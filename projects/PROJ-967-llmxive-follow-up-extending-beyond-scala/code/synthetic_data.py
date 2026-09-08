"""
Synthetic Dataset Generator for Unit Testing (MANUAL INVOCATION ONLY).

This script generates a schema-compliant synthetic dataset for testing the
Z-Reward pipeline logic (specifically Ridge Regression paths).

CRITICAL:
- This data is for UNIT TESTING ONLY.
- Do NOT use this data to validate the scientific hypothesis.
- Do NOT invoke automatically if real data is missing.
- Human annotations are MOCKS for code structure testing only.
"""

import argparse
import json
import logging
import os
import sys
import random
from pathlib import Path

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def generate_synthetic_prompt(n: int, seed: int) -> list[str]:
    """Generate synthetic prompts."""
    rng = random.Random(seed)
    prompts = [
        f"Generate an image of a {rng.choice(['cat', 'dog', 'landscape', 'car'])} with {rng.choice(['sunset', 'night', 'daylight'])} lighting.",
        f"Create a visualization of {rng.choice(['data', 'network', 'flow'])} for {rng.choice(['science', 'art', 'finance'])}.",
        f"Design a logo for a {rng.choice(['tech', 'food', 'fashion'])} startup.",
    ]
    return [rng.choice(prompts) for _ in range(n)]


def generate_synthetic_image_url(n: int, seed: int) -> list[str]:
    """Generate synthetic image URLs."""
    rng = random.Random(seed)
    urls = [f"https://example.com/img_{i}.jpg" for i in range(1000)]
    return [rng.choice(urls) for _ in range(n)]


def generate_teacher_scores(n: int, seed: int) -> list[dict]:
    """
    Generate teacher scores for the four rubric dimensions.
    Sampled from normal distribution: loc=5, scale=2.
    """
    rng = np.random.default_rng(seed)
    dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    scores = []
    for _ in range(n):
        row = {dim: float(rng.normal(loc=5, scale=2)) for dim in dimensions}
        scores.append(row)
    return scores


def generate_student_scalar(n: int, seed: int) -> list[float]:
    """Generate student scalar scores."""
    rng = np.random.default_rng(seed)
    return [float(x) for x in rng.normal(loc=5, scale=2, size=n)]


def generate_human_annotations(n: int, seed: int) -> list[dict]:
    """
    Generate human annotations.
    CRITICAL: These are MOCKS for code structure testing only.
    Sampled independently from teacher scores (seed + 1) to ensure
    independent noise structures.
    """
    rng = np.random.default_rng(seed + 1)  # Independent seed
    dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    annotations = []
    for _ in range(n):
        row = {dim: float(rng.normal(loc=5, scale=2)) for dim in dimensions}
        annotations.append(row)
    return annotations


def generate_primary_dimension(n: int, seed: int) -> list[str]:
    """Generate primary dimension based on metadata logic (mocked)."""
    rng = random.Random(seed + 2)
    dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    return [rng.choice(dimensions) for _ in range(n)]


def generate_synthetic_dataset(
    n_samples: int, seed: int
) -> pd.DataFrame:
    """
    Assemble the full synthetic dataset.
    """
    logger.info(f"Generating synthetic dataset with {n_samples} samples (seed={seed})...")

    prompts = generate_synthetic_prompt(n_samples, seed)
    image_urls = generate_synthetic_image_url(n_samples, seed)
    teacher_scores = generate_teacher_scores(n_samples, seed)
    student_scalars = generate_student_scalar(n_samples, seed)
    human_annotations = generate_human_annotations(n_samples, seed)
    primary_dimensions = generate_primary_dimension(n_samples, seed)

    df = pd.DataFrame({
        "prompt": prompts,
        "image_url": image_urls,
        "teacher_scores": teacher_scores,
        "student_scalar": student_scalars,
        "human_annotations": human_annotations,
        "primary_dimension": primary_dimensions,
    })

    logger.info("Synthetic dataset generated successfully.")
    return df


def save_config(output_path: Path, n_samples: int, seed: int) -> None:
    """Save configuration metadata to data/processed/config.json."""
    config_path = output_path.parent / "processed" / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing config if it exists to merge
    existing_config = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                existing_config = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_config = {}

    # Update with mock data flag
    existing_config["IS_MOCK_DATA"] = True
    existing_config["synthetic_seed"] = seed
    existing_config["synthetic_n_samples"] = n_samples

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(existing_config, f, indent=2)

    logger.info(f"Updated config at {config_path} with IS_MOCK_DATA=true")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic Z-Reward dataset for unit testing."
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=50,
        help="Number of synthetic samples to generate (default: 50).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/mock_z_reward.parquet",
        help="Output path for the parquet file (default: data/raw/mock_z_reward.parquet).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate dataset
    df = generate_synthetic_dataset(args.n_samples, args.seed)

    # Write to parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Dataset saved to {output_path}")

    # Update config
    save_config(output_path, args.n_samples, args.seed)

    logger.info("Task completed.")


if __name__ == "__main__":
    main()
