import argparse
import json
import logging
import math
import os
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from config import get_project_root, get_stimuli_dir, get_data_dir
from utils.logging import get_logger
from data.checksum import compute_file_checksum, save_checksum_manifest, verify_checksum

logger = get_logger(__name__)

def fetch_real_dataset_image(
    source: str = "visual_genome",
    limit: int = 30,
    output_dir: Optional[str] = None,
    streaming: bool = True
) -> List[str]:
    """
    Fetch a sample of images from a real dataset (Visual Genome).

    Args:
        source: Dataset source identifier.
        limit: Number of images to fetch.
        output_dir: Directory to save images.
        streaming: Whether to stream the dataset.

    Returns:
        List of paths to downloaded images.
    """
    try:
        from datasets import load_dataset
        from PIL import Image
        import io
    except ImportError:
        logger.error("datasets or PIL not installed. Please install them.")
        raise ImportError("datasets and PIL are required for data fetching.")

    if output_dir is None:
        output_dir = get_stimuli_dir() / "raw_subset"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Fetching {limit} images from {source}...")

    # Load dataset
    if streaming:
        dataset = load_dataset(source, split="train", streaming=True)
    else:
        dataset = load_dataset(source, split="train")

    image_paths = []
    count = 0

    for item in dataset:
        if count >= limit:
            break

        # Visual Genome image structure varies; handle common cases
        img = None
        if 'image' in item:
            img = item['image']
        elif 'image_url' in item:
            # Download from URL
            import urllib.request
            try:
                with urllib.request.urlopen(item['image_url']) as response:
                    img = Image.open(io.BytesIO(response.read()))
            except Exception as e:
                logger.warning(f"Failed to download image {item.get('id', 'unknown')}: {e}")
                continue
        else:
            # Try to find image in nested structure
            for key, value in item.items():
                if isinstance(value, Image.Image):
                    img = value
                    break

        if img is None:
            continue

        # Save image
        img_id = item.get('id', count)
        img_path = output_dir / f"vg_{img_id}.png"
        
        # Avoid overwriting
        if img_path.exists():
            continue

        try:
            img.save(img_path, format='PNG')
            image_paths.append(str(img_path))
            count += 1
            logger.debug(f"Fetched image {count}: {img_path}")
        except Exception as e:
            logger.warning(f"Failed to save image {img_id}: {e}")

    logger.info(f"Fetched {len(image_paths)} images.")

    # Generate checksum manifest
    manifest_path = output_dir / "manifest.sha256"
    save_checksum_manifest(image_paths, manifest_path)

    return image_paths

def calculate_complexity_score(
    image_path: str
) -> float:
    """
    Calculate a baseline complexity score for an image.

    Uses object density as a proxy for complexity.

    Args:
        image_path: Path to the image.

    Returns:
        Complexity score (0.0 to 1.0).
    """
    try:
        from PIL import Image
    except ImportError:
        logger.error("PIL not installed.")
        raise ImportError("PIL is required for complexity calculation.")

    img = Image.open(image_path)
    width, height = img.size
    area = width * height

    # Simple heuristic: count non-background pixels and edges
    # This is a placeholder for a more sophisticated metric
    # In a real implementation, we'd use object detection or edge density

    # Convert to grayscale and threshold
    gray = img.convert('L')
    # Assume complexity is proportional to variance in pixel values
    pixels = list(gray.getdata())
    mean_val = sum(pixels) / len(pixels)
    variance = sum((p - mean_val) ** 2 for p in pixels) / len(pixels)

    # Normalize variance to 0-1 range (assuming 0-255 range)
    max_variance = (255 ** 2) / 4  # Max variance for 0-255
    complexity = min(1.0, variance / max_variance)

    return complexity

def load_image_metadata(
    image_path: str
) -> Dict[str, Any]:
    """
    Load metadata for an image.

    Args:
        image_path: Path to the image.

    Returns:
        Metadata dictionary.
    """
    try:
        from PIL import Image
    except ImportError:
        logger.error("PIL not installed.")
        raise ImportError("PIL is required for metadata loading.")

    img = Image.open(image_path)
    width, height = img.size

    return {
        "path": image_path,
        "width": width,
        "height": height,
        "format": img.format,
        "mode": img.mode,
        "complexity_score": calculate_complexity_score(image_path)
    }

def process_image_with_error_handling(
    image_path: str
) -> Optional[Dict[str, Any]]:
    """
    Process an image with error handling.

    Args:
        image_path: Path to the image.

    Returns:
        Metadata dictionary or None if processing fails.
    """
    try:
        return load_image_metadata(image_path)
    except Exception as e:
        logger.error(f"Failed to process image {image_path}: {e}")
        return None

def filter_by_complexity_range(
    image_paths: List[str],
    min_complexity: float = 0.2,
    max_complexity: float = 0.8
) -> List[str]:
    """
    Filter images by complexity score range.

    Args:
        image_paths: List of image paths.
        min_complexity: Minimum complexity score.
        max_complexity: Maximum complexity score.

    Returns:
        Filtered list of image paths.
    """
    filtered = []
    for path in image_paths:
        metadata = process_image_with_error_handling(path)
        if metadata and min_complexity <= metadata['complexity_score'] <= max_complexity:
            filtered.append(path)

    return filtered

def validate_data_bundle(
    bundle_dir: str
) -> bool:
    """
    Validate a data bundle using checksums.

    Args:
        bundle_dir: Directory containing the bundle.

    Returns:
        True if valid, False otherwise.
    """
    manifest_path = Path(bundle_dir) / "manifest.sha256"
    if not manifest_path.exists():
        logger.error(f"Manifest not found at {manifest_path}")
        return False

    # Load manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    # Verify each file
    for file_info in manifest:
        file_path = Path(file_info['path'])
        expected_hash = file_info['checksum']

        if not file_path.exists():
            logger.error(f"File missing: {file_path}")
            return False

        actual_hash = compute_file_checksum(file_path)
        if actual_hash != expected_hash:
            logger.error(f"Checksum mismatch for {file_path}")
            return False

    logger.info("Data bundle validated successfully.")
    return True

def main():
    """CLI entry point for data loading."""
    parser = argparse.ArgumentParser(description="Load and process dataset images")
    parser.add_argument('--source', type=str, default="visual_genome", help='Dataset source')
    parser.add_argument('--limit', type=int, default=30, help='Number of images to fetch')
    parser.add_argument('--output', type=str, help='Output directory')
    parser.add_argument('--validate', action='store_true', help='Validate existing bundle')
    parser.add_argument('--complexity-min', type=float, default=0.2, help='Min complexity')
    parser.add_argument('--complexity-max', type=float, default=0.8, help='Max complexity')

    args = parser.parse_args()

    if args.validate:
        bundle_dir = args.output or get_stimuli_dir() / "raw_subset"
        success = validate_data_bundle(bundle_dir)
        return 0 if success else 1

    # Fetch data
    paths = fetch_real_dataset_image(
        source=args.source,
        limit=args.limit,
        output_dir=args.output
    )

    if not paths:
        logger.error("No images fetched.")
        return 1

    # Optionally filter by complexity
    if args.complexity_min is not None or args.complexity_max is not None:
        filtered = filter_by_complexity_range(
            paths,
            min_complexity=args.complexity_min,
            max_complexity=args.complexity_max
        )
        logger.info(f"Filtered to {len(filtered)} images by complexity.")
        # Save filtered list
        output_file = Path(args.output or get_stimuli_dir()) / "filtered_list.json"
        with open(output_file, 'w') as f:
            json.dump(filtered, f, indent=2)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
