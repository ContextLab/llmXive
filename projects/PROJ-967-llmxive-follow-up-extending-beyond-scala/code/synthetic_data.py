"""
Synthetic Data Generator for llmXive Follow-up Project.

Generates a schema-compliant synthetic dataset matching the provisional
schema defined in T001d (contracts/dataset.schema.yaml).

This generator is used for unit testing and development when real data
is unavailable (T037b), but MUST NOT be used for hypothesis validation.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
import random
import hashlib

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants matching T001d schema
RUBRIC_DIMENSIONS = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
SAMPLE_PROMPTS = [
    "Explain the concept of quantum entanglement to a 5-year-old.",
    "Write a poem about a robot learning to paint.",
    "Summarize the key events of the French Revolution.",
    "Generate a Python script to sort a list of dictionaries.",
    "Describe the process of photosynthesis in simple terms.",
    "Create a dialogue between two aliens discussing Earth's weather.",
    "Explain how blockchain technology works.",
    "Write a short story about a time traveler who forgets their watch.",
    "Describe the benefits of a plant-based diet.",
    "Analyze the impact of social media on modern communication."
]

def generate_synthetic_prompt(seed: int, index: int) -> str:
    """Generate a deterministic synthetic prompt."""
    # Use seed + index to ensure determinism across runs
    rng = random.Random(seed + index)
    base_prompt = SAMPLE_PROMPTS[index % len(SAMPLE_PROMPTS)]
    # Add variation
    suffix = f" (Variant {index})"
    return base_prompt + suffix

def generate_synthetic_image_url(seed: int, index: int) -> str:
    """Generate a deterministic synthetic image URL."""
    # Create a deterministic hash based on seed and index
    hash_input = f"img-{seed}-{index}"
    hash_val = hashlib.md5(hash_input.encode()).hexdigest()[:16]
    return f"https://example.com/images/{hash_val}.jpg"

def generate_teacher_scores(seed: int, index: int) -> dict:
    """
    Generate teacher scores for all rubric dimensions.
    Scores are sampled from a normal distribution (mean=5, std=2)
    as specified in T037b requirements.
    """
    rng = random.Random(seed + index)
    scores = {}
    for dim in RUBRIC_DIMENSIONS:
        # Sample from normal distribution, clamp to reasonable range [0, 10]
        score = rng.gauss(5, 2)
        scores[dim] = round(max(0.0, min(10.0, score)), 2)
    return scores

def generate_student_scalar(seed: int, index: int, teacher_scores: dict) -> float:
    """
    Generate a student scalar score.
    This is a weighted average of teacher scores with added noise
    to simulate student model approximation.
    """
    rng = random.Random(seed + index + 1000)  # Different seed offset
    # Simple weighted average with noise
    base_score = sum(teacher_scores.values()) / len(teacher_scores)
    noise = rng.gauss(0, 0.5)
    return round(max(0.0, min(10.0, base_score + noise)), 2)

def generate_human_annotations(seed: int, index: int) -> dict:
    """
    Generate human annotations for all rubric dimensions.
    IMPORTANT: These are MOCKS for code structure testing ONLY.
    They are sampled independently from teacher scores with a different seed.
    """
    rng = random.Random(seed + index + 5000)  # Different seed offset to ensure independence
    annotations = {}
    for dim in RUBRIC_DIMENSIONS:
        # Sample from normal distribution, clamp to reasonable range [0, 10]
        score = rng.gauss(5, 2)
        annotations[dim] = round(max(0.0, min(10.0, score)), 2)
    return annotations

def generate_primary_dimension(seed: int, index: int, prompt: str) -> str:
    """
    Generate primary dimension based on prompt metadata rules (T014).
    Uses a deterministic hash of the prompt text to map to one of four dimensions.
    """
    # Deterministic hash of prompt text
    prompt_hash = int(hashlib.md5(prompt.encode()).hexdigest(), 16)
    dimension_index = prompt_hash % len(RUBRIC_DIMENSIONS)
    return RUBRIC_DIMENSIONS[dimension_index]

def generate_synthetic_dataset(n_samples: int, seed: int) -> pd.DataFrame:
    """
    Generate a complete synthetic dataset matching the T001d schema.

    Args:
        n_samples: Number of samples to generate
        seed: Random seed for reproducibility

    Returns:
        Pandas DataFrame with schema-compliant synthetic data
    """
    logger.info(f"Generating {n_samples} synthetic samples with seed {seed}")

    data = {
        'prompt': [],
        'image_url': [],
        'teacher_scores': [],
        'student_scalar': [],
        'human_annotations': [],
        'primary_dimension': []
    }

    for i in range(n_samples):
        prompt = generate_synthetic_prompt(seed, i)
        image_url = generate_synthetic_image_url(seed, i)
        teacher_scores = generate_teacher_scores(seed, i)
        student_scalar = generate_student_scalar(seed, i, teacher_scores)
        human_annotations = generate_human_annotations(seed, i)
        primary_dimension = generate_primary_dimension(seed, i, prompt)

        data['prompt'].append(prompt)
        data['image_url'].append(image_url)
        data['teacher_scores'].append(teacher_scores)
        data['student_scalar'].append(student_scalar)
        data['human_annotations'].append(human_annotations)
        data['primary_dimension'].append(primary_dimension)

    df = pd.DataFrame(data)

    # Add metadata flag to indicate this is synthetic data (T037b requirement)
    df['IS_MOCK_DATA'] = True

    logger.info(f"Generated {len(df)} samples")
    logger.info(f"Schema columns: {list(df.columns)}")
    logger.info(f"Sample primary dimensions: {df['primary_dimension'].value_counts().to_dict()}")

    return df

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic dataset for llmXive project testing."
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=10000,
        help="Number of synthetic samples to generate (default: 10000)"
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
        default="data/raw/z_reward_synthetic.parquet",
        help="Output file path (default: data/raw/z_reward_synthetic.parquet)"
    )
    return parser.parse_args()

def main():
    """Main entry point for synthetic data generation."""
    args = parse_args()

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate dataset
    df = generate_synthetic_dataset(n_samples=args.n_samples, seed=args.seed)

    # Write to parquet
    logger.info(f"Writing synthetic dataset to {output_path}")
    df.to_parquet(output_path, index=False)

    # Write a small JSON summary for verification
    summary_path = output_path.with_suffix('.json')
    summary = {
        "n_samples": args.n_samples,
        "seed": args.seed,
        "output_file": str(output_path),
        "is_mock_data": True,
        "schema_columns": list(df.columns),
        "primary_dimension_distribution": df['primary_dimension'].value_counts().to_dict()
    }
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Successfully generated {args.n_samples} samples")
    logger.info(f"Output file: {output_path}")
    logger.info(f"Summary file: {summary_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())