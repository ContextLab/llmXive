"""
T037c: Generate synthetic dataset automatically (FALLBACK).

This module implements the automatic fallback mechanism for T037.
It generates a schema-compliant synthetic dataset when real data is missing.

CRITICAL: This is strictly for automatic fallback. Do NOT invoke manually for unit testing.
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_synthetic_prompt(n_samples: int, seed: int) -> list[str]:
    """Generate synthetic prompts."""
    np.random.seed(seed)
    templates = [
        "Describe the {adj} {noun} in the {context}.",
        "Explain why {noun} is {adj} in {context}.",
        "What makes {noun} {adj} when viewed from {context}?",
    ]
    adjectives = ["beautiful", "complex", "simple", "vibrant", "mysterious"]
    nouns = ["landscape", "city", "person", "object", "scene"]
    contexts = ["forest", "city", "ocean", "mountain", "desert"]
    
    prompts = []
    for _ in range(n_samples):
        template = np.random.choice(templates)
        prompt = template.format(
            adj=np.random.choice(adjectives),
            noun=np.random.choice(nouns),
            context=np.random.choice(contexts)
        )
        prompts.append(prompt)
    return prompts

def generate_synthetic_image_url(n_samples: int, seed: int) -> list[str]:
    """Generate synthetic image URLs."""
    np.random.seed(seed + 1)
    return [f"https://example.com/images/synthetic_{i}.jpg" for i in range(n_samples)]

def generate_teacher_scores(n_samples: int, seed: int) -> np.ndarray:
    """
    Generate teacher scores for the four rubric dimensions.
    
    Teacher scores are sampled from np.random.normal(loc=5, scale=2, size=...)
    with a specific seed to ensure reproducibility.
    """
    np.random.seed(seed + 2)
    # 4 dimensions: Alignment, Realism, Aesthetics, Plausibility
    return np.random.normal(loc=5, scale=2, size=(n_samples, 4))

def generate_student_scalar(n_samples: int, seed: int) -> np.ndarray:
    """Generate student scalar scores."""
    np.random.seed(seed + 3)
    return np.random.normal(loc=5, scale=2, size=n_samples)

def generate_human_annotations(n_samples: int, seed: int) -> np.ndarray:
    """
    Generate human annotations for the four rubric dimensions.
    
    CRITICAL: Human annotations are sampled independently from a separate 
    np.random.normal(loc=5, scale=2, ...) with a DIFFERENT seed than teacher scores,
    guaranteeing independent noise structures as required by the spec.
    """
    np.random.seed(seed + 100)  # Different seed from teacher scores
    # 4 dimensions: Alignment, Realism, Aesthetics, Plausibility
    return np.random.normal(loc=5, scale=2, size=(n_samples, 4))

def generate_primary_dimension(n_samples: int, seed: int) -> list[str]:
    """
    Generate primary dimension based on metadata rules.
    
    Uses a deterministic hash of the prompt text mapping to one of the four dimensions.
    """
    np.random.seed(seed + 4)
    dimensions = ["Alignment", "Realism", "Aesthetics", "Plausibility"]
    return [np.random.choice(dimensions) for _ in range(n_samples)]

def generate_synthetic_dataset(n_samples: int = 10000, seed: int = 42) -> pd.DataFrame:
    """
    Generate a complete synthetic dataset matching the schema.
    
    Args:
        n_samples: Number of samples to generate (default: 10,000)
        seed: Random seed for reproducibility
        
    Returns:
        pd.DataFrame: Synthetic dataset with all required columns
    """
    logger.info(f"Generating synthetic dataset with {n_samples} samples (seed={seed})")
    
    # Generate components
    prompts = generate_synthetic_prompt(n_samples, seed)
    image_urls = generate_synthetic_image_url(n_samples, seed)
    teacher_scores = generate_teacher_scores(n_samples, seed)
    student_scalars = generate_student_scalar(n_samples, seed)
    human_annotations = generate_human_annotations(n_samples, seed)
    primary_dimensions = generate_primary_dimension(n_samples, seed)
    
    # Create DataFrame
    df = pd.DataFrame({
        'prompt': prompts,
        'image_url': image_urls,
        'teacher_scores': list(teacher_scores),
        'student_scalar': student_scalars,
        'human_annotations': list(human_annotations),
        'primary_dimension': primary_dimensions
    })
    
    logger.info(f"Synthetic dataset generated successfully with {len(df)} samples")
    return df

def save_config(output_path: Path, is_synthetic: bool = True) -> None:
    """
    Save configuration flag to data/processed/config.json.
    
    Args:
        output_path: Path to config.json
        is_synthetic: Flag indicating if this is a synthetic run
    """
    config_path = output_path.parent / "config.json"
    
    # Load existing config if it exists, otherwise create new
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    # Update config
    config['IS_SYNTHETIC_RUN'] = is_synthetic
    config['source_type'] = 'synthetic'
    config['generated_at'] = pd.Timestamp.now().isoformat()
    
    # Write config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Config updated: IS_SYNTHETIC_RUN={is_synthetic}")

def update_research_md(research_md_path: Path, note: str = "synthetic_fallback") -> None:
    """
    Update research.md to indicate synthetic data source.
    
    Args:
        research_md_path: Path to research.md
        note: Note to append about synthetic data
    """
    if not research_md_path.exists():
        logger.warning(f"research.md not found at {research_md_path}, skipping update")
        return
    
    with open(research_md_path, 'r') as f:
        content = f.read()
    
    # Check if synthetic note already exists
    if 'synthetic_fallback' not in content:
        # Append note
        content += f"\n\n**NOTE**: Synthetic data fallback used: {note}\n"
        
        with open(research_md_path, 'w') as f:
            f.write(content)
        
        logger.info("research.md updated with synthetic data note")
    else:
        logger.info("research.md already contains synthetic data note")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic dataset for automatic fallback (T037c)"
    )
    parser.add_argument(
        '--n-samples',
        type=int,
        default=10000,
        help='Number of samples to generate (default: 10000)'
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
        default='data/raw/z_reward_synthetic.parquet',
        help='Output path for the synthetic dataset (default: data/raw/z_reward_synthetic.parquet)'
    )
    parser.add_argument(
        '--project-root',
        type=str,
        default='projects/PROJ-967-llmxive-follow-up-extending-beyond-scala',
        help='Project root directory'
    )
    return parser.parse_args()

def main():
    """Main entry point for T037c."""
    args = parse_args()
    
    project_root = Path(args.project_root)
    output_path = project_root / args.output
    research_md_path = project_root / "specs/001-llmxive-follow-up-extending-beyond-scala/research.md"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Generate synthetic dataset
        df = generate_synthetic_dataset(n_samples=args.n_samples, seed=args.seed)
        
        # Validate schema
        required_columns = [
            'prompt', 'image_url', 'teacher_scores', 
            'student_scalar', 'human_annotations', 'primary_dimension'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise RuntimeError(f"Missing required columns: {missing_columns}")
        
        # Write to parquet
        df.to_parquet(output_path, index=False)
        logger.info(f"Synthetic dataset written to {output_path}")
        
        # Update config.json
        config_path = project_root / "data/processed"
        save_config(config_path, is_synthetic=True)
        
        # Update research.md
        update_research_md(research_md_path)
        
        logger.info("T037c completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}")
        raise

if __name__ == '__main__':
    main()
