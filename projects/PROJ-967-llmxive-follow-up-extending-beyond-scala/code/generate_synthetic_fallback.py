"""
Synthetic Data Fallback Generator for llmXive Follow-up Project.

This module generates a synthetic dataset adhering to the schema defined in
contracts/dataset.schema.yaml. It is intended as a fallback mechanism if the
primary data source (T037) fails.

CRITICAL: This script must strictly adhere to the schema to ensure downstream
validation (T038) and feature engineering (T025) work correctly.
"""

import argparse
import csv
import logging
import os
import sys
import random
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
def setup_logging(log_file: str = "logs/ingest.log") -> logging.Logger:
    """Setup logging to file and console."""
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("synthetic_fallback")
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def generate_synthetic_row(
    sample_id: int,
    dimensions: List[str],
    random_seed: int
) -> Dict[str, Any]:
    """
    Generate a single synthetic row adhering to the schema.

    Schema requirements:
    - prompt (str)
    - image_path (str)
    - teacher_logits (list[float]) - 4 dimensions
    - student_scalar (float)
    - human_annotations (dict{dim: float}) - 4 dimensions
    - primary_dimension (str)
    """
    random.seed(random_seed + sample_id)

    # Generate prompt
    prompt = f"Synthetic prompt for sample {sample_id} regarding topic {random.choice(['quality', 'alignment', 'safety'])}"

    # Generate image path
    image_path = f"data/images/synthetic_{sample_id:05d}.jpg"

    # Generate teacher_logits (4 floats)
    # Simulating a distribution over 4 dimensions: Alignment, Realism, Aesthetics, Plausibility
    teacher_logits = [round(random.uniform(0.0, 10.0), 4) for _ in range(4)]

    # Generate student_scalar (single float)
    student_scalar = round(random.uniform(0.0, 10.0), 4)

    # Generate human_annotations (dict mapping dimension name to float)
    human_annotations = {}
    for dim in dimensions:
        human_annotations[dim] = round(random.uniform(0.0, 10.0), 4)

    # Select primary dimension (randomly for synthetic data)
    primary_dimension = random.choice(dimensions)

    return {
        "sample_id": sample_id,
        "prompt": prompt,
        "image_path": image_path,
        "teacher_logits": teacher_logits,
        "student_scalar": student_scalar,
        "human_annotations": human_annotations,
        "primary_dimension": primary_dimension
    }

def generate_synthetic_dataset(
    output_path: str,
    num_samples: int = 100,
    dimensions: List[str] = None,
    random_seed: int = 42
) -> None:
    """
    Generate the full synthetic dataset and write to CSV.

    Args:
        output_path: Path to the output CSV file.
        num_samples: Number of rows to generate.
        dimensions: List of dimension names for human_annotations keys.
        random_seed: Base seed for reproducibility.
    """
    if dimensions is None:
        dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]

    logger = logging.getLogger("synthetic_fallback")
    logger.info(f"Generating {num_samples} synthetic samples...")

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "sample_id",
        "prompt",
        "image_path",
        "teacher_logits",
        "student_scalar",
        "human_annotations",
        "primary_dimension"
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(num_samples):
            row = generate_synthetic_row(i, dimensions, random_seed)
            # Convert list and dict to string representation for CSV storage
            # This matches how pandas/scikit-learn often handle complex types in CSVs
            # or we can use JSON strings. The schema validator in T038 will need
            # to parse these back.
            row["teacher_logits"] = str(row["teacher_logits"])
            row["human_annotations"] = str(row["human_annotations"])
            writer.writerow(row)

    logger.info(f"Successfully wrote synthetic dataset to {output_path}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic fallback dataset")
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/zreward_dataset_synthetic.csv",
        help="Path to output CSV file"
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=100,
        help="Number of synthetic samples to generate"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    logger = setup_logging()

    # Log fallback activation as required
    logger.warning("FALLBACK MODE ACTIVATED: Generating synthetic data due to primary source failure.")

    generate_synthetic_dataset(
        output_path=args.output,
        num_samples=args.num_samples,
        random_seed=args.seed
    )

    logger.info("Synthetic fallback generation complete.")

if __name__ == "__main__":
    main()