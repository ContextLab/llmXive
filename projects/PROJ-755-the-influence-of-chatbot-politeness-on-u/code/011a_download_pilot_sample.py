import os
import sys
import json
import logging
import random
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure the project root is in the path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datasets import load_dataset
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def ensure_directories(base_path: Path) -> None:
    """Create necessary directory structure if it doesn't exist."""
    dirs = [
        base_path / "data" / "raw" / "pilot_sample"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {d}")

def load_dataset_sample(
    dataset_name: str,
    split: str = "train",
    sample_size: int = 500,
    seed: int = 42
) -> pd.DataFrame:
    """
    Load a small, raw subset of the specified dataset for pilot analysis.
    
    Args:
        dataset_name: HuggingFace dataset identifier (e.g., 'HuggingFaceH4/hci_p2')
        split: Dataset split to load
        sample_size: Number of rows to sample
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame containing the sampled data
    
    Raises:
        RuntimeError: If the dataset cannot be loaded or is empty
    """
    logger.info(f"Loading dataset: {dataset_name}, split: {split}")
    
    try:
        # Load the dataset from HuggingFace
        dataset = load_dataset(dataset_name, split=split)
        
        if len(dataset) == 0:
            raise RuntimeError(f"Dataset {dataset_name} is empty")
        
        logger.info(f"Dataset loaded successfully. Total rows: {len(dataset)}")
        
        # Convert to pandas for easier sampling
        df = dataset.to_pandas()
        
        if len(df) == 0:
            raise RuntimeError(f"Converted DataFrame is empty")
        
        # Sample the data
        if len(df) <= sample_size:
            logger.warning(f"Dataset size ({len(df)}) is smaller than requested sample size ({sample_size}). Using all available data.")
            sampled_df = df.copy()
        else:
            sampled_df = df.sample(n=sample_size, random_state=seed).reset_index(drop=True)
        
        logger.info(f"Sampled {len(sampleed_df)} rows from {dataset_name}")
        return sampled_df
        
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise RuntimeError(f"Failed to load dataset {dataset_name}: {e}") from e

def save_raw_sample(df: pd.DataFrame, output_dir: Path, filename: str = "pilot_sample_raw.parquet") -> Path:
    """
    Save the raw sample to disk.
    
    Args:
        df: DataFrame to save
        output_dir: Directory to save the file
        filename: Name of the output file
    
    Returns:
        Path to the saved file
    """
    output_path = output_dir / filename
    
    logger.info(f"Saving raw sample to {output_path}")
    
    # Save as parquet
    df.to_parquet(output_path, index=False)
    
    # Verify the file was created and has content
    if not output_path.exists():
        raise RuntimeError(f"Failed to create output file: {output_path}")
    
    file_size = output_path.stat().st_size
    if file_size == 0:
        raise RuntimeError(f"Output file is empty: {output_path}")
    
    logger.info(f"Saved {len(df)} rows to {output_path} (Size: {file_size} bytes)")
    return output_path

def generate_manifest(
    output_dir: Path,
    dataset_name: str,
    sample_size: int,
    seed: int,
    total_rows: int,
    columns: list
) -> Path:
    """
    Generate a manifest file describing the pilot sample.
    
    Args:
        output_dir: Directory to save the manifest
        dataset_name: Source dataset name
        sample_size: Number of rows sampled
        seed: Random seed used
        total_rows: Total rows in the original dataset
        columns: List of column names
    
    Returns:
        Path to the manifest file
    """
    manifest = {
        "dataset_name": dataset_name,
        "sample_size": sample_size,
        "total_rows": total_rows,
        "seed": seed,
        "columns": columns,
        "created_at": pd.Timestamp.now().isoformat(),
        "description": "Raw pilot sample for initial analysis and MDE estimation"
    }
    
    manifest_path = output_dir / "manifest.json"
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Generated manifest: {manifest_path}")
    return manifest_path

def main():
    """
    Main entry point for T011a: Download Raw Sample for Pilot.
    
    This task downloads a small, raw subset of HCI_P2 for pilot analysis.
    It verifies T015a passed (HCI_P2 is valid) by attempting to load the dataset.
    """
    # Configuration
    DATASET_NAME = "HuggingFaceH4/hci_p2"
    SAMPLE_SIZE = 500
    SEED = 42
    SPLIT = "train"
    
    logger.info("=" * 60)
    logger.info("Starting T011a: Download Raw Sample for Pilot")
    logger.info("=" * 60)
    
    # Ensure output directories exist
    base_path = PROJECT_ROOT
    output_dir = base_path / "data" / "raw" / "pilot_sample"
    ensure_directories(output_dir)
    
    # Load the dataset sample
    try:
        df = load_dataset_sample(
            dataset_name=DATASET_NAME,
            split=SPLIT,
            sample_size=SAMPLE_SIZE,
            seed=SEED
        )
    except RuntimeError as e:
        logger.error(f"Task failed: {e}")
        sys.exit(1)
    
    # Verify required columns exist (basic sanity check)
    required_columns = ['quality_rating', 'user_id', 'dialogue_id']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logger.warning(f"Warning: Missing expected columns: {missing_columns}")
        logger.info("Proceeding anyway as this is a pilot sample for exploration")
    
    # Save the raw sample
    try:
        saved_path = save_raw_sample(df, output_dir)
    except RuntimeError as e:
        logger.error(f"Failed to save sample: {e}")
        sys.exit(1)
    
    # Generate manifest
    try:
        generate_manifest(
            output_dir=output_dir,
            dataset_name=DATASET_NAME,
            sample_size=len(df),
            seed=SEED,
            total_rows=len(df) * (len(df) // SAMPLE_SIZE) if len(df) > SAMPLE_SIZE else len(df),
            columns=list(df.columns)
        )
    except Exception as e:
        logger.error(f"Failed to generate manifest: {e}")
        # Non-fatal, but log the error
    
    # Final verification
    logger.info("=" * 60)
    logger.info("T011a COMPLETED SUCCESSFULLY")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Files created:")
    for f in output_dir.iterdir():
        logger.info(f"  - {f.name} ({f.stat().st_size} bytes)")
    
    # Verify file count and size
    file_count = sum(1 for _ in output_dir.iterdir())
    total_size = sum(f.stat().st_size for f in output_dir.iterdir() if f.is_file())
    
    if file_count == 0:
        logger.error("VERIFICATION FAILED: No files created in output directory")
        sys.exit(1)
    
    if total_size == 0:
        logger.error("VERIFICATION FAILED: Total file size is 0")
        sys.exit(1)
    
    logger.info(f"Verification passed: {file_count} files, {total_size} bytes total")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
