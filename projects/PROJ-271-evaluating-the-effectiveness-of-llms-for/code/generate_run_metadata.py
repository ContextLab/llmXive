"""
Generate run metadata for reproducibility (T052).

This script captures:
- Environment hash (pip freeze)
- Dataset version commit ID (from codeparrot/github-code)
- Random seed used for sampling (from config)
"""

import os
import json
import subprocess
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from config import get_results_path, setup_logging
from data_pipeline import load_sampled_functions

# Setup logging
logger = setup_logging("generate_run_metadata")

def get_environment_hash() -> str:
    """Get hash of current pip environment."""
    try:
        result = subprocess.run(
            ["pip", "freeze"],
            capture_output=True,
            text=True,
            check=True
        )
        # Create hash of the frozen requirements
        return hashlib.sha256(result.stdout.encode()).hexdigest()[:16]
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get pip freeze: {e}")
        raise

def get_dataset_commit_id() -> Optional[str]:
    """Get the commit ID of the codeparrot/github-code dataset."""
    try:
        from datasets import load_dataset
        # Load the dataset in streaming mode to get info without downloading
        dataset = load_dataset(
            "codeparrot/github-code",
            split="train",
            streaming=True
        )
        # Get the dataset info which includes the revision/commit
        info = dataset.info
        if hasattr(info, 'dataset_name'):
            # Try to get the revision from the dataset builder
            # This might require checking the dataset card or builder config
            pass
        
        # Alternative: Try to get from the dataset's features or builder
        # For HuggingFace datasets, we can try to access the builder's revision
        if hasattr(dataset, '_builder'):
            builder = dataset._builder
            if hasattr(builder, 'config'):
                if hasattr(builder.config, 'data_files'):
                    # For some datasets, the revision is stored in the config
                    pass
        
        # Fallback: Try to get from the dataset's cached info
        # This is a bit hacky but works for many HF datasets
        try:
            from huggingface_hub import HfApi
            api = HfApi()
            dataset_info = api.dataset_info("codeparrot/github-code")
            return dataset_info.sha if hasattr(dataset_info, 'sha') else None
        except Exception as e:
            logger.warning(f"Could not get dataset info from HfApi: {e}")
            return None
        
        return None
    except Exception as e:
        logger.error(f"Failed to get dataset commit ID: {e}")
        return None

def get_random_seed() -> int:
    """Get the random seed used for sampling (from config)."""
    # Import the seed from config - assuming it's set there
    # If not, we'll use a default and log a warning
    try:
        from config import RANDOM_SEED
        return RANDOM_SEED
    except ImportError:
        logger.warning("RANDOM_SEED not found in config, using default 42")
        return 42

def generate_run_metadata() -> Dict[str, Any]:
    """Generate the run metadata dictionary."""
    logger.info("Generating run metadata...")
    
    metadata = {
        "environment_hash": get_environment_hash(),
        "dataset_commit_id": get_dataset_commit_id(),
        "random_seed": get_random_seed(),
        "generated_at": subprocess.run(
            ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
            capture_output=True,
            text=True,
            check=True
        ).stdout.strip()
    }
    
    logger.info(f"Environment hash: {metadata['environment_hash']}")
    logger.info(f"Dataset commit ID: {metadata['dataset_commit_id']}")
    logger.info(f"Random seed: {metadata['random_seed']}")
    
    return metadata

def save_metadata(metadata: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """Save metadata to JSON file."""
    if output_path is None:
        output_path = os.path.join(get_results_path(), "run_metadata.json")
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Metadata saved to {output_path}")
    return output_path

def main():
    """Main entry point."""
    logger.info("Starting run metadata generation...")
    
    try:
        metadata = generate_run_metadata()
        output_path = save_metadata(metadata)
        logger.info(f"Successfully generated run metadata: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate run metadata: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
