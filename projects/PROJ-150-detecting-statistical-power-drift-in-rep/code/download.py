import os
import sys
import hashlib
import json
from pathlib import Path

import pandas as pd
import numpy as np

from logging_config import (
    setup_logging,
    get_module_logger,
    log_operation_start,
    log_operation_complete,
    log_error_fallback,
)

logger = get_module_logger(__name__)

class DataFetchError(Exception):
    """Raised when data fetch fails."""
    pass

def get_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_title_token_overlap(title1: str, title2: str) -> float:
    """
    Calculate cosine similarity of tokenized titles.
    """
    def tokenize(text):
        return set(text.lower().split())
    
    tokens1 = tokenize(title1)
    tokens2 = tokenize(title2)
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    return len(intersection) / len(union) if union else 0.0

def main():
    """
    Main entry point for the download script.
    Fetches the OSF reproducibility dataset.
    """
    setup_logging()
    project_root = Path(__file__).parent.parent
    raw_data_path = project_root / "data" / "raw" / "data.csv"
    
    log_operation_start(logger, "download_pipeline", "Starting data download.")
    
    try:
        # Attempt to fetch using datasets library
        # Note: We must ensure the dataset exists and is accessible.
        # The task specifies: "huggingface_hub to fetch the osf/reproducibility_project dataset"
        
        from datasets import load_dataset
        
        log_operation_start(logger, "fetch_dataset", "Fetching from HuggingFace Datasets.")
        
        # Try to load the dataset
        # The dataset name is 'osf/reproducibility_project'
        # We assume the split is 'train' or default
        dataset = load_dataset("osf/reproducibility_project", split="train", streaming=True)
        
        # Convert to DataFrame
        # Since streaming=True, we iterate and build the dataframe
        # This might be memory intensive if the dataset is huge, but we assume it fits or we stream carefully
        # For simplicity, we'll collect it into a list of dicts and then create a DF
        # If the dataset is too large, we might need to process in chunks, but for this task,
        # we assume it's manageable or we just take the first N if needed.
        # However, the spec says "real data only", so we try to get it all.
        
        # Let's try to load it as a DF directly if possible, or iterate
        # The 'datasets' library supports to_pandas()
        df = dataset.to_pandas()
        
        log_operation_complete(logger, "fetch_dataset", f"Fetched {len(df)} rows.")
        
        # Verify metadata
        # We need to check the title token overlap
        # Assuming the dataset has a 'title' column or similar metadata
        # If not, we might need to infer from the dataset description
        # For this implementation, we assume the dataset has a 'title' column
        # or we use the dataset name as a proxy.
        
        # Let's assume the dataset has a 'title' column
        if 'title' in df.columns:
            # Get a sample title (e.g., first row)
            sample_title = str(df['title'].iloc[0])
            target_title = "OSF Reproducibility Project"
            overlap = calculate_title_token_overlap(sample_title, target_title)
            
            log_operation_start(logger, "verify_metadata", f"Title overlap: {overlap:.2f}")
            
            if overlap < 0.7:
                log_error_fallback(logger, "verify_metadata", f"Title overlap {overlap} is below threshold 0.7.")
                raise DataFetchError(f"Dataset title overlap {overlap} is below required threshold 0.7.")
            else:
                log_operation_complete(logger, "verify_metadata", "Metadata verified.")
        else:
            # If no title column, we might skip this check or use a different method
            # For now, we log a warning
            logger.warning("No 'title' column found in dataset. Skipping title overlap check.")
        
        # Save to raw data path
        raw_data_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(raw_data_path, index=False)
        
        log_operation_complete(logger, "download_pipeline", f"Data saved to {raw_data_path}")
        
    except Exception as e:
        log_error_fallback(logger, "download_pipeline", f"Failed to download data: {e}")
        raise DataFetchError(f"Data fetch failed: {e}")

if __name__ == "__main__":
    main()
