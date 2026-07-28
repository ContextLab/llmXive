"""
Synthetic Dataset Generator for PerceptionDLM Overflow Study.

Orchestrates the generation of synthetic images with varying region counts
(20, 25, 30, 35, 40, 45, 50) using the ParaDLC-Bench dataset.
Ensures JSON annotation files with coordinates and derived relations are saved.
"""

import os
import sys
import json
import random
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Local imports matching API surface
from config import get_data_path, ensure_directories
from synthetic.fetcher import fetch_dataset_sample
from synthetic.placer import place_boxes_with_retry
from synthetic.deriver import derive_all_relations
from synthetic.validator import validate_no_overlaps
from synthetic.serializer import save_image, save_annotations, serialize_synthetic_sample

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
REGION_COUNTS = [20, 25, 30, 35, 40, 45, 50]
SAMPLES_PER_BIN = 50
RANDOM_SEED = 42

def generate_sample_for_bin(
    image_data: Any,
    target_regions: int,
    image_id: int,
    bin_id: int
) -> Optional[Dict[str, Any]]:
    """
    Generate a single synthetic sample for a specific region count bin.

    Args:
        image_data: The source image data (PIL Image or similar).
        target_regions: The number of regions to place.
        image_id: Unique identifier for the generated sample.
        bin_id: The region count bin this sample belongs to.

    Returns:
        A dictionary containing the image path, annotation path, and metadata,
        or None if generation fails (e.g., placement retries exhausted).
    """
    logger.info(f"Generating sample {image_id} for bin {target_regions} regions...")
    start_time = time.perf_counter()

    try:
        # 1. Place boxes with retry logic (handled in placer.py)
        # Returns list of boxes: [{'x': x, 'y': y, 'w': w, 'h': h, 'label': 'obj'}]
        boxes = place_boxes_with_retry(image_data, target_regions)

        if not boxes:
            logger.warning(f"Failed to place {target_regions} boxes for image {image_id}. Skipping.")
            return None

        # 2. Validate no overlaps (double check)
        if not validate_no_overlaps(boxes):
            logger.error(f"Validation failed: Overlaps detected in generated boxes for {image_id}.")
            return None

        # 3. Derive ground-truth spatial relations
        # Returns list of relations: [{'subject': ..., 'relation': ..., 'object': ...}]
        relations = derive_all_relations(boxes)

        # 4. Prepare annotation data
        annotations = {
            "image_id": image_id,
            "bin_regions": target_regions,
            "boxes": boxes,
            "relations": relations,
            "metadata": {
                "generation_time_sec": time.perf_counter() - start_time,
                "source_image_id": image_id, # Placeholder for actual source ID
                "seed": RANDOM_SEED
            }
        }

        # 5. Serialize (Save Image and JSON)
        # This function handles writing to disk
        result = serialize_synthetic_sample(
            image_data,
            annotations,
            image_id,
            bin_id
        )

        if result:
            logger.info(f"Successfully saved sample {image_id} (Bin: {target_regions}, Relations: {len(relations)})")
            return result
        else:
            logger.error(f"Serialization failed for image {image_id}.")
            return None

    except Exception as e:
        logger.exception(f"Unexpected error during generation of {image_id}: {e}")
        return None

def run_generation_pipeline():
    """
    Orchestrates the full generation pipeline across all region count bins.
    Fetches data, generates samples, and saves JSON annotations with coordinates.
    """
    logger.info("Starting Synthetic Generation Pipeline...")
    ensure_directories()

    data_path = get_data_path("synthetic")
    logger.info(f"Output directory: {data_path}")

    # Fetch a sample of the source dataset (ParaDLC-Bench via COCO-Stuff)
    # We need enough images to cover SAMPLES_PER_BIN * len(REGION_COUNTS)
    # With retry logic, we might need more source images.
    total_needed = SAMPLES_PER_BIN * len(REGION_COUNTS)
    logger.info(f"Fetching {total_needed} source images from dataset...")

    source_images = list(fetch_dataset_sample(total_needed * 2)) # Fetch extra for retries
    random.shuffle(source_images)

    if len(source_images) < total_needed:
        logger.error(f"Insufficient source images fetched. Needed {total_needed}, got {len(source_images)}.")
        # In a real scenario, we might raise an error or try to fetch more
        # For this task, we proceed with what we have, but log the limitation.

    generated_count = 0
    failed_count = 0

    image_id_counter = 0
    for bin_regions in REGION_COUNTS:
        logger.info(f"--- Processing Bin: {bin_regions} regions ---")
        bin_success = 0
        attempts = 0

        while bin_success < SAMPLES_PER_BIN and attempts < len(source_images):
            source_img = source_images[attempts]
            attempts += 1

            result = generate_sample_for_bin(
                image_data=source_img,
                target_regions=bin_regions,
                image_id=image_id_counter,
                bin_id=bin_regions
            )

            if result:
                generated_count += 1
                bin_success += 1
                image_id_counter += 1
            else:
                failed_count += 1
                image_id_counter += 1 # Still increment ID to keep unique

            # Safety break if we run out of source images
            if attempts >= len(source_images) and bin_success < SAMPLES_PER_BIN:
                logger.warning(f"Ran out of source images for bin {bin_regions}. Stopping.")
                break

        logger.info(f"Bin {bin_regions}: Generated {bin_success}/{SAMPLES_PER_BIN} samples.")

    logger.info(f"Pipeline Complete. Total Generated: {generated_count}, Total Failed: {failed_count}")
    return generated_count, failed_count

def main():
    """Entry point for the generator script."""
    try:
        count, failures = run_generation_pipeline()
        if failures > 0:
            logger.warning(f"Pipeline finished with {failures} failures.")
        else:
            logger.info("Pipeline finished successfully.")
    except Exception as e:
        logger.exception(f"Fatal error in main pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()