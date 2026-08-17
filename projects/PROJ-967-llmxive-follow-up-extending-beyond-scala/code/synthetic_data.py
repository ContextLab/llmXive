"""
Synthetic Data Generator for llmXive Follow-up Project.

This module generates schema-compliant synthetic data for testing and
development purposes when real data is unavailable. It strictly adheres
to the provisional schema defined in contracts/dataset.schema.yaml.

Usage:
    python code/synthetic_data.py --n-samples 1000 --seed 42 --output data/raw/synthetic_z_reward.parquet
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants for synthetic data generation
DIMENSIONS = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
PROMPT_TEMPLATES = [
    "Generate a realistic image of {subject} in {style} style.",
    "Create an {adjective} visualization of {concept}.",
    "Produce an image showing {subject} with {attribute}.",
    "Render a {style} depiction of {subject}.",
    "Create an image that captures the essence of {concept}."
]
SUBJECTS = ['mountains', 'ocean', 'forest', 'cityscape', 'abstract pattern', 'human face', 'animal', 'vehicle']
STYLES = ['photorealistic', 'impressionist', 'surreal', 'minimalist', 'cyberpunk', 'watercolor']
ADJECTIVES = ['vibrant', 'mysterious', 'serene', 'chaotic', 'elegant', 'dynamic']
CONCEPTS = ['harmony', 'balance', 'innovation', 'tradition', 'future', 'nature']
ATTRIBUTES = ['warm lighting', 'cool tones', 'high contrast', 'soft focus']

def generate_synthetic_prompt(rng: np.random.Generator) -> str:
    """Generate a synthetic prompt string."""
    template = rng.choice(PROMPT_TEMPLATES)
    return template.format(
        subject=rng.choice(SUBJECTS),
        style=rng.choice(STYLES),
        adjective=rng.choice(ADJECTIVES),
        concept=rng.choice(CONCEPTS),
        attribute=rng.choice(ATTRIBUTES)
    )

def generate_synthetic_image_url(idx: int, rng: np.random.Generator) -> str:
    """Generate a synthetic image URL."""
    # Using a placeholder service for testing
    width = rng.integers(256, 1024)
    height = rng.integers(256, 1024)
    return f"https://via.placeholder.com/{width}x{height}?text=Sample_{idx}"

def generate_teacher_scores(rng: np.random.Generator) -> dict:
    """Generate synthetic teacher scores for the four dimensions."""
    scores = {}
    for dim in DIMENSIONS:
        # Scores sampled from normal distribution (mean=5, std=2)
        scores[dim] = float(rng.normal(loc=5.0, scale=2.0))
    return scores

def generate_student_scalar(rng: np.random.Generator) -> float:
    """Generate a synthetic student scalar score."""
    return float(rng.normal(loc=5.0, scale=2.0))

def generate_human_annotations(rng: np.random.Generator) -> dict:
    """Generate synthetic human annotations for the four dimensions."""
    annotations = {}
    for dim in DIMENSIONS:
        # Independent noise structure from teacher scores
        annotations[dim] = float(rng.normal(loc=5.0, scale=2.0))
    return annotations

def generate_primary_dimension(rng: np.random.Generator) -> str:
    """Generate a synthetic primary dimension."""
    return rng.choice(DIMENSIONS)

def generate_synthetic_dataset(
    n_samples: int,
    seed: int,
    output_path: str
) -> None:
    """
    Generate a synthetic dataset matching the schema.

    Args:
        n_samples: Number of samples to generate.
        seed: Random seed for reproducibility.
        output_path: Path to save the output parquet file.
    """
    logger.info(f"Generating {n_samples} synthetic samples with seed {seed}")
    rng = np.random.default_rng(seed)

    # Pre-allocate lists for efficiency
    prompts = []
    image_urls = []
    teacher_scores_list = []
    student_scalars = []
    human_annotations_list = []
    primary_dimensions = []

    for i in range(n_samples):
        # Generate prompt and image
        prompts.append(generate_synthetic_prompt(rng))
        image_urls.append(generate_synthetic_image_url(i, rng))

        # Generate scores
        teacher_scores = generate_teacher_scores(rng)
        teacher_scores_list.append(teacher_scores)

        student_scalar = generate_student_scalar(rng)
        student_scalars.append(student_scalar)

        # Generate human annotations (independent noise)
        human_annotations = generate_human_annotations(rng)
        human_annotations_list.append(human_annotations)

        # Primary dimension
        primary_dimensions.append(generate_primary_dimension(rng))

    # Create DataFrame
    df = pd.DataFrame({
        'prompt': prompts,
        'image_url': image_urls,
        'teacher_scores': teacher_scores_list,
        'student_scalar': student_scalars,
        'human_annotations': human_annotations_list,
        'primary_dimension': primary_dimensions
    })

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Save to parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully saved synthetic dataset to {output_path}")
    logger.info(f"Dataset shape: {df.shape}")
    logger.info(f"Columns: {list(df.columns)}")

    # Log sample statistics
    logger.info("Sample statistics:")
    for col in ['student_scalar']:
        logger.info(f"  {col}: mean={df[col].mean():.2f}, std={df[col].std():.2f}")

    # Log teacher scores statistics
    for dim in DIMENSIONS:
        scores = [row[dim] for row in teacher_scores_list]
        logger.info(f"  teacher_scores.{dim}: mean={np.mean(scores):.2f}, std={np.std(scores):.2f}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate synthetic dataset for llmXive follow-up project.'
    )
    parser.add_argument(
        '--n-samples',
        type=int,
        default=1000,
        help='Number of synthetic samples to generate (default: 1000)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/raw/synthetic_z_reward.parquet',
        help='Output path for the synthetic dataset (default: data/raw/synthetic_z_reward.parquet)'
    )
    return parser.parse_args()

def main():
    """Main entry point for synthetic data generation."""
    args = parse_args()

    try:
        generate_synthetic_dataset(
            n_samples=args.n_samples,
            seed=args.seed,
            output_path=args.output
        )
        logger.info("Synthetic data generation completed successfully.")
    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
