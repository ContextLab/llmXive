"""
T037c: Generate synthetic dataset automatically (FALLBACK).

This script is invoked automatically by T037 if real data is missing.
It generates a schema-compliant synthetic dataset with independent noise
structures for teacher scores and human annotations.

Output:
  - data/raw/z_reward_synthetic.parquet
  - Updates data/processed/config.json (IS_SYNTHETIC_RUN: true)
  - Updates research.md to reflect synthetic source
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def generate_synthetic_prompt(n: int, seed: int) -> list[str]:
    """Generate synthetic prompts."""
    np.random.seed(seed)
    prompts = [
        f"Generate an image of a {animal} in a {setting} style.",
        f"Write a story about a {person} who finds a {object}.",
        f"Design a {building} with {color} accents.",
    ]
    # Simple cycling for synthetic data
    return [prompts[i % len(prompts)].format(
        animal=np.random.choice(["cat", "dog", "bird", "lion"]),
        setting=np.random.choice(["forest", "city", "ocean", "space"]),
        person=np.random.choice(["hero", "villain", "wizard", "robot"]),
        object=np.random.choice(["key", "map", "gem", "sword"]),
        building=np.random.choice(["castle", "tower", "bridge", "house"]),
        color=np.random.choice(["red", "blue", "green", "gold"])
    ) for i in range(n)]

def generate_synthetic_image_url(n: int) -> list[str]:
    """Generate synthetic image URLs."""
    return [f"https://example.com/synthetic/img_{i}.png" for i in range(n)]

def generate_teacher_scores(n: int, seed: int) -> np.ndarray:
    """
    Generate teacher scores (Alignment, Realism, Aesthetics, Plausibility).
    Sampled from normal distribution: loc=5, scale=2.
    """
    np.random.seed(seed)
    # Shape: (n, 4)
    return np.random.normal(loc=5.0, scale=2.0, size=(n, 4))

def generate_student_scalar(n: int, seed: int) -> np.ndarray:
    """Generate student scalar scores."""
    np.random.seed(seed + 1) # Different seed for independence
    return np.random.normal(loc=5.0, scale=2.0, size=n)

def generate_human_annotations(n: int, seed: int) -> np.ndarray:
    """
    Generate human annotations (Alignment, Realism, Aesthetics, Plausibility).
    CRITICAL: Sampled from a SEPARATE random seed to guarantee independent noise.
    """
    # Use a distinct seed offset to ensure statistical independence from teacher scores
    np.random.seed(seed + 100)
    return np.random.normal(loc=5.0, scale=2.0, size=(n, 4))

def generate_primary_dimension(n: int, seed: int) -> list[str]:
    """Generate primary dimension labels based on metadata rules."""
    np.random.seed(seed + 200)
    dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    return [np.random.choice(dimensions) for _ in range(n)]

def generate_synthetic_dataset(n_samples: int, seed: int = 42) -> pd.DataFrame:
    """
    Generate the full synthetic dataset matching the schema.
    """
    logger.info(f"Generating {n_samples} synthetic samples with seed {seed}...")

    prompts = generate_synthetic_prompt(n_samples, seed)
    image_urls = generate_synthetic_image_url(n_samples)
    teacher_scores = generate_teacher_scores(n_samples, seed)
    student_scalars = generate_student_scalar(n_samples, seed)
    human_annotations = generate_human_annotations(n_samples, seed)
    primary_dimensions = generate_primary_dimension(n_samples, seed)

    # Construct DataFrame
    # teacher_scores and human_annotations are arrays of shape (n, 4)
    # We need to convert them to lists of dicts or objects for the schema
    teacher_scores_list = [
        {
            "Alignment": float(row[0]),
            "Realism": float(row[1]),
            "Aesthetics": float(row[2]),
            "Plausibility": float(row[3])
        }
        for row in teacher_scores
    ]

    human_annotations_list = [
        {
            "Alignment": float(row[0]),
            "Realism": float(row[1]),
            "Aesthetics": float(row[2]),
            "Plausibility": float(row[3])
        }
        for row in human_annotations
    ]

    df = pd.DataFrame({
        "prompt": prompts,
        "image_url": image_urls,
        "teacher_scores": teacher_scores_list,
        "student_scalar": student_scalars,
        "human_annotations": human_annotations_list,
        "primary_dimension": primary_dimensions
    })

    logger.info("Synthetic dataset generation complete.")
    return df

def save_config(is_synthetic: bool, output_path: str):
    """
    Update data/processed/config.json to flag synthetic run.
    """
    config_path = Path(output_path).parent / "config.json"
    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            config = {}

    config["IS_SYNTHETIC_RUN"] = is_synthetic
    config["data_source"] = "synthetic_fallback"

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    logger.info(f"Updated {config_path} with IS_SYNTHETIC_RUN: {is_synthetic}")

def update_research_md(output_path: str):
    """
    Append note to research.md indicating synthetic source.
    """
    # Determine project root relative to this script
    # Assuming script is in code/, project root is parent of code/
    project_root = Path(output_path).parent.parent
    research_md_path = project_root / "specs" / "001-llmxive-follow-up-extending-beyond-scala" / "research.md"

    if not research_md_path.exists():
        logger.warning(f"research.md not found at {research_md_path}. Skipping update.")
        return

    note = "\n\n---\n**Note**: This run used synthetic data fallback (T037c).\n"

    with open(research_md_path, 'a') as f:
        f.write(note)

    logger.info(f"Appended synthetic note to {research_md_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Generate synthetic Z-Reward dataset (Fallback).")
    parser.add_argument(
        "--n-samples",
        type=int,
        default=10000,
        help="Number of synthetic samples to generate (default: 10000)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/z_reward_synthetic.parquet",
        help="Output path for the synthetic parquet file."
    )
    return parser.parse_args()

def main():
    args = parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate dataset
    df = generate_synthetic_dataset(n_samples=args.n_samples, seed=args.seed)

    # Validate schema (basic check)
    required_cols = ["prompt", "image_url", "teacher_scores", "student_scalar", "human_annotations", "primary_dimension"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing required columns in generated data: {missing}")

    # Write to parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved synthetic dataset to {output_path}")

    # Update config
    save_config(is_synthetic=True, output_path=str(output_path))

    # Update research.md
    update_research_md(str(output_path))

    logger.info("T037c Synthetic Fallback generation completed successfully.")

if __name__ == "__main__":
    main()