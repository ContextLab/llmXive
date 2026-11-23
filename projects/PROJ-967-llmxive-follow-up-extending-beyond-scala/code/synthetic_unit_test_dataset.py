"""
T037b: Synthetic Unit-Test Dataset Generator

Generates a small synthetic dataset (N=50) for unit testing via simulate.py.
Includes mock human annotations generated deterministically based on species_id
and prompt_text ONLY, ensuring independence from teacher/student scores.

Usage:
    python code/synthetic_unit_test_dataset.py
"""

import argparse
import json
import logging
import os
import sys
import hashlib
from pathlib import Path

import pandas as pd
import numpy as np

# Ensure we can import from the code directory
CODE_DIR = Path(__file__).parent
PROJECT_ROOT = CODE_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the simulate script logic
# We will call the simulate.py script as a subprocess to ensure consistency
# with the main simulation logic, or we can import functions if available.
# Given the API surface, we assume simulate.py exists and has a CLI.
# However, to keep this self-contained and avoid subprocess complexity for a simple task,
# we will implement the generation logic directly here, matching the spec of simulate.py.

def derive_primary_dimension(prompt_text: str) -> int:
    """
    Derive primary dimension index from prompt text.
    Rule: hash(prompt_text) % 4
    """
    hash_obj = hashlib.sha256(prompt_text.encode('utf-8'))
    hash_int = int(hash_obj.hexdigest(), 16)
    return hash_int % 4

def generate_mock_human_annotations(species_id: int, prompt_text: str, seed: int) -> list:
    """
    Generate mock human annotations.
    CRITICAL: Must be independent of teacher_scores or student_scalar.
    Only depends on species_id and prompt_text.
    """
    # Create a deterministic seed based on inputs
    combined_str = f"{species_id}:{prompt_text}:{seed}"
    hash_val = int(hashlib.sha256(combined_str.encode('utf-8')).hexdigest(), 16)
    rng = np.random.default_rng(hash_val)

    # Generate 4 annotations corresponding to 4 rubric dimensions
    # Values between 0 and 10 (simulating a score)
    annotations = rng.uniform(0, 10, size=4).tolist()
    return annotations

def generate_teacher_scores(seed: int, primary_dim: int) -> list:
    """
    Generate teacher scores (4 dimensions).
    For unit tests, we generate random values.
    """
    rng = np.random.default_rng(seed + 1000) # Offset seed to avoid collision
    scores = rng.uniform(0, 10, size=4).tolist()
    return scores

def generate_student_scalar(seed: int, primary_dim: int) -> float:
    """
    Generate student scalar output.
    For unit tests, random value.
    """
    rng = np.random.default_rng(seed + 2000)
    return float(rng.uniform(0, 10))

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic unit-test dataset")
    parser.add_argument("--n-samples", type=int, default=50, help="Number of samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/raw/mock_oxford_pets.parquet",
                        help="Output file path")
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating {args.n_samples} samples with seed {args.seed}")

    # Mock species and prompts for variety
    species_ids = list(range(1, 38)) # Oxford Pets has 37 species
    prompts = [
        "A photo of a {species}.",
        "Close-up of a {species}.",
        "Side view of a {species}.",
        "A cute {species} in a garden."
    ]

    data = []
    for i in range(args.n_samples):
        # Deterministic selection for reproducibility
        rng = np.random.default_rng(args.seed + i)
        species_id = int(rng.choice(species_ids))
        prompt_template = prompts[i % len(prompts)]
        prompt_text = prompt_template.format(species=f"species_{species_id}")

        # Derive primary dimension
        primary_dim = derive_primary_dimension(prompt_text)

        # Generate annotations (MUST be independent of scores)
        mock_annotations = generate_mock_human_annotations(species_id, prompt_text, args.seed)

        # Generate teacher scores
        teacher_scores = generate_teacher_scores(args.seed + i, primary_dim)

        # Generate student scalar
        student_scalar = generate_student_scalar(args.seed + i, primary_dim)

        # Image path (mock)
        image_path = f"projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/raw/images/img_{i:04d}.jpg"

        row = {
            "image_path": image_path,
            "species_id": species_id,
            "prompt_text": prompt_text,
            "teacher_scores": teacher_scores,
            "student_scalar": student_scalar,
            "human_annotations": mock_annotations,
            "primary_dimension": primary_dim
        }
        data.append(row)

    df = pd.DataFrame(data)

    # Save to parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully wrote {args.n_samples} samples to {output_path}")

    # Log to validation_log.json if it exists, or create it
    validation_log_path = PROJECT_ROOT / "projects/PROJ-967-llmxive-follow-up-extending-beyond-scala/data/raw/validation_log.json"
    if validation_log_path.exists():
        with open(validation_log_path, 'r') as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
    else:
        logs = []

    logs.append({
        "source": "mock_oxford_pets",
        "status": "generated",
        "n_samples": args.n_samples,
        "seed": args.seed,
        "output_path": str(output_path)
    })

    with open(validation_log_path, 'w') as f:
        json.dump(logs, f, indent=2)

    logger.info(f"Updated validation log at {validation_log_path}")

if __name__ == "__main__":
    main()
