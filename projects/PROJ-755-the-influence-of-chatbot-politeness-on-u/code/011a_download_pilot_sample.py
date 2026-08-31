"""
T011a: Download Raw Sample for Pilot
Downloads a small, raw subset of the HCI_P2 dataset from HuggingFace for pilot analysis.
Saves the raw sample to data/raw/pilot_sample/ without filtering or transformation.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATASET_ID = "HuggingFaceH4/hci_p2"
PILOT_SAMPLE_SIZE = 500  # Small representative subset
FIXED_SEED = 42
OUTPUT_DIR = Path("data/raw/pilot_sample")

def ensure_directories() -> Path:
    """Ensure the output directory exists."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured output directory exists: {OUTPUT_DIR}")
    return OUTPUT_DIR

def load_dataset_sample() -> Optional[Any]:
    """
    Load a sample from the HCI_P2 dataset.
    Uses the `datasets` library to fetch a small subset with a fixed seed.
    """
    try:
        from datasets import load_dataset
        logger.info(f"Attempting to load dataset: {DATASET_ID}")
        
        # Load the full dataset in streaming mode to avoid memory issues initially
        # Then take a sample. Since we need a fixed seed sample, we load with trust_remote_code if needed
        dataset = load_dataset(
            DATASET_ID, 
            split="train", 
            trust_remote_code=True,
            streaming=False
        )
        
        logger.info(f"Dataset loaded successfully. Total size: {len(dataset)} rows")
        
        # Take a sample with a fixed seed
        sample = dataset.shuffle(seed=FIXED_SEED).select(range(min(PILOT_SAMPLE_SIZE, len(dataset))))
        logger.info(f"Sampled {len(sample)} rows with seed {FIXED_SEED}")
        
        return sample
    except ImportError:
        logger.error("The 'datasets' library is not installed. Please install it via 'pip install datasets'.")
        raise
    except Exception as e:
        logger.error(f"Failed to load dataset {DATASET_ID}: {e}")
        raise

def save_raw_sample(sample: Any, output_dir: Path) -> None:
    """
    Save the raw sample to the output directory.
    Saves as a parquet file for efficient storage and reading.
    """
    output_file = output_dir / "pilot_sample.parquet"
    try:
        sample.to_parquet(str(output_file))
        logger.info(f"Raw sample saved to: {output_file}")
    except Exception as e:
        logger.error(f"Failed to save sample to parquet: {e}")
        raise

def generate_manifest(output_dir: Path, sample_size: int) -> None:
    """
    Generate a manifest file describing the pilot sample.
    """
    manifest = {
        "source_dataset": DATASET_ID,
        "sample_size": sample_size,
        "fixed_seed": FIXED_SEED,
        "output_file": str(output_dir / "pilot_sample.parquet"),
        "description": "Raw pilot sample for T011a. No filtering or schema transformation applied.",
        "timestamp": None  # Can be added if needed, but keeping it simple
    }
    
    manifest_file = output_dir / "manifest.json"
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest generated at: {manifest_file}")

def main() -> None:
    """Main execution function for T011a."""
    logger.info("Starting T011a: Download Raw Sample for Pilot")
    
    # 1. Ensure directories
    output_dir = ensure_directories()
    
    # 2. Load dataset sample
    sample = load_dataset_sample()
    
    # 3. Save raw sample
    save_raw_sample(sample, output_dir)
    
    # 4. Generate manifest
    generate_manifest(output_dir, len(sample))
    
    logger.info("T011a completed successfully.")

if __name__ == "__main__":
    main()
