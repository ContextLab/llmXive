"""
Error handling utilities for the EBSD data pipeline.

This module implements robust error handling for missing reduction levels
and corrupted EBSD files, logging warnings and allowing processing to continue
as required by US-1 Scenario 3.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from config import get_reductions, ConfigurationError
from utils.logging import get_logger

logger = get_logger(__name__)


def validate_reduction_levels(
    sample_metadata: Dict[str, Any],
    required_reductions: Optional[List[float]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate that a sample has a valid reduction level.
    
    Args:
        sample_metadata: Dictionary containing sample metadata including 'reduction'
        required_reductions: Optional list of valid reduction levels from config
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if 'reduction' not in sample_metadata:
        return False, "Missing 'reduction' field in sample metadata"
    
    reduction = sample_metadata['reduction']
    
    if reduction is None or pd.isna(reduction):
        return False, "Reduction level is None or NaN"
    
    if not isinstance(reduction, (int, float)):
        return False, f"Invalid reduction type: {type(reduction)}, expected numeric"
    
    if required_reductions is not None:
        if reduction not in required_reductions:
            return False, f"Reduction {reduction} not in allowed set: {required_reductions}"
    
    return True, None


def check_file_integrity(file_path: Path) -> Tuple[bool, Optional[str]]:
    """
    Check if an EBSD data file exists and is readable.
    
    Args:
        file_path: Path to the EBSD data file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    if not file_path.is_file():
        return False, f"Path is not a file: {file_path}"
    
    try:
        # Attempt to read file metadata
        if file_path.suffix in ['.csv', '.txt']:
            pd.read_csv(file_path, nrows=1)
        elif file_path.suffix in ['.parquet', '.h5', '.hdf5']:
            pd.read_parquet(file_path)
        else:
            # Generic check - try to read as text
            with open(file_path, 'r') as f:
                f.read(1024)
    except Exception as e:
        return False, f"File corrupted or unreadable: {str(e)}"
    
    return True, None


def handle_corrupted_file(
    file_path: Path,
    error_message: str,
    skip_mode: bool = True
) -> bool:
    """
    Handle a corrupted file by logging a warning and optionally skipping.
    
    Args:
        file_path: Path to the corrupted file
        error_message: Description of the corruption
        skip_mode: If True, skip processing this file. If False, raise an error.
        
    Returns:
        True if file was skipped successfully, False if processing should stop
    """
    logger.warning(f"Corrupted file detected: {file_path}")
    logger.warning(f"Error details: {error_message}")
    
    if skip_mode:
        logger.info(f"Skipping corrupted file and continuing with remaining files")
        return True
    else:
        logger.error(f"Cannot proceed with corrupted file: {file_path}")
        return False


def handle_missing_reduction(
    sample_id: str,
    skip_mode: bool = True
) -> bool:
    """
    Handle a sample with missing reduction level.
    
    Args:
        sample_id: Identifier for the sample
        skip_mode: If True, skip this sample. If False, raise an error.
        
    Returns:
        True if sample was skipped successfully, False if processing should stop
    """
    logger.warning(f"Sample {sample_id} has missing reduction level")
    
    if skip_mode:
        logger.info(f"Skipping sample {sample_id} and continuing")
        return True
    else:
        logger.error(f"Cannot proceed with sample {sample_id} due to missing reduction")
        return False


def process_with_error_handling(
    file_paths: List[Path],
    sample_metadata_list: List[Dict[str, Any]],
    required_reductions: Optional[List[float]] = None,
    skip_corrupted: bool = True,
    skip_missing_reduction: bool = True
) -> Tuple[List[Path], List[Dict[str, Any]], List[str]]:
    """
    Process a list of files with comprehensive error handling.
    
    This function validates reduction levels and file integrity for each sample,
    logging warnings and skipping problematic entries as configured.
    
    Args:
        file_paths: List of paths to EBSD data files
        sample_metadata_list: List of metadata dictionaries for each sample
        required_reductions: Optional list of valid reduction levels
        skip_corrupted: If True, skip corrupted files
        skip_missing_reduction: If True, skip samples with missing reduction
        
    Returns:
        Tuple of (valid_file_paths, valid_metadata_list, skipped_reasons)
    """
    if len(file_paths) != len(sample_metadata_list):
        raise ValueError("file_paths and sample_metadata_list must have same length")
    
    valid_files = []
    valid_metadata = []
    skipped_reasons = []
    
    # Get required reductions from config if not provided
    if required_reductions is None:
        try:
            required_reductions = get_reductions()
        except ConfigurationError as e:
            logger.warning(f"Could not load required reductions from config: {e}")
            logger.warning("Proceeding without reduction level validation")
            required_reductions = None
    
    for file_path, metadata in zip(file_paths, sample_metadata_list):
        sample_id = metadata.get('sample_id', str(file_path))
        
        # Check file integrity
        is_valid, error_msg = check_file_integrity(file_path)
        if not is_valid:
            if not handle_corrupted_file(file_path, error_msg, skip_corrupted):
                # Critical error, stop processing
                return [], [], skipped_reasons
            skipped_reasons.append(f"{sample_id}: Corrupted file - {error_msg}")
            continue
        
        # Validate reduction level
        is_valid, error_msg = validate_reduction_levels(metadata, required_reductions)
        if not is_valid:
            if not handle_missing_reduction(sample_id, skip_missing_reduction):
                # Critical error, stop processing
                return [], [], skipped_reasons
            skipped_reasons.append(f"{sample_id}: Missing/invalid reduction - {error_msg}")
            continue
        
        # File passed all checks
        valid_files.append(file_path)
        valid_metadata.append(metadata)
    
    logger.info(f"Processed {len(file_paths)} files: {len(valid_files)} valid, {len(skipped_reasons)} skipped")
    
    return valid_files, valid_metadata, skipped_reasons


def main():
    """
    Main entry point for error handling validation.
    
    This function demonstrates the error handling capabilities by:
    1. Loading configuration for reduction levels
    2. Creating test scenarios with valid/invalid data
    3. Processing with error handling and logging results
    """
    logger.info("Starting error handling validation")
    
    # Get reduction levels from config
    try:
        required_reductions = get_reductions()
        logger.info(f"Loaded required reductions from config: {required_reductions}")
    except ConfigurationError as e:
        logger.warning(f"Configuration error for reductions: {e}")
        required_reductions = None
    
    # Create test data paths (these may not exist, but we test the logic)
    test_files = [
        Path("data/raw/test_valid.csv"),
        Path("data/raw/test_missing_reduction.csv"),
        Path("data/raw/test_corrupted.csv"),
        Path("data/nonexistent.csv"),
    ]
    
    test_metadata = [
        {'sample_id': 'valid_sample', 'reduction': 0.2, 'material': 'Al'},
        {'sample_id': 'missing_reduction', 'material': 'Cu'},  # Missing reduction
        {'sample_id': 'invalid_reduction', 'reduction': 0.99, 'material': 'Ni'},  # Invalid reduction
        {'sample_id': 'nonexistent', 'reduction': 0.3, 'material': 'Al'},  # File doesn't exist
    ]
    
    # Process with error handling
    valid_files, valid_metadata, skipped_reasons = process_with_error_handling(
        test_files,
        test_metadata,
        required_reductions=required_reductions,
        skip_corrupted=True,
        skip_missing_reduction=True
    )
    
    logger.info(f"Valid files: {len(valid_files)}")
    logger.info(f"Skipped samples: {len(skipped_reasons)}")
    
    for reason in skipped_reasons:
        logger.info(f"  - {reason}")
    
    logger.info("Error handling validation complete")


if __name__ == "__main__":
    main()
