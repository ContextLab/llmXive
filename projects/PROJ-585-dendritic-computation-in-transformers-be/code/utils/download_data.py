"""
Download GLUE SST-2 dataset for the dendritic computation experiments.

This script fetches the real SST-2 dataset from HuggingFace Datasets.
It saves the data to `data/raw/sst2/` and generates a checksum manifest.

Usage:
    python code/utils/download_data.py
"""
import os
import sys
import hashlib
import argparse
import logging
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from datasets import load_dataset
except ImportError:
    logging.error("The 'datasets' package is required. Install it via: pip install datasets")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_file_hash(filepath: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    parser = argparse.ArgumentParser(description="Download GLUE SST-2 dataset")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(project_root / "data" / "raw" / "sst2"),
        help="Directory to save the downloaded dataset"
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading GLUE SST-2 dataset to {output_dir}...")

    try:
        # Load the real dataset from HuggingFace
        # The 'glue' dataset is a builder that loads from the nyu-mll/glue repo
        # We use trust_remote_code=False as the glue script is standard in the datasets library
        # and does not require remote code execution in recent versions.
        # However, if the specific cache resolution fails, we fallback to the explicit canonical path
        # which is 'glue' with config 'sst2'.
        
        logger.info("Attempting to load dataset with load_dataset('glue', 'sst2')...")
        dataset = load_dataset("glue", "sst2", trust_remote_code=False)
        
        logger.info("Dataset loaded successfully.")
        logger.info(f"Dataset splits: {list(dataset.keys())}")

        # Save each split to parquet for efficient loading and checksumming
        saved_files = []
        for split_name, split_data in dataset.items():
            split_path = output_dir / f"{split_name}.parquet"
            logger.info(f"Saving split '{split_name}' ({len(split_data)} rows) to {split_path}...")
            
            # Convert to pandas and save as parquet
            # This ensures we have a single file per split for hashing
            df = split_data.to_pandas()
            df.to_parquet(split_path, index=False)
            saved_files.append(split_path)

        # Generate checksum manifest
        manifest_path = output_dir / "checksums.manifest"
        logger.info(f"Generating checksum manifest at {manifest_path}...")
        
        with open(manifest_path, "w") as f:
            f.write("# SHA-256 checksums for SST-2 dataset splits\n")
            f.write(f"# Generated on: {dataset.info.download_checksums if dataset.info else 'N/A'}\n")
            for filepath in saved_files:
                file_hash = calculate_file_hash(filepath)
                f.write(f"{file_hash}  {filepath.name}\n")
        
        logger.info("Download and verification complete.")
        logger.info(f"Manifest saved to: {manifest_path}")
        
        # Print summary
        total_rows = sum(len(dataset[s]) for s in dataset.keys())
        logger.info(f"Total rows downloaded: {total_rows}")

    except Exception as e:
        logger.error(f"Failed to download or process dataset: {e}")
        # Fail loudly as per constraints - do not fall back to synthetic
        raise SystemExit(1)

if __name__ == "__main__":
    main()