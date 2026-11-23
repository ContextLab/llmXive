import argparse
import json
import logging
import os
import sys
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure project root is in path for imports if running as script
# However, this script is self-contained for generation purposes.
# It relies on T000d (simulate.py) being present in code/

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def generate_deterministic_scores(prompt_text: str, species_id: int, seed_offset: int = 0) -> list:
    """
    Generates a deterministic list of 4 floats based on prompt_text and species_id.
    Uses a hash function to ensure reproducibility without randomness.
    """
    # Combine inputs into a single seed string
    seed_str = f"{species_id}:{prompt_text}:{seed_offset}"
    hash_val = int(hashlib.sha256(seed_str.encode('utf-8')).hexdigest(), 16)
    
    # Generate 4 values in [0, 1)
    scores = []
    for i in range(4):
        # Use different slices of the hash for each dimension to ensure variation
        dim_hash = (hash_val >> (i * 64)) & 0xFFFFFFFFFFFFFFFF
        val = (dim_hash % 10000) / 10000.0
        scores.append(float(val))
    
    return scores

def generate_student_scalar(teacher_scores: list) -> float:
    """
    Derives student_scalar from teacher_scores via mean.
    """
    return float(np.mean(teacher_scores))

def generate_human_annotations(prompt_text: str, species_id: int) -> list:
    """
    Generates human annotations determinically from species_id and prompt_text ONLY.
    Explicitly NO dependency on teacher_scores.
    """
    # Use a different offset to ensure independence from teacher_scores generation
    return generate_deterministic_scores(prompt_text, species_id, seed_offset=9999)

def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Generate synthetic unit-test dataset")
    parser.add_argument("--n-samples", type=int, default=50, help="Number of samples to generate")
    parser.add_argument("--seed", type=int, default=42, help="Seed for reproducibility (used for species_id generation)")
    parser.add_argument("--output", type=str, default="data/raw/mock_oxford_pets.parquet", help="Output file path")
    args = parser.parse_args()

    n_samples = args.n_samples
    seed = args.seed
    output_path = Path(args.output)

    logger.info(f"Generating {n_samples} synthetic samples with seed {seed}...")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate synthetic data
    data = {
        "image_path": [],
        "species_id": [],
        "prompt_text": [],
        "teacher_scores": [],
        "student_scalar": [],
        "human_annotations": []
    }

    np.random.seed(seed)
    
    # Mock species list for variety
    mock_species = list(range(1, 37)) # Oxford Pets has ~37 species
    
    for i in range(n_samples):
        species_id = np.random.choice(mock_species)
        # Mock prompt text based on species
        prompt_text = f"Generate an image of a {species_id} pet"
        
        # Generate scores
        teacher_scores = generate_deterministic_scores(prompt_text, species_id)
        student_scalar = generate_student_scalar(teacher_scores)
        human_annotations = generate_human_annotations(prompt_text, species_id)

        data["image_path"].append(f"/images/mock_{i}.jpg")
        data["species_id"].append(species_id)
        data["prompt_text"].append(prompt_text)
        data["teacher_scores"].append(teacher_scores)
        data["student_scalar"].append(student_scalar)
        data["human_annotations"].append(human_annotations)

    # Create DataFrame
    df = pd.DataFrame(data)

    # Save to parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Dataset saved to {output_path}")
    logger.info(f"Total samples: {len(df)}")

    # Log validation info
    validation_log_path = output_path.parent / "validation_log.json"
    log_entry = {
        "source": "mock_oxford_pets",
        "status": "generated",
        "n_samples": n_samples,
        "seed": seed,
        "output_path": str(output_path)
    }
    
    # Append to existing log if exists, otherwise create
    if validation_log_path.exists():
        with open(validation_log_path, 'r') as f:
            try:
                logs = json.load(f)
                if not isinstance(logs, list):
                    logs = [logs]
            except json.JSONDecodeError:
                logs = []
        logs.append(log_entry)
        with open(validation_log_path, 'w') as f:
            json.dump(logs, f, indent=2)
    else:
        with open(validation_log_path, 'w') as f:
            json.dump([log_entry], f, indent=2)
    
    logger.info(f"Validation log updated at {validation_log_path}")

if __name__ == "__main__":
    main()
