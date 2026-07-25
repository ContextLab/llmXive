"""
Data loading utilities for the Visual Detail and False Memory project.

This module handles fetching real datasets (COCO 2017), loading metadata,
and processing images with robust error handling.
"""

import json
import logging
import math
import os
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator

# Import logging utilities from the project's utils
from utils.logging import get_logger, log_error
from config import get_stimuli_dir, get_stimuli_metadata_dir, get_logs_dir

# Import Image entity
from data.image import Image

# Configure module logger
logger = get_logger(__name__)

# Constants
MISSING_METADATA_ERROR = "Metadata file missing for image ID: {}"
FETCH_FAILED_ERROR = "Failed to fetch image ID: {} from dataset source"
PROCESSING_FAILED_ERROR = "Failed to process image ID: {}"
LOG_FILE_PATH = None  # Will be initialized dynamically

def _get_manipulation_error_log_path() -> Path:
    """Get the path to the manipulation error log file."""
    global LOG_FILE_PATH
    if LOG_FILE_PATH is None:
        logs_dir = get_logs_dir()
        LOG_FILE_PATH = logs_dir / "manipulation_errors.log"
        # Ensure the directory exists
        LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    return LOG_FILE_PATH

def generate_mock_visual_genome(count: int = 10) -> List[Dict[str, Any]]:
    """
    Generate a small set of mock Visual Genome-like metadata for testing.
    
    Args:
        count: Number of mock items to generate.
        
    Returns:
        List of dictionaries containing mock image metadata.
    """
    mock_data = []
    categories = ["vehicle", "animal", "furniture", "food", "electronics"]
    
    for i in range(count):
        item = {
            "image_id": f"mock_{i:04d}",
            "width": 512,
            "height": 512,
            "objects": [
                {
                    "name": f"mock_object_{i}",
                    "category": random.choice(categories),
                    "bbox": [50, 50, 100, 100],
                    "confidence": 0.9
                }
            ],
            "complexity_score": random.uniform(0.3, 0.7)
        }
        mock_data.append(item)
        
    return mock_data

def fetch_real_dataset_image(image_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single image and its metadata from the real dataset source (COCO 2017).
    
    This function attempts to retrieve image data. If the fetch fails for an 
    individual image, it logs the error and returns None, allowing the pipeline
    to continue processing other images.
    
    Args:
        image_id: The unique identifier for the image in the dataset.
        
    Returns:
        A dictionary containing image metadata if successful, None otherwise.
        
    Raises:
        SystemExit: If the entire dataset fetch mechanism fails (not individual images).
    """
    try:
        # Attempt to load the dataset in streaming mode
        # Using datasets library to access COCO 2017
        try:
            from datasets import load_dataset
        except ImportError:
            logger.error("The 'datasets' library is not installed. Please install it via pip.")
            raise SystemExit("Dependency 'datasets' not found. Cannot fetch real data.")

        logger.info(f"Attempting to fetch image {image_id} from COCO 2017...")
        
        # Load the dataset in streaming mode to handle large sizes
        dataset = load_dataset("coco_2017", split="train", streaming=True)
        
        # Iterate to find the specific image
        # Note: In a real streaming scenario, we might need to filter by ID
        # For this implementation, we assume the image_id corresponds to an index or specific filter
        # If the dataset structure requires a different lookup, it should be adjusted here.
        
        # Since COCO 2017 in HuggingFace might not have a direct 'id' filter in streaming
        # without loading the whole index, we implement a robust fetch strategy:
        # 1. Try to find the image by iterating (for small subsets) or by index if ID is numeric.
        # 2. If the ID is not found, we log and return None.
        
        found_image = None
        count = 0
        
        # Limit iteration to avoid hanging if ID is not found (safety break)
        # In a production system, we would use a dataset index or map function.
        max_iter = 10000 
        
        for item in dataset:
            if count >= max_iter:
                logger.warning(f"Stopped searching for image {image_id} after {max_iter} items.")
                break
            
            # Check if this item matches the requested ID
            # COCO images usually have an 'id' field
            if str(item.get("id", "")) == image_id or str(item.get("image_id", "")) == image_id:
                found_image = item
                break
            
            count += 1
        
        if found_image:
            logger.info(f"Successfully fetched image {image_id}")
            return found_image
        else:
            logger.warning(f"Image {image_id} not found in the dataset stream.")
            return None

    except Exception as e:
        # Log the specific error
        error_msg = FETCH_FAILED_ERROR.format(image_id)
        log_error(str(e), log_file_path=_get_manipulation_error_log_path())
        logger.error(f"{error_msg}: {str(e)}")
        return None

def load_image_metadata(image_id: str) -> Optional[Dict[str, Any]]:
    """
    Load metadata for a specific image from the generated YAML files.
    
    Args:
        image_id: The unique identifier for the image.
        
    Returns:
        A dictionary containing the metadata if found, None otherwise.
        
    Raises:
        Logs error and returns None if metadata is missing.
    """
    metadata_dir = get_stimuli_metadata_dir()
    metadata_path = metadata_dir / f"{image_id}.yaml"
    
    if not metadata_path.exists():
        error_msg = MISSING_METADATA_ERROR.format(image_id)
        log_error(error_msg, log_file_path=_get_manipulation_error_log_path())
        logger.warning(error_msg)
        return None
    
    try:
        import yaml
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f)
        return metadata
    except Exception as e:
        error_msg = f"Failed to parse metadata for image {image_id}: {str(e)}"
        log_error(error_msg, log_file_path=_get_manipulation_error_log_path())
        logger.error(error_msg)
        return None

def process_image_with_error_handling(image_id: str, process_func, *args, **kwargs) -> Optional[Image]:
    """
    Wrapper function to process an image with comprehensive error handling.
    
    This function attempts to load metadata and fetch the image. If any step fails,
    it logs the error and returns None, allowing the pipeline to continue.
    
    Args:
        image_id: The unique identifier for the image.
        process_func: A callable that takes the image data and returns an Image object.
        *args: Additional positional arguments for process_func.
        **kwargs: Additional keyword arguments for process_func.
        
    Returns:
        An Image object if successful, None otherwise.
    """
    # Step 1: Load Metadata
    metadata = load_image_metadata(image_id)
    if metadata is None:
        # Metadata missing is a fatal error for this specific image
        logger.warning(f"Skipping image {image_id} due to missing metadata.")
        return None
    
    # Step 2: Fetch Real Image Data (if needed by process_func)
    # In many cases, process_func might just need the ID and metadata, 
    # but if it needs the actual image bytes, we fetch here.
    # For this generic wrapper, we assume process_func handles the fetch if needed,
    # or we pass the metadata which contains paths.
    
    try:
        # Execute the processing function
        result = process_func(image_id, metadata, *args, **kwargs)
        
        if result is None:
            error_msg = PROCESSING_FAILED_ERROR.format(image_id)
            log_error(error_msg, log_file_path=_get_manipulation_error_log_path())
            logger.warning(error_msg)
            return None
            
        return result
        
    except Exception as e:
        error_msg = f"Processing error for image {image_id}: {str(e)}"
        log_error(error_msg, log_file_path=_get_manipulation_error_log_path())
        logger.error(error_msg)
        return None

def main():
    """
    Main entry point for testing the loader module.
    Demonstrates fetching and processing logic.
    """
    logger.info("Starting loader module test...")
    
    # Example: Try to load metadata for a known mock ID or a real one if available
    # Since we don't have a guaranteed real ID without running the downloader first,
    # we test the error handling path.
    
    test_ids = ["non_existent_id_12345", "another_fake_id"]
    
    for tid in test_ids:
        logger.info(f"Testing fetch for: {tid}")
        img_data = fetch_real_dataset_image(tid)
        if img_data:
            logger.info(f"Found: {img_data.get('id')}")
        else:
            logger.info("Fetch returned None (expected for fake IDs)")
        
        meta = load_image_metadata(tid)
        if meta:
            logger.info(f"Metadata loaded: {meta}")
        else:
            logger.info("Metadata missing (expected for fake IDs)")

if __name__ == "__main__":
    main()