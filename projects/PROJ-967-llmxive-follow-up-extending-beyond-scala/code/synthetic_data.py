"""
Synthetic Data Generator for Z-Reward Schema.

Generates a schema-compliant synthetic dataset for unit testing purposes only.
This data is NOT for hypothesis validation or final metric calculation.

Schema (from T001d):
- prompt: string
- image_url: string
- teacher_scores: object (Alignment, Realism, Aesthetics, Plausibility) -> float
- student_scalar: float
- human_annotations: object (Alignment, Realism, Aesthetics, Plausibility) -> float
- primary_dimension: string
"""

import argparse
import json
import logging
import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_synthetic_prompt(seed: int, index: int) -> str:
    """Generate a deterministic synthetic prompt."""
    # Use a small corpus of templates to ensure variety but determinism
    templates = [
        "Describe an image of {topic} in {style} style.",
        "Generate a realistic depiction of {topic} with {mood} mood.",
        "Create an artistic rendering of {topic} focusing on {aspect}.",
        "Write a caption for an image showing {topic} in {context}.",
    ]
    
    topics = ["mountains", "ocean", "cityscape", "forest", "desert", "space", "animals", "architecture"]
    styles = ["photorealistic", "impressionist", "cyberpunk", "watercolor", "oil painting"]
    moods = ["serene", "chaotic", "melancholic", "joyful", "mysterious"]
    aspects = ["lighting", "texture", "composition", "color palette"]
    contexts = ["sunset", "midnight", "dawn", "stormy weather", "clear day"]

    rng = np.random.default_rng(seed + index)
    
    template = rng.choice(templates)
    data = {
        "topic": rng.choice(topics),
        "style": rng.choice(styles),
        "mood": rng.choice(moods),
        "aspect": rng.choice(aspects),
        "context": rng.choice(contexts)
    }
    
    try:
        return template.format(**data)
    except KeyError:
        # Fallback if template keys don't match data keys
        return f"Prompt for sample {index} involving {rng.choice(topics)}"


def generate_synthetic_image_url(index: int) -> str:
    """Generate a deterministic synthetic image URL."""
    return f"https://example.com/images/synthetic/{index:08d}.jpg"


def generate_teacher_scores(seed: int, index: int) -> Dict[str, float]:
    """
    Generate teacher scores for the four rubric dimensions.
    Sampled from normal distribution: loc=5, scale=2.
    """
    rng = np.random.default_rng(seed + index)
    dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    
    # Generate scores with some correlation structure to mimic real data
    # Base score
    base = rng.normal(loc=5.0, scale=2.0)
    
    scores = {}
    for dim in dimensions:
        # Add dimension-specific noise
        noise = rng.normal(loc=0.0, scale=1.0)
        scores[dim] = round(float(base + noise), 4)
        
    return scores


def generate_student_scalar(seed: int, index: int, teacher_scores: Dict[str, float]) -> float:
    """
    Generate student scalar score.
    Ideally correlated with teacher scores but with independent noise.
    """
    rng = np.random.default_rng(seed + index + 1000) # Offset seed for independence
    
    # Calculate average teacher score
    avg_teacher = sum(teacher_scores.values()) / len(teacher_scores)
    
    # Student score is correlated but with noise
    student_score = avg_teacher + rng.normal(loc=0.0, scale=1.5)
    
    return round(float(student_score), 4)


def generate_human_annotations(seed: int, index: int) -> Dict[str, float]:
    """
    Generate human annotations for the four rubric dimensions.
    IMPORTANT: These are MOCKS for code structure testing only.
    They are sampled independently from teacher scores with a different seed.
    """
    rng = np.random.default_rng(seed + index + 5000) # Distinct seed for independence
    dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    
    annotations = {}
    for dim in dimensions:
        # Independent noise structure as per requirement
        annotations[dim] = round(float(rng.normal(loc=5.0, scale=2.0)), 4)
        
    return annotations


def generate_primary_dimension(seed: int, index: int) -> str:
    """
    Generate a primary dimension based on a deterministic hash of the index.
    This satisfies the requirement for a metadata-based derivation rule.
    """
    dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    # Use a simple hash to pick one deterministically
    idx = (seed + index) % len(dimensions)
    return dimensions[idx]


def generate_synthetic_dataset(n_samples: int, seed: int) -> pd.DataFrame:
    """
    Generate the full synthetic dataset.
    
    Args:
        n_samples: Number of samples to generate.
        seed: Random seed for reproducibility.
        
    Returns:
        pandas.DataFrame matching the Z-Reward schema.
    """
    logger.info(f"Generating {n_samples} synthetic samples with seed {seed}...")
    
    data = {
        "prompt": [],
        "image_url": [],
        "teacher_scores": [],
        "student_scalar": [],
        "human_annotations": [],
        "primary_dimension": []
    }
    
    for i in range(n_samples):
        prompt = generate_synthetic_prompt(seed, i)
        image_url = generate_synthetic_image_url(i)
        teacher_scores = generate_teacher_scores(seed, i)
        student_scalar = generate_student_scalar(seed, i, teacher_scores)
        human_annotations = generate_human_annotations(seed, i)
        primary_dimension = generate_primary_dimension(seed, i)
        
        data["prompt"].append(prompt)
        data["image_url"].append(image_url)
        data["teacher_scores"].append(teacher_scores)
        data["student_scalar"].append(student_scalar)
        data["human_annotations"].append(human_annotations)
        data["primary_dimension"].append(primary_dimension)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Generated {i + 1}/{n_samples} samples...")
            
    df = pd.DataFrame(data)
    logger.info("Synthetic dataset generation complete.")
    return df


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic Z-Reward dataset for unit testing."
    )
    parser.add_argument(
        "--n-samples", 
        type=int, 
        default=50,
        help="Number of synthetic samples to generate (default: 50)"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/raw/mock_z_reward.parquet",
        help="Output file path (default: data/raw/mock_z_reward.parquet)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for synthetic data generation."""
    args = parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate dataset
    df = generate_synthetic_dataset(n_samples=args.n_samples, seed=args.seed)
    
    # Write to parquet
    # Using compression='snappy' for efficiency, or 'none' if dependencies are limited
    try:
        df.to_parquet(output_path, index=False, compression='snappy')
    except Exception as e:
        logger.warning(f"Snappy compression failed, trying gzip: {e}")
        df.to_parquet(output_path, index=False, compression='gzip')
        
    logger.info(f"Dataset written to {output_path}")
    logger.info(f"Schema verification: {list(df.columns)}")
    
    # Log a sample row for quick verification
    logger.info(f"Sample row 0: {df.iloc[0].to_dict()}")


if __name__ == "__main__":
    main()