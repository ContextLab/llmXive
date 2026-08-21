import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd
from datasets import load_dataset

from src.utils.io import set_global_seed, ensure_directory

# Configure logging
logger = logging.getLogger(__name__)

class DataUnavailableError(Exception):
    """Raised when required data (e.g., human_intensity_score) is missing from a dataset."""
    pass

def load_raw_text_corpus(dataset_id: str = "cmu/text_messages_v1", cache_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Fetches a real text message corpus and verifies the presence of 'human_intensity_score'.
    
    This function implements the "fail loud" policy:
    1. Attempts to load the specified dataset.
    2. Immediately checks for the 'human_intensity_score' column.
    3. If the column is missing, raises DataUnavailableError to halt the pipeline.
    4. If present, returns the DataFrame.
    
    Args:
        dataset_id: The HuggingFace dataset identifier.
        cache_dir: Optional directory for caching the dataset.
        
    Returns:
        pd.DataFrame: The loaded dataset containing text and intensity scores.
        
    Raises:
        DataUnavailableError: If 'human_intensity_score' is not found in the dataset.
        Exception: If the dataset cannot be fetched or is otherwise unavailable.
    """
    set_global_seed(42)
    
    logger.info(f"Attempting to load dataset: {dataset_id}")
    
    try:
        # Load the dataset from HuggingFace
        # We use streaming=False to ensure we get the full object for immediate column check
        # If the dataset is too large, the power analysis (T021) should have guided us,
        # but for the loader, we need to verify the schema exists.
        dataset = load_dataset(dataset_id, split="train", cache_dir=cache_dir)
        
        df = dataset.to_pandas()
        
        logger.info(f"Dataset loaded successfully. Shape: {df.shape}")
        logger.info(f"Available columns: {list(df.columns)}")
        
        # CRITICAL: Verify presence of human_intensity_score
        if "human_intensity_score" not in df.columns:
            logger.error(f"CRITICAL: 'human_intensity_score' column is MISSING in dataset '{dataset_id}'.")
            logger.error(f"Available columns: {list(df.columns)}")
            raise DataUnavailableError(
                f"DataUnavailableError: Required column 'human_intensity_score' not found in dataset '{dataset_id}'. "
                f"Available columns: {list(df.columns)}. Pipeline halted."
            )
        
        logger.info("Validation passed: 'human_intensity_score' is present.")
        
        # Ensure 'text' column exists as well, as it's fundamental for this project
        if "text" not in df.columns:
            # Attempt to find a similar column if 'text' is missing but intensity exists
            # This is a soft check; the schema validation later will catch hard mismatches.
            text_candidates = [c for c in df.columns if 'text' in c.lower() or 'message' in c.lower()]
            if text_candidates:
                logger.warning(f"Standard 'text' column not found. Found candidates: {text_candidates}. "
                             f"Assuming first candidate is text for now, but schema validation may fail later.")
            else:
                logger.warning("Standard 'text' column not found. Schema validation may fail later.")

        return df

    except DataUnavailableError:
        # Re-raise our custom error immediately
        raise
    except Exception as e:
        logger.error(f"Failed to load dataset '{dataset_id}': {str(e)}")
        raise

def main():
    """
    Entry point for testing the loader directly.
    Attempts to load the dataset and prints the result or error.
    """
    try:
        df = load_raw_text_corpus()
        print(f"SUCCESS: Loaded {len(df)} rows.")
        print(f"Columns: {list(df.columns)}")
        print(f"Sample intensity scores:\n{df['human_intensity_score'].describe()}")
    except DataUnavailableError as e:
        print(f"HALTED: {e}")
        # In a real pipeline, this would trigger T018 (Data Unavailable Report)
        # For this script, we just exit with a non-zero code to indicate failure
        import sys
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()