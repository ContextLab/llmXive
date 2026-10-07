"""
Crystallography Open Database (COD) Organic Subset Loader.
Streams the dataset from HuggingFace.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Iterator, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from datasets import load_dataset
from config import get_path_raw_data, ensure_directory
from logging_config import setup_logging, get_logger
from exceptions import SourceUnreachableError, DownloadError

setup_logging(level=logging.INFO)
logger = get_logger("load_cod")

def stream_cod_organic(output_path: str, sample_size: int = None) -> None:
    """
    Streams the COD organic dataset from HuggingFace and saves it to a Parquet file.
    
    Args:
        output_path: Path to the output Parquet file.
        sample_size: Optional number of rows to sample.
    """
    logger.info("Starting stream of COD organic dataset...")
    
    try:
        # Load the dataset with streaming
        # The dataset name is 'crystallography-open-database/organic' as per spec
        dataset = load_dataset(
            "crystallography-open-database/organic",
            split="train",
            streaming=True
        )
        
        if sample_size:
            logger.info(f"Sampling {sample_size} rows from the stream.")
            dataset = dataset.take(sample_size)
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        ensure_directory(str(output_dir))
        
        # Convert to pandas and save (streaming to parquet directly is complex, 
        # so we buffer in chunks or convert to DF if memory allows for the sample)
        # For a full stream, we would iterate and append. 
        # For this task, we assume a manageable sample or the full stream fits in memory if not too large.
        # Given the <500MB constraint in spec, we can likely load the whole thing if it's the organic subset.
        
        logger.info("Converting stream to DataFrame...")
        df = dataset.to_pandas()
        
        logger.info(f"Saving {len(df)} rows to {output_path}")
        df.to_parquet(output_path, index=False)
        
        logger.info("Stream completed and saved successfully.")
        
    except Exception as e:
        logger.error(f"Failed to stream dataset: {e}")
        raise SourceUnreachableError(f"Could not access COD organic dataset: {e}")

def main():
    parser = argparse.ArgumentParser(description="Stream COD Organic Dataset")
    parser.add_argument("--output", type=str, default=None, help="Output path for the Parquet file.")
    parser.add_argument("--sample", type=int, default=None, help="Number of rows to sample.")
    args = parser.parse_args()

    output_path = args.output if args.output else str(get_path_raw_data() / "cod_organic_subset.parquet")
    
    stream_cod_organic(output_path, sample_size=args.sample)

if __name__ == "__main__":
    main()
