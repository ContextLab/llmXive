"""
Synthetic Dataset Generator for PerceptionDLM Overflow Experiment.

Orchestrates the generation of synthetic images with varying region counts (25-50).
Uses real data from HuggingFace (coco/coco-stuff-164k) and ensures non-overlapping
bounding boxes with derived geometric relations.
"""
import os
import sys
import json
import random
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_data_path, get_random_state, ensure_directories
from synthetic.fetcher import fetch_dataset_sample
from synthetic.placer import place_boxes_with_retry
from synthetic.deriver import derive_all_relations
from synthetic.validator import validate_no_overlaps, validate_synthetic_image_file
from synthetic.serializer import serialize_synthetic_sample
from contracts.validator import validate_synthetic_image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Region count bins as per config
REGION_COUNTS = [25, 30, 35, 40, 45, 50]
SAMPLES_PER_BIN = 50  # Minimum samples per bin

def generate_sample_for_bin(
    bin_count: int,
    source_dataset: Any,
    output_dir: Path,
    start_idx: int = 0
) -> Dict[str, Any]:
    """
    Generate synthetic samples for a specific region count bin.

    Args:
        bin_count: Target number of regions (25, 30, ..., 50)
        source_dataset: HuggingFace dataset iterator
        output_dir: Directory to save generated files
        start_idx: Starting index in the dataset

    Returns:
        Dictionary with generation statistics
    """
    stats = {
        'bin_count': bin_count,
        'attempted': 0,
        'successful': 0,
        'failed': 0,
        'skipped': 0
    }

    logger.info(f"Starting generation for bin: {bin_count} regions")

    samples_generated = 0
    dataset_iter = iter(source_dataset)
    current_idx = start_idx

    while samples_generated < SAMPLES_PER_BIN:
        stats['attempted'] += 1
        try:
            # Fetch next sample from dataset
            sample = next(dataset_iter)
            current_idx += 1

            # Extract image and annotations
            if 'image' not in sample or 'annotations' not in sample:
                logger.warning(f"Skipping sample {current_idx}: missing required fields")
                stats['skipped'] += 1
                continue

            image = sample['image']
            annotations = sample['annotations']

            if not isinstance(image, object) or image is None:
                logger.warning(f"Skipping sample {current_idx}: invalid image")
                stats['skipped'] += 1
                continue

            # Place bounding boxes with retry logic
            boxes = place_boxes_with_retry(
                image_size=image.size,
                target_count=bin_count,
                max_retries=50
            )

            if boxes is None:
                logger.warning(f"Failed to place {bin_count} boxes for sample {current_idx}")
                stats['failed'] += 1
                continue

            # Validate no overlaps
            if not validate_no_overlaps(boxes):
                logger.warning(f"Overlap detected in generated boxes for sample {current_idx}")
                stats['failed'] += 1
                continue

            # Derive ground-truth relations
            relations = derive_all_relations(boxes)

            # Prepare annotation data
            annotation_data = {
                'image_path': f"synthetic_{bin_count}_{samples_generated}.png",
                'bounding_boxes': boxes,
                'derived_relations': relations,
                'region_count': bin_count,
                'source_sample_idx': current_idx
            }

            # Validate against schema
            if not validate_synthetic_image(annotation_data):
                logger.warning(f"Schema validation failed for sample {current_idx}")
                stats['failed'] += 1
                continue

            # Serialize and save
            output_path = serialize_synthetic_sample(
                image=image,
                annotation_data=annotation_data,
                output_dir=output_dir,
                filename_prefix=f"synthetic_{bin_count}_{samples_generated}"
            )

            if output_path:
                samples_generated += 1
                stats['successful'] += 1
                logger.info(f"Generated sample {samples_generated}/{SAMPLES_PER_BIN} for bin {bin_count}")
            else:
                stats['failed'] += 1

        except StopIteration:
            logger.error(f"Ran out of dataset samples for bin {bin_count}")
            break
        except Exception as e:
            logger.error(f"Error processing sample {current_idx}: {e}")
            stats['failed'] += 1
            continue

    logger.info(f"Completed bin {bin_count}: {stats['successful']}/{stats['attempted']} successful")
    return stats

def run_generation_pipeline():
    """
    Main pipeline execution for generating the full synthetic dataset.
    """
    logger.info("Starting synthetic dataset generation pipeline")

    # Ensure directories exist
    ensure_directories()
    output_dir = get_data_path() / "synthetic"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fetch real dataset
    logger.info("Fetching dataset from HuggingFace...")
    try:
        dataset = fetch_dataset_sample(
            dataset_name="coco/coco-stuff-164k",
            split="train",
            max_samples=500  # Enough for all bins
        )
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        sys.exit(1)

    # Convert to list for multiple iterations
    dataset_list = list(dataset)
    logger.info(f"Loaded {len(dataset_list)} samples from dataset")

    # Generate for each bin
    all_stats = []
    current_idx = 0

    for count in REGION_COUNTS:
        bin_stats = generate_sample_for_bin(
            bin_count=count,
            source_dataset=dataset_list,
            output_dir=output_dir,
            start_idx=current_idx
        )
        all_stats.append(bin_stats)
        current_idx += SAMPLES_PER_BIN

        # Small delay to avoid rate limiting
        time.sleep(0.1)

    # Summary
    total_attempted = sum(s['attempted'] for s in all_stats)
    total_successful = sum(s['successful'] for s in all_stats)
    total_failed = sum(s['failed'] for s in all_stats)

    logger.info(f"Pipeline complete: {total_successful}/{total_attempted} successful, {total_failed} failed")

    # Save generation log
    log_path = output_dir / "generation_log.json"
    with open(log_path, 'w') as f:
        json.dump({
            'region_counts': REGION_COUNTS,
            'samples_per_bin': SAMPLES_PER_BIN,
            'statistics': all_stats
        }, f, indent=2)

    logger.info(f"Generation log saved to {log_path}")

    return all_stats

def main():
    """Entry point for the generator script."""
    run_generation_pipeline()

if __name__ == "__main__":
    main()
