import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from code.config import get_path, ensure_dirs
from code.logging_utils import warn_missing_metadata

# Configure logger
logger = logging.getLogger(__name__)

# Valid brain regions as per spec (T006a)
VALID_BRAIN_REGIONS = {"Hippocampus", "Prefrontal Cortex"}
VALID_PATHOLOGY_STATUSES = {"Normal", "Early AD"}

def load_image(image_path: Path) -> Optional[np.ndarray]:
    """
    Load an image file as a numpy array.
    Currently a placeholder for the actual loading logic (e.g., using PIL or OpenCV).
    In the context of T012a (metadata parsing), this is a stub to satisfy the pipeline flow,
    but the core logic focuses on metadata extraction.
    """
    if not image_path.exists():
        logger.warning(f"Image file not found: {image_path}")
        return None
    
    # Placeholder for actual image loading
    # In a real scenario: return cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    logger.debug(f"Loading image: {image_path}")
    return None

def parse_metadata_from_filename(filename: str) -> Dict[str, Any]:
    """
    Parse metadata (brain_region, pathology_status) from the image filename.
    Expected format: <subject_id>_<brain_region>_<pathology_status>_<timestamp>.png
    Example: sub_001_Hippocampus_Normal_20231027.png
    
    Returns a dictionary with parsed fields.
    """
    metadata = {}
    
    # Regex to capture parts: subject, region, status, timestamp
    # We assume the region and status are the 2nd and 3rd parts separated by underscore
    pattern = r"^(.+)_(.+)_(.+)_(.+)\.(png|jpg|jpeg|tif|tiff)$"
    match = re.match(pattern, filename, re.IGNORECASE)
    
    if not match:
        logger.warning(f"Filename does not match expected pattern: {filename}")
        # Attempt to return partial metadata if possible, or empty
        return metadata
    
    subject_id = match.group(1)
    region_candidate = match.group(2)
    status_candidate = match.group(3)
    
    # Validate Brain Region
    if region_candidate in VALID_BRAIN_REGIONS:
        metadata['brain_region'] = region_candidate
    else:
        logger.warning(f"Invalid brain region '{region_candidate}' in {filename}. Expected one of {VALID_BRAIN_REGIONS}")
        # Do not set brain_region if invalid
    
    # Validate Pathology Status
    if status_candidate in VALID_PATHOLOGY_STATUSES:
        metadata['pathology_status'] = status_candidate
    else:
        logger.warning(f"Invalid pathology status '{status_candidate}' in {filename}. Expected one of {VALID_PATHOLOGY_STATUSES}")
        # Do not set pathology_status if invalid
    
    metadata['subject_id'] = subject_id
    
    return metadata

def validate_brain_region(brain_region: Optional[str]) -> bool:
    """
    Validate if the brain_region is one of the allowed values.
    """
    if not brain_region:
        return False
    return brain_region in VALID_BRAIN_REGIONS

def ingest_directory(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Ingest all images from a directory, parsing metadata and validating fields.
    Implements FR-001 (Parse metadata) and FR-008 (Exclusion logic for missing/invalid tags).
    
    Returns a list of dictionaries containing image path and valid metadata.
    Images with missing or invalid brain_region/pathology_status are excluded from the return list
    but logged as warnings.
    """
    if not data_dir.exists():
        logger.error(f"Data directory does not exist: {data_dir}")
        return []
    
    ingested_records = []
    image_extensions = {'.png', '.jpg', '.jpeg', '.tif', '.tiff'}
    
    for file_path in data_dir.iterdir():
        if file_path.suffix.lower() not in image_extensions:
            continue
        
        filename = file_path.name
        metadata = parse_metadata_from_filename(filename)
        
        # FR-001: Log missing metadata fields
        missing_fields = []
        if 'brain_region' not in metadata:
            missing_fields.append('brain_region')
        if 'pathology_status' not in metadata:
            missing_fields.append('pathology_status')
        
        if missing_fields:
            warn_missing_metadata(filename, missing_fields)
            # FR-008: Exclude subjects missing tags
            logger.warning(f"Excluding {filename} due to missing or invalid metadata fields: {missing_fields}")
            continue
        
        # If we reach here, metadata is valid
        record = {
            'image_path': str(file_path),
            'filename': filename,
            'subject_id': metadata.get('subject_id'),
            'brain_region': metadata['brain_region'],
            'pathology_status': metadata['pathology_status']
        }
        ingested_records.append(record)
        logger.info(f"Ingested: {filename} -> {record['brain_region']}, {record['pathology_status']}")
    
    logger.info(f"Ingestion complete. Processed {len(ingested_records)} valid records.")
    return ingested_records

def run_ingestion_pipeline(config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Main entry point for the data ingestion pipeline.
    Loads configuration, determines input paths, and executes ingestion.
    
    Args:
        config: Optional configuration dictionary. If None, uses defaults from code/config.py.
    
    Returns:
        List of valid record dictionaries.
    """
    if config is None:
        from code.config import load_config
        config = load_config()
    
    # Determine data root
    # Assuming raw data is in data/raw/ based on T001
    data_root = get_path("data", "raw")
    ensure_dirs([data_root])
    
    logger.info(f"Starting ingestion pipeline from {data_root}")
    records = ingest_directory(data_root)
    
    return records
def exclude_missing_cognitive_or_region(records: List[Dict[str, Any]], cognitive_scores: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
    """
    Implements FR-008: Exclusion logic.
    
    Excludes subjects missing cognitive scores or untagged brain regions.
    Also handles the edge case of empty fields of view (if image path is invalid or empty).
    
    Args:
        records: List of ingested record dictionaries from ingest_directory.
        cognitive_scores: Optional dictionary mapping subject_id to cognitive score.
                        If provided, records missing a score for their subject_id are excluded.
                        If None, this check is skipped (assuming synthetic data or external join later).
    
    Returns:
        Filtered list of records.
    """
    filtered_records = []
    
    for record in records:
        # Check 1: Ensure brain_region is present (should be guaranteed by ingest_directory, but double-check)
        if not record.get('brain_region'):
            logger.warning(f"Excluding {record['filename']}: Missing brain_region tag.")
            continue
        
        # Check 2: Ensure pathology_status is present
        if not record.get('pathology_status'):
            logger.warning(f"Excluding {record['filename']}: Missing pathology_status tag.")
            continue

        # Check 3: Cognitive Score exclusion (if scores provided)
        if cognitive_scores is not None:
            subject_id = record.get('subject_id')
            if subject_id is None:
                logger.warning(f"Excluding {record['filename']}: Missing subject_id for cognitive score lookup.")
                continue
            
            if subject_id not in cognitive_scores:
                logger.warning(f"Excluding {record['filename']} (Subject {subject_id}): Missing cognitive score.")
                continue
            # Optionally attach the score to the record for downstream use
            record['cognitive_score'] = cognitive_scores[subject_id]
        
        # Check 4: Empty Field of View / Invalid Image Path
        # If the image path is empty or the file does not exist, skip it.
        image_path = record.get('image_path')
        if not image_path:
            logger.warning(f"Excluding {record['filename']}: Empty image path.")
            continue
        
        path_obj = Path(image_path)
        if not path_obj.exists():
            logger.warning(f"Excluding {record['filename']}: Image file not found at {image_path}.")
            continue
        
        # If all checks pass, include the record
        filtered_records.append(record)
    
    logger.info(f"Exclusion logic complete. Retained {len(filtered_records)} of {len(records)} records.")
    return filtered_records

def run_ingestion_pipeline_with_exclusion(config: Optional[Dict[str, Any]] = None, cognitive_scores: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
    """
    Extended ingestion pipeline that includes FR-008 exclusion logic.
    
    Args:
        config: Optional configuration dictionary.
        cognitive_scores: Optional mapping of subject_id to cognitive score for exclusion logic.
    
    Returns:
        List of valid, non-excluded record dictionaries.
    """
    if config is None:
        from code.config import load_config
        config = load_config()
    
    data_root = get_path("data", "raw")
    ensure_dirs([data_root])
    
    logger.info(f"Starting ingestion pipeline with exclusion from {data_root}")
    
    # Step 1: Ingest and parse metadata
    records = ingest_directory(data_root)
    
    # Step 2: Apply exclusion logic (FR-008)
    filtered_records = exclude_missing_cognitive_or_region(records, cognitive_scores)
    
    return filtered_records