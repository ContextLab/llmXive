import os
import sys
import pandas as pd
from datasets import load_dataset
import hashlib
import logging
from pathlib import Path
from typing import Optional

# Ensure imports work relative to project root if run as script
if __name__ == '__main__' and 'code' not in sys.path[0]:
    sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

# Verified sources as per project constraints
PRIMARY_SOURCE = "deepchem/delaney-processed" # HuggingFace dataset ID
# Note: The original S3 URL is deprecated/unreliable. We rely on HF mirror.
# If HF fails, we must fail loudly.

def fetch_esol_dataset(output_dir: str) -> pd.DataFrame:
    """
    Fetches the ESOL dataset from a verified real source.
    Fails loudly if the source is unreachable. No synthetic fallbacks.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    csv_path = output_path / "delaney-processed.csv"

    if csv_path.exists():
        logger.info(f"Found existing raw CSV at {csv_path}")
        return pd.read_csv(csv_path)

    logger.info(f"Fetching ESOL dataset from {PRIMARY_SOURCE}...")
    try:
        # Load from HuggingFace datasets (verified source)
        # This wraps the CSV download logic
        dataset = load_dataset(PRIMARY_SOURCE, split="train")
        
        # Convert to pandas
        df = dataset.to_pandas()
        
        # Validate required columns
        if "logS" not in df.columns:
            raise ValueError("Invalid dataset format: 'logS' column missing.")
        if "smiles" not in df.columns:
            # Some versions might use 'SMILES'
            if "SMILES" in df.columns:
                df = df.rename(columns={"SMILES": "smiles"})
            else:
                raise ValueError("Invalid dataset format: 'smiles' column missing.")

        # Save to disk
        df.to_csv(csv_path, index=False)
        logger.info(f"Successfully saved raw CSV to {csv_path}")
        return df

    except Exception as e:
        # CRITICAL: Fail loudly. No synthetic fallback.
        logger.error(f"Failed to fetch ESOL dataset from verified source: {e}")
        raise RuntimeError(f"CRITICAL: Could not fetch real data. Aborting. Source: {PRIMARY_SOURCE}") from e

def save_raw_csv(df: pd.DataFrame, output_path: str):
    """Saves the dataframe to a CSV file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved raw CSV to {output_path}")

def verify_checksum(file_path: str) -> str:
    """Computes SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """Main entry point for downloading ESOL dataset."""
    logging.basicConfig(level=logging.INFO)
    output_dir = os.environ.get("DATA_RAW_DIR", "data/raw")
    os.makedirs(output_dir, exist_ok=True)
    
    df = fetch_esol_dataset(output_dir)
    checksum = verify_checksum(os.path.join(output_dir, "delaney-processed.csv"))
    logger.info(f"Dataset checksum: {checksum}")

if __name__ == "__main__":
    main()
