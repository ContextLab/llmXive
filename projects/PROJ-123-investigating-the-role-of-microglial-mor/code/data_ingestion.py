"""
Data Ingestion Module for Microglial Morphology Project.

Handles loading microscopy images, parsing metadata from filenames/directories,
and validating brain region tags. Implements FR-001 (Image Loading) and FR-008
(Metadata Parsing & Warning for missing tags).
"""
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from PIL import Image

from code.config import get_path, ensure_dirs, CONFIG
from code.logging_utils import warn_missing_metadata, get_logger

logger = get_logger(__name__)

# Supported image extensions
SUPPORTED_EXTENSIONS = {'.tif', '.tiff', '.png', '.jpg', '.jpeg'}

# Expected filename pattern: <subject_id>_<brain_region>_<timestamp>.tif
# Example: mouse_001_hippocampus_20231027.tif
FILENAME_PATTERN = re.compile(
    r'^(?P<subject_id>[a-zA-Z0-9_]+)_(?P<brain_region>[a-zA-Z0-9_]+)_(?P<timestamp>\d{8,14})\.(?P<ext>[a-zA-Z0-9]+)$'
)

def load_image(image_path: Path) -> np.ndarray:
    """
    Load an image file into a numpy array.

    Args:
        image_path: Path to the image file.

    Returns:
        Numpy array representing the image (grayscale or RGB).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported or unreadable.
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    if image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported image extension: {image_path.suffix}")

    try:
        with Image.open(image_path) as img:
            # Convert to numpy array
            arr = np.array(img)
            # Ensure 2D or 3D (grayscale or RGB)
            if arr.ndim == 2:
                logger.debug(f"Loaded grayscale image: {image_path.name}, shape: {arr.shape}")
            elif arr.ndim == 3:
                logger.debug(f"Loaded RGB image: {image_path.name}, shape: {arr.shape}")
            else:
                logger.warning(f"Unexpected image dimensions for {image_path.name}: {arr.ndim}")
            return arr
    except Exception as e:
        logger.error(f"Failed to read image {image_path}: {e}")
        raise

def parse_metadata_from_filename(filename: str) -> Dict[str, Any]:
    """
    Extract metadata (subject_id, brain_region, timestamp) from filename.

    Args:
        filename: The name of the image file.

    Returns:
        Dictionary with extracted metadata keys. Returns empty dict if no match.
    """
    match = FILENAME_PATTERN.match(filename)
    if match:
        return match.groupdict()
    return {}

def validate_brain_region(brain_region: Optional[str], filepath: Path) -> bool:
    """
    Validate that the brain region is present and known.

    FR-008: Log a warning if metadata is missing.

    Args:
        brain_region: The extracted brain region string.
        filepath: Path to the file for logging context.

    Returns:
        True if valid, False if missing or invalid.
    """
    if not brain_region:
        warn_missing_metadata(filepath, "brain_region")
        return False

    # Optional: Check against a list of known regions if defined in config
    known_regions = CONFIG.get('known_brain_regions', [])
    if known_regions and brain_region not in known_regions:
        logger.warning(f"Unknown brain region '{brain_region}' in {filepath.name}. "
                       f"Expected one of: {known_regions}")
        # Depending on strictness, we might return False here.
        # For now, we log but allow processing, as the region might be valid but new.
        return True

    return True

def ingest_directory(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Ingest all images from a directory, parsing metadata and validating tags.

    Args:
        data_dir: Path to the directory containing images.

    Returns:
        List of dictionaries containing image data and metadata.
        Format: [{'path': Path, 'image': np.ndarray, 'metadata': dict}, ...]
    """
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    if not data_dir.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {data_dir}")

    ingested_data = []
    skipped_count = 0

    logger.info(f"Starting ingestion from: {data_dir}")

    for file_path in sorted(data_dir.iterdir()):
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        # Parse metadata
        metadata = parse_metadata_from_filename(file_path.name)

        if not metadata:
            logger.warning(f"Filename does not match expected pattern: {file_path.name}. Skipping.")
            skipped_count += 1
            continue

        # Validate brain region
        if not validate_brain_region(metadata.get('brain_region'), file_path):
            # If brain region is missing, we skip this image as per FR-008 logic
            # (exclusion of untagged images)
            logger.warning(f"Skipping image due to missing/invalid brain_region: {file_path.name}")
            skipped_count += 1
            continue

        try:
            image_array = load_image(file_path)
            ingested_data.append({
                'path': file_path,
                'image': image_array,
                'metadata': metadata
            })
            logger.debug(f"Successfully ingested: {file_path.name}")

        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            skipped_count += 1
            continue

    logger.info(f"Ingestion complete. Processed: {len(ingested_data)}, Skipped: {skipped_count}")
    return ingested_data

def run_ingestion_pipeline(input_dir_name: str = 'raw', output_dir_name: str = 'intermediates') -> None:
    """
    Main entry point for the ingestion pipeline.

    Reads from `data/<input_dir_name>`, validates, and saves a manifest
    to `data/<output_dir_name>/ingestion_manifest.json`.

    Args:
        input_dir_name: Name of the input directory relative to data root.
        output_dir_name: Name of the output directory relative to data root.
    """
    data_root = get_path('data')
    input_path = data_root / input_dir_name
    
    # Ensure output directory exists
    output_path = data_root / output_dir_name
    ensure_dirs(output_path)

    manifest_path = output_path / 'ingestion_manifest.json'

    if not input_path.exists():
        # If raw data doesn't exist, we might generate synthetic for testing
        # but the task requires real ingestion logic. We raise an error if
        # the user expects real data and it's missing.
        logger.warning(f"Input directory {input_path} does not exist. "
                       "Ingestion pipeline requires real data or pre-generated synthetic data in data/raw.")
        # For the purpose of this task, we do not auto-generate synthetic data here
        # as that is the responsibility of synthetic_data.py (T007).
        # We fail loudly as per constraint 9.
        raise FileNotFoundError(f"Input directory for ingestion not found: {input_path}")

    try:
        results = ingest_directory(input_path)
    except Exception as e:
        logger.critical(f"Ingestion pipeline failed: {e}")
        raise

    # Save manifest
    manifest_data = {
        'input_directory': str(input_path),
        'processed_count': len(results),
        'files': []
    }

    for item in results:
        manifest_data['files'].append({
            'filename': item['path'].name,
            'subject_id': item['metadata'].get('subject_id'),
            'brain_region': item['metadata'].get('brain_region'),
            'shape': list(item['image'].shape),
            'dtype': str(item['image'].dtype)
        })

    import json
    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)

    logger.info(f"Ingestion manifest saved to: {manifest_path}")

if __name__ == '__main__':
    # Example execution
    run_ingestion_pipeline()
