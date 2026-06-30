"""
Control Corpus Generation for Phenomenological AI Research.

This script generates a control corpus of non-phenomenological text samples
from the arxiv_nlp dataset to serve as a baseline for discriminant validity
testing. These samples will be processed through the same three validity metrics
(Consistency, Stability, Markers) as the phenomenological reports.

Target: ≥80 control samples via random sampling.
"""

import os
import random
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Import project utilities
from utils.logging import setup_logging, get_logger, retry_on_failure
from utils.io import safe_write_json, ensure_dir
from config import get_config

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Constants
TARGET_SAMPLE_COUNT = 80
DATASET_NAME = "arxiv_nlp"
RANDOM_SEED = 42

def load_control_dataset():
    """
    Load the arxiv_nlp dataset using the datasets library.
    Returns a list of text samples.
    """
    try:
        from datasets import load_dataset
        logger.info(f"Loading dataset: {DATASET_NAME}")
        
        # Load the dataset
        dataset = load_dataset(DATASET_NAME, split="train")
        
        # Extract text samples
        # The arxiv_nlp dataset typically has 'text' or 'abstract' fields
        # We'll use 'text' if available, otherwise fallback to 'abstract'
        text_field = 'text' if 'text' in dataset.column_names else 'abstract'
        logger.info(f"Using field '{text_field}' for sampling")
        
        samples = dataset[text_field]
        logger.info(f"Loaded {len(samples)} total samples from dataset")
        
        return samples
        
    except ImportError:
        logger.error("datasets library not installed. Please install with: pip install datasets")
        raise
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def sample_control_corpus(samples: List[str], target_count: int, seed: int) -> List[Dict[str, Any]]:
    """
    Randomly sample control corpus entries from the dataset.
    
    Args:
        samples: List of raw text samples
        target_count: Number of samples to collect
        seed: Random seed for reproducibility
        
    Returns:
        List of dictionaries containing sample metadata and text
    """
    random.seed(seed)
    
    if len(samples) < target_count:
        logger.warning(f"Dataset has only {len(samples)} samples, sampling all available")
        target_count = len(samples)
    
    # Randomly select indices
    selected_indices = random.sample(range(len(samples)), target_count)
    
    control_samples = []
    for idx in selected_indices:
        sample_text = samples[idx]
        control_samples.append({
            "id": f"control_{idx:04d}",
            "source": DATASET_NAME,
            "text": sample_text,
            "sampling_seed": seed,
            "type": "control"
        })
    
    logger.info(f"Sampled {len(control_samples)} control samples")
    return control_samples

def save_control_corpus(samples: List[Dict[str, Any]], output_path: Path):
    """
    Save the control corpus to a JSON file.
    
    Args:
        samples: List of control sample dictionaries
        output_path: Path to save the JSON file
    """
    ensure_dir(output_path.parent)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(samples)} control samples to {output_path}")

@retry_on_failure(max_attempts=3, delay=2.0)
def generate_control_corpus():
    """
    Main function to generate the control corpus.
    
    This function:
    1. Loads the arxiv_nlp dataset
    2. Randomly samples ≥80 control entries
    3. Saves them to data/raw/control_corpus.json
    
    The resulting samples are structured identically to phenomenological
    reports so they can be processed through the same validity metrics.
    """
    config = get_config()
    output_dir = Path(config["paths"]["raw_data"])
    output_file = output_dir / "control_corpus.json"
    
    logger.info("Starting control corpus generation")
    
    # Load dataset
    raw_samples = load_control_dataset()
    
    # Sample control corpus
    control_samples = sample_control_corpus(
        raw_samples, 
        TARGET_SAMPLE_COUNT, 
        RANDOM_SEED
    )
    
    # Save to disk
    save_control_corpus(control_samples, output_file)
    
    logger.info(f"Control corpus generation complete: {len(control_samples)} samples saved")
    
    return {
        "output_file": str(output_file),
        "sample_count": len(control_samples),
        "source": DATASET_NAME,
        "seed": RANDOM_SEED
    }

def main():
    """Entry point for script execution."""
    logger.info("=" * 60)
    logger.info("Control Corpus Generation Pipeline")
    logger.info("=" * 60)
    
    try:
        result = generate_control_corpus()
        logger.info("Success!")
        logger.info(f"Output: {result['output_file']}")
        logger.info(f"Samples generated: {result['sample_count']}")
    except Exception as e:
        logger.error(f"Control corpus generation failed: {e}")
        raise

if __name__ == "__main__":
    main()