import logging
import sys
from pathlib import Path
from datasets import load_dataset
from llmxive_toolkit import paths

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

def main():
    """
    Download MS-COCO 2017 validation captions using the datasets library
    and save them as a parquet file.
    """
    output_path = paths.data("raw", "coco_captions.parquet")
    
    try:
        log.info(f"Loading MS-COCO 2017 validation captions from HuggingFace...")
        # Load the validation split of the coco_captions dataset
        dataset = load_dataset("nlpconnect/coco_captions", split="validation", streaming=False)
        
        log.info(f"Saving dataset to {output_path}...")
        dataset.to_parquet(str(output_path))
        
        log.info("Successfully downloaded and saved COCO validation captions.")
    except Exception as e:
        # Fail loudly as per constraints
        raise RuntimeError(f"Failed to fetch COCO validation dataset: {e}") from e

if __name__ == "__main__":
    main()
