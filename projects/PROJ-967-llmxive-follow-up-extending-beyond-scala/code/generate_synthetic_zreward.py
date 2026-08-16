import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

def setup_logging():
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def generate_synthetic_dataset(n_samples=10000, seed=42, output_dir="data/raw"):
    """
    Generate a synthetic Z-Reward dataset for pipeline verification.

    This dataset mimics the schema of the real Z-Reward dataset but uses
    random noise. It is intended for unit testing and pipeline verification
    ONLY.

    Args:
        n_samples (int): Number of samples to generate.
        seed (int): Random seed for reproducibility.
        output_dir (str): Directory to save the output parquet file.

    Returns:
        pd.DataFrame: The generated synthetic dataset.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Generating synthetic dataset with {n_samples} samples (seed={seed})...")

    np.random.seed(seed)

    # Generate prompts and image URLs (mock strings)
    prompts = [f"Sample prompt {i} for dimension {np.random.choice(['Alignment', 'Realism', 'Aesthetics', 'Plausibility'])}" for i in range(n_samples)]
    image_urls = [f"https://example.com/image_{i}.jpg" for i in range(n_samples)]

    # Generate teacher scores: 4 dimensions, independent noise
    # Using different seeds for teacher and human to ensure independence
    np.random.seed(seed)
    teacher_scores = {
        "Alignment": np.random.normal(loc=5, scale=2, size=n_samples),
        "Realism": np.random.normal(loc=5, scale=2, size=n_samples),
        "Aesthetics": np.random.normal(loc=5, scale=2, size=n_samples),
        "Plausibility": np.random.normal(loc=5, scale=2, size=n_samples),
    }

    # Generate student scalar
    student_scalar = np.random.normal(loc=5, scale=2, size=n_samples)

    # Generate human annotations: 4 dimensions, independent noise (different seed)
    np.random.seed(seed + 1000)  # Different seed for independence
    human_annotations = {
        "Alignment": np.random.normal(loc=5, scale=2, size=n_samples),
        "Realism": np.random.normal(loc=5, scale=2, size=n_samples),
        "Aesthetics": np.random.normal(loc=5, scale=2, size=n_samples),
        "Plausibility": np.random.normal(loc=5, scale=2, size=n_samples),
    }

    # Determine primary dimension (randomly selected for simplicity)
    primary_dimensions = np.random.choice(["Alignment", "Realism", "Aesthetics", "Plausibility"], size=n_samples)

    # Construct DataFrame
    df = pd.DataFrame({
        "prompt": prompts,
        "image_url": image_urls,
        "teacher_scores": [
            {k: teacher_scores[k][i] for k in teacher_scores} for i in range(n_samples)
        ],
        "student_scalar": student_scalar,
        "human_annotations": [
            {k: human_annotations[k][i] for k in human_annotations} for i in range(n_samples)
        ],
        "primary_dimension": primary_dimensions,
    })

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save to parquet
    output_file = output_path / "mock_z_reward.parquet"
    df.to_parquet(output_file, index=False)
    logger.info(f"Saved synthetic dataset to {output_file}")

    # Save configuration flag
    config_file = output_path / "config.json"
    config = {
        "IS_MOCK_DATA": True,
        "n_samples": n_samples,
        "seed": seed,
        "generated_at": str(pd.Timestamp.now()),
        "source": "synthetic_generator_T037b"
    }
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)
    logger.info(f"Saved config to {config_file}")

    return df

def save_config(output_dir="data/raw", is_mock=True):
    """
    Save the configuration flag indicating this is mock data.

    Args:
        output_dir (str): Directory to save the config file.
        is_mock (bool): Flag indicating if data is mock.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    config_file = output_path / "config.json"

    # Load existing config if present to preserve other keys, then update
    config = {}
    if config_file.exists():
        with open(config_file, "r") as f:
            config = json.load(f)

    config["IS_MOCK_DATA"] = is_mock
    config["generated_by"] = "T037b"

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

def parse_args():
    parser = argparse.ArgumentParser(description="Generate synthetic Z-Reward dataset for pipeline verification.")
    parser.add_argument(
        "--n-samples",
        type=int,
        default=10000,
        help="Number of samples to generate (default: 10000)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Output directory for the synthetic dataset (default: data/raw)"
    )
    return parser.parse_args()

def main():
    logger = setup_logging()
    args = parse_args()

    try:
        df = generate_synthetic_dataset(
            n_samples=args.n_samples,
            seed=args.seed,
            output_dir=args.output_dir
        )
        save_config(output_dir=args.output_dir, is_mock=True)
        logger.info("Synthetic dataset generation completed successfully.")
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
