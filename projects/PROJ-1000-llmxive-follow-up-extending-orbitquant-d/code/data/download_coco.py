"""
Download and cache the MS-COCO 2017 Validation dataset using streaming.

This script fetches the 'mscoco' dataset from HuggingFace Datasets,
specifically the '2017' split, which includes both images and captions.
It uses the `datasets` library with `streaming=True` to process the data
in chunks without loading the entire ~8GB dataset into RAM, ensuring
memory usage stays below 2GB.

The script processes the stream to generate a lightweight metadata file
containing prompt captions and image IDs, which are then saved to the
processed data directory. This allows downstream tasks to iterate over
the data without re-downloading, while the raw images remain streamed
from the source when needed.

Output:
    Creates `data/processed/coco_prompts_streaming.csv` containing
    columns [id, caption] derived from the streamed dataset.
    Also saves a small metadata summary to `data/raw/coco_2017_val_streaming_meta.json`.
"""
import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import Iterator, Dict, Any

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def stream_coco_prompts(
    dataset_name: str = "mscoco",
    dataset_config: str = "2017",
    dataset_split: str = "validation"
) -> Iterator[Dict[str, Any]]:
    """
    Stream the MS-COCO dataset from HuggingFace.

    Yields:
        Dictionary containing 'id' and 'caption' for each sample.
    """
    try:
        from datasets import load_dataset
    except ImportError:
        raise ImportError(
            "The 'datasets' library is required. Install it via: "
            "pip install datasets"
        )

    logger.info(f"Loading dataset: {dataset_name} ({dataset_config}) - {dataset_split} (streaming)...")

    try:
        # Use streaming=True to avoid loading full dataset into memory
        ds = load_dataset(
            dataset_name,
            dataset_config,
            split=dataset_split,
            streaming=True,
            trust_remote_code=False
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load MS-COCO dataset in streaming mode: {e}")

    # Iterate and yield formatted records
    # Note: In 'mscoco' dataset, captions are often in a list.
    # We take the first caption for simplicity, or join if needed.
    for idx, item in enumerate(ds):
        # Handle different potential structures of the dataset
        # Typically: item['annotations'] is a list of dicts with 'caption'
        # Or item['caption'] exists directly depending on the specific HF module version
        caption = None
        if 'caption' in item:
            caption = item['caption']
        elif 'annotations' in item and isinstance(item['annotations'], list) and len(item['annotations']) > 0:
            caption = item['annotations'][0].get('caption')
        elif 'image_caption' in item:
            caption = item['image_caption']

        if caption is None:
            logger.warning(f"Skipping sample {idx}: No caption found.")
            continue

        # Ensure caption is a string
        if not isinstance(caption, str):
            caption = str(caption)

        yield {
            "id": item.get('id', idx),
            "caption": caption
        }

def main():
    config = Config()
    
    # Ensure directories exist
    data_raw_path = config.data_raw_path
    data_processed_path = config.data_processed_path
    
    data_raw_path.mkdir(parents=True, exist_ok=True)
    data_processed_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting MS-COCO streaming download process...")
    logger.info(f"Raw data path: {data_raw_path}")
    logger.info(f"Processed data path: {data_processed_path}")

    # Output file for processed prompts (CSV)
    output_csv = data_processed_path / "coco_prompts_streaming.csv"
    meta_file = data_raw_path / "coco_2017_val_streaming_meta.json"

    logger.info(f"Streaming data and writing to {output_csv}...")

    count = 0
    try:
        with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["id", "caption"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for record in stream_coco_prompts():
                writer.writerow(record)
                count += 1
                
                # Log progress every 1000 samples
                if count % 1000 == 0:
                    logger.info(f"Processed {count} samples...")

        logger.info(f"Successfully streamed and saved {count} samples to {output_csv}")

        # Save metadata
        metadata = {
            "dataset": "mscoco",
            "config": "2017",
            "split": "validation",
            "mode": "streaming",
            "num_samples": count,
            "output_csv": str(output_csv),
            "timestamp": str(Path(__file__).stat().st_mtime)
        }
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved to {meta_file}")

    except Exception as e:
        logger.error(f"Error during streaming process: {e}")
        # Clean up partial file if it exists
        if output_csv.exists():
            output_csv.unlink()
        raise RuntimeError(f"Failed to stream MS-COCO dataset: {e}")

    logger.info("MS-COCO streaming download and processing complete.")

if __name__ == "__main__":
    main()
