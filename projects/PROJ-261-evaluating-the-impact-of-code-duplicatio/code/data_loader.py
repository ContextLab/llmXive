"""
data_loader.py
---------------
Implements the data download pipeline for the codeparrot/github-code dataset.
This module streams a 500MB subset of the dataset and saves it to
``data/raw/github-code-sample.csv``. It handles the download, extraction, and
formatting required to produce a CSV file with columns: repo_name, file_path,
content. The implementation ensures the output file size matches the expected
~500MB by streaming the appropriate number of records from the Hugging Face
dataset repository.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

__all__ = ["download_and_save_sample"]


import os
import random
import string
from datasets import load_dataset


def download_and_save_sample(*args, **kwargs) -> None:
    """
    Download and save a 500MB sample of the codeparrot/github-code dataset.

    This function streams the codeparrot/github-code dataset from Hugging Face,
    processes a subset of records to create a CSV file with approximately 500MB
    of data. The output is saved to data/raw/github-code-sample.csv with columns:
    repo_name, file_path, content.

    The function:
    1. Loads a subset of the codeparrot/github-code dataset
    2. Streams records until approximately 500MB of content is accumulated
    3. Writes the data to a CSV file with the required columns
    4. Logs the final file size for verification
    """
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    target_size_bytes = 500 * 1024 * 1024  # 500MB
    output_file = raw_dir / "github-code-sample.csv"
    
    logger.info("Starting download of codeparrot/github-code dataset...")
    logger.info("Target size: ~500MB")
    
    try:
        # Load a subset of the dataset (using streaming to handle large datasets)
        # Filter for Python files to ensure valid content and reasonable size
        dataset = load_dataset(
            "codeparrot/github-code",
            split="train",
            streaming=True,
            trust_remote_code=True,
            filter=lambda x: x["language"] == "Python"
        )
        
        # Shuffle the dataset to get a representative sample
        dataset = dataset.shuffle(seed=42)
        
        with open(output_file, "w", encoding="utf-8") as f:
            # Write CSV header
            f.write("repo_name,file_path,content\n")
            
            total_size = 0
            record_count = 0
            
            for record in dataset:
                if total_size >= target_size_bytes:
                    break
                
                # Extract fields (adjust field names based on actual dataset schema)
                repo_name = record.get("repo", "unknown")
                file_path = record.get("path", "unknown")
                content = record.get("content", "")
                
                # Skip if content is empty
                if not content:
                    continue
                
                # Escape CSV fields properly
                repo_name = repo_name.replace('"', '""')
                file_path = file_path.replace('"', '""')
                content = content.replace('"', '""')
                
                # Write record
                f.write(f'"{repo_name}","{file_path}","{content}"\n')
                
                total_size += len(content.encode("utf-8"))
                record_count += 1
                
                if record_count % 1000 == 0:
                    logger.info(f"Processed {record_count} records, size: {total_size / 1024 / 1024:.1f}MB")
        
        logger.info(f"Download complete. Saved {record_count} records to {output_file}")
        logger.info(f"Final file size: {output_file.stat().st_size / 1024 / 1024:.1f}MB")
        
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

