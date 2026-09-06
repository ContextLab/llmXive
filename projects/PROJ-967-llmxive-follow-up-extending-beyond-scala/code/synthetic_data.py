import argparse
import json
import logging
import os
import sys
import random
import numpy as np
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_synthetic_prompt(seed_offset: int = 0) -> str:
    """Generate a synthetic prompt string."""
    base_prompts = [
        "Describe the image in detail.",
        "What is happening in this scene?",
        "Evaluate the realism of the depicted scenario.",
        "Assess the aesthetic quality of the composition.",
        "Determine the plausibility of the event."
    ]
    return f"{base_prompts[seed_offset % len(base_prompts)]} [ID:{seed_offset}]"

def generate_synthetic_image_url(seed_offset: int = 0) -> str:
    """Generate a synthetic image URL."""
    return f"https://example.com/images/synth_{seed_offset:05d}.jpg"

def generate_teacher_scores(seed: int, n_samples: int) -> pd.DataFrame:
    """
    Generate teacher scores for four rubric dimensions.
    Scores are sampled from np.random.normal(loc=5, scale=2).
    """
    rng = np.random.default_rng(seed)
    data = {
        "Alignment": rng.normal(loc=5, scale=2, size=n_samples),
        "Realism": rng.normal(loc=5, scale=2, size=n_samples),
        "Aesthetics": rng.normal(loc=5, scale=2, size=n_samples),
        "Plausibility": rng.normal(loc=5, scale=2, size=n_samples)
    }
    return pd.DataFrame(data)

def generate_student_scalar(seed: int, n_samples: int) -> np.ndarray:
    """Generate student scalar scores."""
    rng = np.random.default_rng(seed + 1) # Different seed for independence
    return rng.normal(loc=5, scale=2, size=n_samples)

def generate_human_annotations(seed: int, n_samples: int) -> pd.DataFrame:
    """
    Generate human annotations for four rubric dimensions.
    CRITICAL: Sampled independently from teacher scores with a different seed
    to guarantee independent noise structures for unit testing.
    """
    rng = np.random.default_rng(seed + 2) # Different seed for independence
    data = {
        "Alignment": rng.normal(loc=5, scale=2, size=n_samples),
        "Realism": rng.normal(loc=5, scale=2, size=n_samples),
        "Aesthetics": rng.normal(loc=5, scale=2, size=n_samples),
        "Plausibility": rng.normal(loc=5, scale=2, size=n_samples)
    }
    return pd.DataFrame(data)

def generate_primary_dimension(seed: int, n_samples: int) -> np.ndarray:
    """Generate primary dimension labels based on metadata rules."""
    rng = np.random.default_rng(seed + 3)
    dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    return rng.choice(dimensions, size=n_samples)

def generate_synthetic_dataset(n_samples: int, seed: int) -> pd.DataFrame:
    """
    Generate a complete synthetic dataset matching the schema.
    NOTE: This data is for unit-testing only.
    """
    logger.info(f"Generating synthetic dataset with {n_samples} samples and seed {seed}")
    
    # Generate components
    prompts = [generate_synthetic_prompt(i) for i in range(n_samples)]
    image_urls = [generate_synthetic_image_url(i) for i in range(n_samples)]
    
    teacher_df = generate_teacher_scores(seed, n_samples)
    student_scalars = generate_student_scalar(seed, n_samples)
    human_df = generate_human_annotations(seed, n_samples)
    primary_dims = generate_primary_dimension(seed, n_samples)
    
    # Construct DataFrame
    df = pd.DataFrame({
        "prompt": prompts,
        "image_url": image_urls,
        "teacher_scores": [teacher_df.iloc[i].to_dict() for i in range(n_samples)],
        "student_scalar": student_scalars,
        "human_annotations": [human_df.iloc[i].to_dict() for i in range(n_samples)],
        "primary_dimension": primary_dims
    })
    
    return df

def save_config(output_path: Path, is_mock: bool = True) -> None:
    """Update data/processed/config.json with the mock flag."""
    config_path = output_path.parent / "config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    config = {}
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    
    config["IS_MOCK_DATA"] = is_mock
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Updated config.json at {config_path}")

def update_research_md(project_root: Path, is_mock: bool = True) -> None:
    """Append a note to research.md indicating synthetic data source."""
    specs_dir = project_root / "specs" / "001-llmxive-follow-up-extending-beyond-scala"
    research_md_path = specs_dir / "research.md"
    
    if not specs_dir.exists():
        specs_dir.mkdir(parents=True, exist_ok=True)
        
    note = "\n\n## Synthetic Data Note\n"
    note += "This run used mock data generated for unit testing (T037b). "
    note += "Human annotations are mocks for code structure testing only "
    note += "and MUST NOT be used to validate the hypothesis or calculate final fidelity loss metrics.\n"
    
    if research_md_path.exists():
        with open(research_md_path, 'r') as f:
            content = f.read()
        if "Synthetic Data Note" not in content:
            with open(research_md_path, 'a') as f:
                f.write(note)
    else:
        with open(research_md_path, 'w') as f:
            f.write("# Research Notes\n")
            f.write(note)
    
    logger.info(f"Updated research.md at {research_md_path}")

def update_results_json(project_root: Path) -> None:
    """Write IS_SYNTHETIC_RUN: true to results.json."""
    results_path = project_root / "results" / "results.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = {}
    if results_path.exists():
        with open(results_path, 'r') as f:
            data = json.load(f)
    
    data["IS_SYNTHETIC_RUN"] = True
    
    with open(results_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Updated results.json at {results_path}")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for unit testing.")
    parser.add_argument("--n-samples", type=int, default=50, help="Number of samples to generate.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    parser.add_argument("--output", type=str, default="data/raw/mock_z_reward.parquet", 
                        help="Output path for the parquet file.")
    parser.add_argument("--project-root", type=str, default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala",
                        help="Root path of the project.")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    
    # Ensure paths are relative to the project root
    project_root = Path(args.project_root)
    output_path = project_root / args.output
    
    # Generate dataset
    df = generate_synthetic_dataset(n_samples=args.n_samples, seed=args.seed)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved synthetic dataset to {output_path}")
    
    # Update config.json
    save_config(output_path, is_mock=True)
    
    # Update research.md
    update_research_md(project_root)
    
    # Update results.json
    update_results_json(project_root)
    
    logger.info("Synthetic dataset generation completed successfully.")

if __name__ == "__main__":
    main()
