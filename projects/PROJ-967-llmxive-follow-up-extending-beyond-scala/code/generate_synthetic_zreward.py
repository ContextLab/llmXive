"""
Synthetic dataset generator for pipeline verification (T037b).
Generates a mock Z-Reward dataset with independent noise structures for
teacher scores and human annotations to test pipeline robustness.
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
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_logging():
    """Setup logging configuration."""
    return logger

def generate_synthetic_dataset(
    n_samples: int = 1000,
    seed: int = 42,
    output_path: str = "data/raw/mock_z_reward.parquet"
) -> pd.DataFrame:
    """
    Generate a synthetic Z-Reward dataset for pipeline verification.

    Args:
        n_samples: Number of samples to generate.
        seed: Random seed for reproducibility.
        output_path: Path to save the output parquet file.

    Returns:
        Generated DataFrame.
    """
    logger.info(f"Generating synthetic dataset with {n_samples} samples (seed={seed})")

    # Set random seed for reproducibility
    np.random.seed(seed)

    # Generate prompts (simple text templates)
    prompts = [
        f"Describe the image of a {category} in a {style} style."
        for _ in range(n_samples)
    ]
    categories = ["mountain", "ocean", "city", "forest", "desert"]
    styles = ["realistic", "impressionist", "abstract", "minimalist", "surreal"]
    prompts = [
        f"Describe the image of a {np.random.choice(categories)} in a {np.random.choice(styles)} style."
        for _ in range(n_samples)
    ]

    # Generate image URLs (mock URLs)
    image_urls = [f"https://example.com/images/{i}.jpg" for i in range(n_samples)]

    # Generate teacher_scores with independent noise (seed 42)
    # Using a separate seed context to ensure independence from human annotations
    teacher_rng = np.random.RandomState(42)
    teacher_scores = {
        "Alignment": teacher_rng.normal(loc=5.0, scale=2.0, size=n_samples),
        "Realism": teacher_rng.normal(loc=5.0, scale=2.0, size=n_samples),
        "Aesthetics": teacher_rng.normal(loc=5.0, scale=2.0, size=n_samples),
        "Plausibility": teacher_rng.normal(loc=5.0, scale=2.0, size=n_samples)
    }

    # Generate human_annotations with independent noise (different seed: 123)
    # This guarantees independent noise structures as required
    human_rng = np.random.RandomState(123)
    human_annotations = {
        "Alignment": human_rng.normal(loc=5.0, scale=2.0, size=n_samples),
        "Realism": human_rng.normal(loc=5.0, scale=2.0, size=n_samples),
        "Aesthetics": human_rng.normal(loc=5.0, scale=2.0, size=n_samples),
        "Plausibility": human_rng.normal(loc=5.0, scale=2.0, size=n_samples)
    }

    # Generate student_scalar (independent of teacher and human)
    student_scalar = np.random.normal(loc=5.0, scale=2.0, size=n_samples)

    # Generate primary_dimension (randomly selected from the four dimensions)
    dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    primary_dimension = np.random.choice(dimensions, size=n_samples)

    # Create DataFrame
    df = pd.DataFrame({
        "prompt": prompts,
        "image_url": image_urls,
        "student_scalar": student_scalar,
        "primary_dimension": primary_dimension
    })

    # Add teacher_scores as nested dictionaries (pandas supports this in object columns)
    df["teacher_scores"] = [
        {k: v[i] for k, v in teacher_scores.items()}
        for i in range(n_samples)
    ]

    # Add human_annotations as nested dictionaries
    df["human_annotations"] = [
        {k: v[i] for k, v in human_annotations.items()}
        for i in range(n_samples)
    ]

    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save to parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Synthetic dataset saved to {output_path}")

    return df

def save_config(output_dir: str = "data/processed", is_mock: bool = True):
    """
    Save configuration flag indicating mock data usage.

    Args:
        output_dir: Directory to save the config file.
        is_mock: Boolean flag indicating if data is mock.
    """
    config_path = Path(output_dir) / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config = {
        "IS_MOCK_DATA": is_mock,
        "generated_by": "T037b_synthetic_generator",
        "note": "This dataset is for unit testing only. Final results must use real data."
    }

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    logger.info(f"Configuration saved to {config_path}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic Z-Reward dataset for pipeline verification."
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=1000,
        help="Number of samples to generate (default: 1000)"
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
        help="Output path for the synthetic dataset (default: data/raw/mock_z_reward.parquet)"
    )
    parser.add_argument(
        "--config-dir",
        type=str,
        default="data/processed",
        help="Directory to save the config file (default: data/processed)"
    )
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    setup_logging()

    try:
        # Generate synthetic dataset
        df = generate_synthetic_dataset(
            n_samples=args.n_samples,
            seed=args.seed,
            output_path=args.output
        )

        # Save configuration flag
        save_config(output_dir=args.config_dir, is_mock=True)

        logger.info("Synthetic dataset generation completed successfully.")
        logger.info(f"Total samples: {len(df)}")
        logger.info(f"Columns: {list(df.columns)}")

    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
