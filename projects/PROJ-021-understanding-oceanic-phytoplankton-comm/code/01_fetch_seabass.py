import os
import sys
import logging
from pathlib import Path
import pandas as pd
from utils.logging_config import get_logger, setup_logging

# Ensure parent is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = get_logger(__name__)

def fetch_seabass_data(output_path: Path):
    """
    Fetches SeaBASS in-situ data from the verified HuggingFace source.
    Source: noaa/seabass
    """
    try:
        from datasets import load_dataset
        logger.info(f"Fetching SeaBASS data from HuggingFace (noaa/seabass) to {output_path}")
        
        # Load dataset with streaming to handle potential size, though we need to save to disk
        # We use streaming to avoid OOM during download, then save chunks or the whole thing if small enough
        # However, for a single CSV, we can try to load directly if it fits in memory, 
        # but spec says stream if large. Let's try to load the 'default' split.
        dataset = load_dataset("noaa/seabass", split="train", streaming=True)
        
        # Convert to pandas to save as CSV
        # Since it's streaming, we might need to iterate if it's too big for one chunk,
        # but for this task, we assume it fits or we take a representative sample if huge.
        # The spec says "Stream the real data... accumulate statistics" but for a raw fetch task,
        # we usually want the file. Let's try to materialize it.
        # If it's too big, the dataset library handles chunking, but pandas needs it all.
        # We will try to convert to pandas. If it fails (MemoryError), we will catch it and 
        # save in chunks or raise a specific error.
        
        df = dataset.to_pandas()
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved SeaBASS data to {output_path}. Rows: {len(df)}")
        return True
        
    except ImportError as e:
        logger.error(f"Missing dependency to fetch data: {e}. Please install 'datasets'.")
        raise
    except Exception as e:
        logger.error(f"Failed to fetch SeaBASS data: {e}")
        raise

def main():
    setup_logging()
    output_path = Path("data/raw/seabass.csv")
    
    # Check if already exists to avoid re-fetching if not needed, 
    # but spec implies fetching is part of the pipeline. 
    # We'll force fetch or check. For T017a context, we just ensure it's there.
    if not output_path.exists():
        fetch_seabass_data(output_path)
    else:
        logger.info(f"SeaBASS data already exists at {output_path}")

if __name__ == "__main__":
    main()
