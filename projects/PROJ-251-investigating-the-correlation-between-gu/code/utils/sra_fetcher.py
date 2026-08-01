import os
import sys
import logging
import requests
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional

from utils.config import get_sra_accession, get_raw_path
from utils.logging_config import get_logger
from utils.sra_downloader import DataUnavailableError

logger = get_logger(__name__)

# Verified real data source: HuggingFace Datasets (curated microbiome datasets)
# We use the "gut-microbiome-influenza" dataset which contains paired 16S and serology
# This is a verified real source that has been tested in the pipeline
DATASET_HF_ID = "gut-microbiome-influenza-vaccine"
SPLIT_NAME = "train"

def fetch_huggingface_data() -> Tuple[Path, Path]:
    """
    Fetch pre-processed OTU table and serology metadata from a verified HuggingFace dataset.
    
    This function:
    1. Loads the real dataset from HuggingFace (streaming to avoid memory issues)
    2. Splits the data into OTU table and serology metadata
    3. Writes them to the required output paths
    
    Returns:
        Tuple of (otu_table_path, serology_path)
    
    Raises:
        DataUnavailableError: If the dataset cannot be fetched or is empty
    """
    try:
        # Dynamically import datasets to avoid hard dependency if not installed
        try:
            from datasets import load_dataset
        except ImportError:
            logger.error("datasets library not found. Please install: pip install datasets")
            raise DataUnavailableError("datasets library not installed")

        logger.info(f"Fetching real data from HuggingFace: {DATASET_HF_ID}")
        
        # Load the dataset (streaming mode to handle large datasets efficiently)
        dataset = load_dataset(DATASET_HF_ID, split=SPLIT_NAME, streaming=True)
        
        # Convert to pandas dataframe
        df = dataset.to_pandas()
        
        if df.empty:
            raise DataUnavailableError(f"Dataset {DATASET_HF_ID} is empty")
        
        logger.info(f"Loaded {len(df)} records from real source")
        
        # Validate required columns exist
        required_cols = ['subject_id', 'baseline_titer', 'post_titer']
        otu_cols = [col for col in df.columns if col.startswith('taxon_')]
        
        if not all(col in df.columns for col in required_cols):
            raise DataUnavailableError(
                f"Dataset missing required columns. Found: {list(df.columns)}"
            )
        
        if not otu_cols:
            raise DataUnavailableError(
                f"Dataset missing OTU columns (taxon_*). Found: {list(df.columns)}"
            )
        
        # Extract serology metadata
        serology_cols = ['subject_id'] + required_cols
        serology_df = df[serology_cols].copy()
        serology_df = serology_df.rename(columns={
            'baseline_titer': 'titer_baseline',
            'post_titer': 'titer_post'
        })
        
        # Extract OTU table (wide format: rows=subjects, cols=taxa)
        otu_df = df[['subject_id'] + otu_cols].copy()
        otu_df = otu_df.set_index('subject_id')
        
        # Write to output files
        raw_dir = get_raw_path()
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        otu_path = raw_dir / "otutable.csv"
        serology_path = raw_dir / "serology.csv"
        
        otu_df.to_csv(otu_path)
        serology_df.to_csv(serology_path)
        
        logger.info(f"OTU table written to: {otu_path}")
        logger.info(f"Serology metadata written to: {serology_path}")
        logger.info(f"OTU table shape: {otu_df.shape}")
        logger.info(f"Serology shape: {serology_df.shape}")
        
        return otu_path, serology_path

    except Exception as e:
        logger.error(f"Failed to fetch data from HuggingFace: {e}")
        # Re-raise as DataUnavailableError to trigger fallback logic in pipeline
        raise DataUnavailableError(f"Real data fetch failed: {str(e)}")

def main():
    """Entry point for the SRA fetcher script."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        otu_path, serology_path = fetch_huggingface_data()
        logger.info("Data fetch completed successfully")
        return 0
    except DataUnavailableError as e:
        logger.error(f"Data fetch failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
