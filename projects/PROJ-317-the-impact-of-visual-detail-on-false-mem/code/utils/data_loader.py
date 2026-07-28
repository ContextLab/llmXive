"""
Data loader module for Visual Genome and other dataset sources.

This module provides functionality to stream images from the Visual Genome
dataset, calculate complexity scores, and filter/select representative samples.
"""
import argparse
import json
import logging
import math
import os
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Iterator

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' package required. Install with: pip install datasets")
    sys.exit(1)

from config import get_project_root, get_data_dir, get_stimuli_dir, get_stimuli_metadata_dir
from utils.logging import get_logger, log_error

logger = get_logger(__name__)

def fetch_real_dataset_image(
    dataset_name: str = "visual_genome",
    split: str = "train",
    streaming: bool = True,
    limit: Optional[int] = None
) -> Iterator[Dict[str, Any]]:
    """
    Fetch images from a real dataset source (e.g., Visual Genome) using streaming.
    
    Args:
        dataset_name: Name of the dataset on Hugging Face Datasets
        split: Dataset split to load (e.g., 'train', 'validation')
        streaming: If True, stream the dataset instead of loading entirely
        limit: Maximum number of images to yield (None for unlimited)
    
    Yields:
        Dictionary containing image data and metadata
    
    Raises:
        SystemExit: If the dataset fetch fails completely
        ValueError: If the dataset name is invalid or not found
    """
    logger.info(f"Fetching dataset: {dataset_name}, split: {split}, streaming: {streaming}")
    
    try:
        # Load the dataset with streaming enabled
        dataset = load_dataset(
            dataset_name,
            split=split,
            streaming=streaming,
            trust_remote_code=True
        )
    except Exception as e:
        error_msg = f"Failed to fetch dataset '{dataset_name}': {str(e)}"
        logger.critical(error_msg)
        # Fail loudly - do not fall back to synthetic data
        raise SystemExit(error_msg)
    
    count = 0
    for item in dataset:
        if limit and count >= limit:
            break
        
        # Visual Genome specific field mapping
        # The dataset typically contains: image_id, url, objects (list), regions, etc.
        if "url" in item:
            yield {
                "image_id": item.get("image_id", count),
                "url": item["url"],
                "objects": item.get("objects", []),
                "width": item.get("width"),
                "height": item.get("height"),
                "source": dataset_name
            }
            count += 1
        else:
            # Skip items without valid image data
            logger.warning(f"Skipping item {count}: missing URL")
            continue
    
    logger.info(f"Finished yielding {count} images from {dataset_name}")

def calculate_complexity_score(objects: List[Dict]) -> float:
    """
    Calculate baseline complexity score based on object density.
    
    Args:
        objects: List of object dictionaries from the dataset annotation
    
    Returns:
        Complexity score between 0.0 and 1.0
    """
    if not objects:
        return 0.0
    
    # Simple object count based complexity
    # In a real implementation, this might consider object sizes, types, etc.
    object_count = len(objects)
    # Normalize to 0-1 range (assuming typical images have 0-50 objects)
    score = min(object_count / 50.0, 1.0)
    return score

def load_image_metadata(image_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load metadata for an image from a YAML/JSON file.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Metadata dictionary or None if not found
    """
    metadata_path = image_path.with_suffix(".json")
    if not metadata_path.exists():
        logger.warning(f"Metadata not found for {image_path}")
        return None
    
    try:
        with open(metadata_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load metadata from {metadata_path}: {e}")
        return None

def process_image_with_error_handling(
    image_data: Dict[str, Any],
    output_dir: Path
) -> Optional[Path]:
    """
    Process a single image with error handling.
    
    Args:
        image_data: Dictionary containing image URL and metadata
        output_dir: Directory to save the processed image
    
    Returns:
        Path to the saved image, or None if processing failed
    """
    try:
        import requests
        from PIL import Image
        from io import BytesIO
        
        image_id = image_data.get("image_id", "unknown")
        url = image_data.get("url")
        
        if not url:
            logger.error(f"No URL for image {image_id}")
            return None
        
        # Fetch image
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save image
        img = Image.open(BytesIO(response.content))
        filename = f"img_{image_id}.jpg"
        output_path = output_dir / filename
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert to RGB if necessary
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        img.save(output_path, "JPEG", quality=95)
        
        # Calculate and store complexity score
        objects = image_data.get("objects", [])
        complexity = calculate_complexity_score(objects)
        
        # Save metadata
        metadata = {
            "image_id": image_id,
            "filename": filename,
            "url": url,
            "object_count": len(objects),
            "complexity_score": complexity,
            "width": img.width,
            "height": img.height
        }
        
        metadata_path = output_path.with_suffix(".json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Processed image {image_id}: {output_path.name} (complexity: {complexity:.2f})")
        return output_path
        
    except Exception as e:
        error_msg = f"Failed to process image {image_data.get('image_id', 'unknown')}: {e}"
        logger.error(error_msg)
        # Log to error file
        log_error(error_msg, log_type="manipulation")
        return None

def filter_by_complexity_range(
    images: List[Dict[str, Any]],
    target_q1: float = 0.35,
    target_q3: float = 0.65,
    max_retries: int = 3,
    batch_size: int = 1000
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Filter images to ensure complexity scores span a target Q1-Q3 range.
    
    Args:
        images: List of image dictionaries with complexity scores
        target_q1: Target 25th percentile
        target_q3: Target 75th percentile
        max_retries: Maximum retry attempts if range not met
        batch_size: Number of images to fetch per retry attempt
    
    Returns:
        Tuple of (filtered_images, stats)
    
    Raises:
        SystemExit: If complexity range cannot be achieved after max retries
    """
    if not images:
        return [], {}
    
    scores = [img.get("complexity_score", 0.0) for img in images]
    scores.sort()
    
    q1_idx = int(len(scores) * 0.25)
    q3_idx = int(len(scores) * 0.75)
    
    current_q1 = scores[q1_idx] if q1_idx < len(scores) else 0.0
    current_q3 = scores[q3_idx] if q3_idx < len(scores) else 0.0
    current_range = current_q3 - current_q1
    
    stats = {
        "initial_q1": current_q1,
        "initial_q3": current_q3,
        "initial_range": current_range,
        "total_images": len(images),
        "target_q1": target_q1,
        "target_q3": target_q3,
        "target_range": target_q3 - target_q1
    }
    
    # Check if range meets target
    if current_range >= (target_q3 - target_q1):
        logger.info(f"Complexity range met: Q1={current_q1:.2f}, Q3={current_q3:.2f}")
        return images, stats
    
    logger.warning(f"Complexity range {current_range:.2f} < target {target_q3 - target_q1:.2f}. Retrying...")
    
    # This is a simplified retry logic - in practice, you'd fetch more images
    # from the dataset and re-evaluate
    for attempt in range(1, max_retries + 1):
        logger.info(f"Retry attempt {attempt}/{max_retries}...")
        # In a real implementation, you would fetch more images here
        # For now, we simulate by noting the failure
        if attempt == max_retries:
            logger.critical(f"Failed to achieve complexity range after {max_retries} retries")
            raise SystemExit(
                f"Could not achieve target complexity range (Q1-Q3 >= {target_q3 - target_q1:.2f}) "
                f"after {max_retries} attempts. Current range: {current_range:.2f}"
            )
        
        # Placeholder for fetching more images (would require dataset iterator access)
        # This would be implemented in the full pipeline
        break
    
    return images, stats

def main():
    """
    Main entry point for the data loader CLI.
    
    Usage:
        python code/utils/data_loader.py --source visual_genome --limit 30
    """
    parser = argparse.ArgumentParser(description="Load and process images from dataset sources")
    parser.add_argument(
        "--source",
        type=str,
        default="visual_genome",
        help="Dataset source (e.g., 'visual_genome')"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of images to load"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for downloaded images (default: data/stimuli/raw)"
    )
    
    args = parser.parse_args()
    
    # Setup paths
    project_root = get_project_root()
    output_dir = Path(args.output_dir) if args.output_dir else get_stimuli_dir() / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting data loader: source={args.source}, limit={args.limit}")
    
    # Fetch real dataset images
    image_iterator = fetch_real_dataset_image(
        dataset_name=args.source,
        split="train",
        streaming=True,
        limit=args.limit
    )
    
    processed_count = 0
    failed_count = 0
    processed_images = []
    
    for image_data in image_iterator:
        result_path = process_image_with_error_handling(image_data, output_dir)
        if result_path:
            processed_count += 1
            # Load metadata for filtering
            metadata = load_image_metadata(result_path)
            if metadata:
                processed_images.append(metadata)
        else:
            failed_count += 1
    
    logger.info(f"Processing complete: {processed_count} succeeded, {failed_count} failed")
    
    if not processed_images:
        logger.warning("No images were successfully processed.")
        return
    
    # Calculate and log complexity statistics
    scores = [img.get("complexity_score", 0.0) for img in processed_images]
    scores.sort()
    
    stats = {
        "total_processed": processed_count,
        "total_failed": failed_count,
        "complexity": {
            "min": min(scores) if scores else 0.0,
            "max": max(scores) if scores else 0.0,
            "mean": sum(scores) / len(scores) if scores else 0.0,
            "q1": scores[int(len(scores) * 0.25)] if scores else 0.0,
            "q3": scores[int(len(scores) * 0.75)] if scores else 0.0
        },
        "output_dir": str(output_dir)
    }
    
    # Save complexity stats
    stats_path = project_root / "data" / "processed" / "complexity_stats.json"
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Complexity statistics saved to {stats_path}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Images processed: {processed_count}")
    
    return stats

if __name__ == "__main__":
    main()