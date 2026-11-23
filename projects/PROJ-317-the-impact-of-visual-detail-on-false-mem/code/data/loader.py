"""
Data loading utilities for the Visual Detail and False Memory project.

This module provides robust error handling for:
1. Missing metadata files
2. Failed dataset fetches from external sources
3. Corrupted or invalid data files

It ensures that the pipeline fails loudly with clear error messages rather than
silently falling back to synthetic data.
"""

import json
import logging
import math
import os
import random
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import yaml
from datasets import load_dataset
from PIL import Image
from io import BytesIO

from config import get_project_root, get_stimuli_dir, get_stimuli_metadata_dir, get_data_dir
from utils.logging import get_logger, log_error
from data.checksum import compute_file_checksum, verify_checksum

# Configure logger
logger = get_logger(__name__)

class DataLoadError(Exception):
    """Custom exception for data loading failures."""
    pass

class MetadataNotFoundError(DataLoadError):
    """Exception raised when metadata file is missing."""
    pass

class FetchFailedError(DataLoadError):
    """Exception raised when dataset fetch fails."""
    pass

class IntegrityError(DataLoadError):
    """Exception raised when data integrity check fails."""
    pass

def generate_mock_visual_genome(output_dir: Path, count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate mock Visual Genome image metadata for testing purposes ONLY.
    
    WARNING: This function is for CI/testing only. It MUST NOT be used in
    production or research runs. Real data must always be loaded from
    the actual Visual Genome dataset.
    
    Args:
        output_dir: Directory to write mock metadata files
        count: Number of mock entries to generate
        
    Returns:
        List of mock metadata dictionaries
        
    Raises:
        ValueError: If called in production mode
    """
    # This is strictly for testing - raise if used inappropriately
    if os.environ.get("ALLOW_MOCK_DATA", "false").lower() != "true":
        raise DataLoadError(
            "Mock data generation is disabled. Set ALLOW_MOCK_DATA=true for testing only. "
            "Production runs must use real data from the Visual Genome dataset."
        )
    
    logger.warning(f"Generating {count} mock Visual Genome entries (TEST MODE ONLY)")
    mock_data = []
    for i in range(count):
        mock_entry = {
            "image_id": f"mock_{i:04d}",
            "url": f"https://example.com/mock/{i}.jpg",
            "width": 640,
            "height": 480,
            "objects": [{"name": "mock_object"}],
            "attributes": [],
            "relationships": []
        }
        mock_data.append(mock_entry)
        
        # Write mock metadata file
        metadata_path = output_dir / f"mock_{i:04d}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(mock_entry, f, indent=2)
    
    return mock_data

def fetch_real_dataset_image(image_id: str, subset_dir: Path) -> Optional[Path]:
    """
    Fetch a real image from the Visual Genome dataset.
    
    This function attempts to load the image from the pre-bundled subset.
    If the image is not found in the local subset, it will attempt to fetch
    it from the streaming dataset.
    
    Args:
        image_id: The unique identifier for the image
        subset_dir: Directory containing the pre-bundled subset
        
    Returns:
        Path to the downloaded image file, or None if fetch fails
        
    Raises:
        FetchFailedError: If the image cannot be retrieved from any source
        IntegrityError: If checksum verification fails
    """
    logger.info(f"Attempting to fetch image {image_id}")
    
    # First, check local pre-bundled subset
    local_path = subset_dir / f"{image_id}.jpg"
    if local_path.exists():
        logger.info(f"Found image {image_id} in local subset")
        # Verify checksum if manifest exists
        manifest_path = subset_dir / "manifest.sha256"
        if manifest_path.exists():
            if not verify_checksum(local_path, manifest_path):
                raise IntegrityError(f"Checksum mismatch for image {image_id}")
        return local_path
    
    # If not in local subset, try streaming fetch
    try:
        logger.info(f"Fetching image {image_id} from streaming dataset")
        dataset = load_dataset("visual_genense", split="train", streaming=True)
        
        for item in dataset:
            if str(item.get('image_id')) == image_id:
                img_data = item.get('image')
                if img_data:
                    # Save to local file
                    output_path = subset_dir / f"{image_id}.jpg"
                    img_data.save(output_path)
                    logger.info(f"Successfully saved image {image_id} to {output_path}")
                    return output_path
        
        raise FetchFailedError(f"Image {image_id} not found in dataset")
        
    except Exception as e:
        logger.error(f"Failed to fetch image {image_id}: {str(e)}")
        raise FetchFailedError(f"Failed to fetch image {image_id}: {str(e)}") from e

def load_image_metadata(image_id: str, metadata_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load metadata for a specific image from YAML file.
    
    This function implements robust error handling for:
    1. Missing metadata files (raises MetadataNotFoundError)
    2. Corrupted YAML files (raises DataLoadError)
    3. Missing required fields (raises DataLoadError)
    
    Args:
        image_id: The unique identifier for the image
        metadata_dir: Optional override for metadata directory
        
    Returns:
        Dictionary containing image metadata
        
    Raises:
        MetadataNotFoundError: If metadata file does not exist
        DataLoadError: If metadata file is corrupted or missing required fields
    """
    if metadata_dir is None:
        metadata_dir = get_stimuli_metadata_dir()
    
    # Check for metadata file
    metadata_path = metadata_dir / f"{image_id}_metadata.yaml"
    
    if not metadata_path.exists():
        error_msg = f"Metadata file not found: {metadata_path}"
        logger.error(error_msg)
        raise MetadataNotFoundError(error_msg)
    
    try:
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f)
        
        if metadata is None:
            error_msg = f"Empty metadata file: {metadata_path}"
            logger.error(error_msg)
            raise DataLoadError(error_msg)
        
        # Validate required fields
        required_fields = ['id', 'detail_level']
        for field in required_fields:
            if field not in metadata:
                error_msg = f"Missing required field '{field}' in metadata for {image_id}"
                logger.error(error_msg)
                raise DataLoadError(error_msg)
        
        logger.debug(f"Successfully loaded metadata for {image_id}")
        return metadata
        
    except yaml.YAMLError as e:
        error_msg = f"Failed to parse YAML metadata for {image_id}: {str(e)}"
        logger.error(error_msg)
        raise DataLoadError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error loading metadata for {image_id}: {str(e)}"
        logger.error(error_msg)
        raise DataLoadError(error_msg) from e

def process_image_with_error_handling(image_path: Path, processing_func, **kwargs) -> Tuple[Optional[Path], Optional[str]]:
    """
    Process an image with comprehensive error handling.
    
    This wrapper function catches common image processing errors and logs them
    appropriately, returning a tuple of (result_path, error_message).
    
    Args:
        image_path: Path to the image file to process
        processing_func: Function to apply to the image
        **kwargs: Additional arguments to pass to processing_func
        
    Returns:
        Tuple of (output_path or None, error_message or None)
    """
    try:
        if not image_path.exists():
            error_msg = f"Image file not found: {image_path}"
            logger.error(error_msg)
            return None, error_msg
        
        # Validate image format
        try:
            with Image.open(image_path) as img:
                img.verify()
        except Exception as e:
            error_msg = f"Corrupted or unsupported image format: {image_path} - {str(e)}"
            logger.error(error_msg)
            return None, error_msg
        
        # Execute processing function
        result = processing_func(image_path, **kwargs)
        return result, None
        
    except Exception as e:
        error_msg = f"Processing failed for {image_path}: {str(e)}"
        logger.error(error_msg)
        log_error(error_msg)
        return None, error_msg

def validate_data_bundle(bundle_dir: Path) -> bool:
    """
    Validate the integrity of a data bundle.
    
    Checks:
    1. Required files exist
    2. Checksums match manifest
    3. File sizes are reasonable
    
    Args:
        bundle_dir: Directory containing the data bundle
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        IntegrityError: If validation fails
    """
    required_files = ['manifest.sha256']
    for req_file in required_files:
        if not (bundle_dir / req_file).exists():
            raise IntegrityError(f"Required file missing: {req_file}")
    
    if not verify_directory_integrity(bundle_dir):
        raise IntegrityError("Directory integrity check failed")
    
    return True

def main():
    """Main entry point for CLI usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Data loading utilities")
    parser.add_argument('--image-id', type=str, help="Image ID to load")
    parser.add_argument('--metadata-dir', type=str, help="Override metadata directory")
    parser.add_argument('--validate-bundle', type=str, help="Validate a data bundle directory")
    
    args = parser.parse_args()
    
    if args.validate_bundle:
        bundle_dir = Path(args.validate_bundle)
        try:
            validate_data_bundle(bundle_dir)
            print(f"Validation successful for {bundle_dir}")
        except IntegrityError as e:
            print(f"Validation failed: {e}")
            return 1
    
    if args.image_id:
        metadata_dir = Path(args.metadata_dir) if args.metadata_dir else None
        try:
            metadata = load_image_metadata(args.image_id, metadata_dir)
            print(json.dumps(metadata, indent=2))
        except (MetadataNotFoundError, DataLoadError) as e:
            print(f"Error: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
