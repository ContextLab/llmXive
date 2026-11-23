import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Project logger
from utils.logging_config import get_logger

logger = get_logger(__name__)

def log_metadata_ambiguity(record_id: str, reason: str, stage: str = 'unknown') -> None:
    """
    Log metadata ambiguity events.
    """
    logger.warning(f"Metadata ambiguity in record {record_id} at stage {stage}: {reason}")

def run_pipeline() -> Dict[str, Any]:
    """
    Execute the full data ingestion pipeline:
    1. Download raw data from NCBI GEO/ProteomeXchange
    2. Normalize (filter low abundance, LCM imputation)
    3. Merge (UniProt -> Ensembl mapping)
    """
    logger.info("Starting full data ingestion pipeline...")

    # Step 1: Download
    from data_ingestion.download import run_download_pipeline
    try:
        downloaded_files = run_download_pipeline()
        logger.info(f"Downloaded {len(downloaded_files)} files.")
    except Exception as e:
        logger.error(f"Download step failed: {e}")
        raise

    # Step 2: Normalization
    from data_ingestion.normalize import run_normalization_pipeline
    try:
        normalized_df, norm_stats = run_normalization_pipeline()
        logger.info(f"Normalization completed. Stats: {norm_stats}")
    except Exception as e:
        logger.error(f"Normalization step failed: {e}")
        raise

    # Step 3: Merge
    from data_ingestion.merge import run_merge_pipeline
    try:
        merged_df = run_merge_pipeline()
        logger.info(f"Merged dataset shape: {merged_df.shape}")
    except Exception as e:
        logger.error(f"Merge step failed: {e}")
        raise

    summary = {
        "downloaded_files": [str(p) for p in downloaded_files],
        "normalization_stats": norm_stats,
        "merged_shape": merged_df.shape
    }
    logger.info("Data ingestion pipeline completed successfully.")
    return summary

def main():
    """
    Entry point for the pipeline script.
    """
    try:
        summary = run_pipeline()
        print(json.dumps(summary, indent=2))
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
