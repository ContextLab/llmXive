import os
import sys
import logging
from pathlib import Path
from datasets import load_dataset
import pyarrow.parquet as pq

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_oqmd_dataset(output_path: str):
    """
    Downloads the OQMD Formation Energy dataset from HuggingFace and saves it as a Parquet file.
    
    Args:
        output_path: Path to save the parquet file.
    """
    logger.info("Starting download of OQMD Formation Energy dataset...")
    try:
        # Load dataset from HuggingFace
        # The dataset name is 'oqmd/formation-energy' as specified in the task.
        # We load the 'train' split. If the dataset is large, we stream it to avoid OOM,
        # then convert to pandas to save as parquet.
        ds = load_dataset("oqmd/formation-energy", split="train", streaming=True)
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert streaming dataset to pandas by iterating and collecting
        # Since streaming=True returns a generator of rows, we need to materialize it.
        # For large datasets, this might be memory intensive, but we need a parquet file.
        # We convert to list of dicts then to DataFrame.
        # Note: If the dataset is too large for RAM, this will fail, but the task requires
        # saving to parquet which implies materialization or chunked writing.
        # We assume the runner has enough memory for the full dataset or a representative slice
        # if the dataset is massive, but the requirement is to fetch the REAL data.
        
        # Convert to pandas DataFrame
        df = ds.to_pandas()
        
        # Save as parquet
        df.to_parquet(output_path, index=False)
        
        logger.info(f"Dataset saved successfully to {output_path}")
        logger.info(f"Dataset shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

def main():
    """Main entry point for downloading the dataset."""
    output_path = "data/raw/oqmd.parquet"
    download_oqmd_dataset(output_path)

if __name__ == "__main__":
    main()