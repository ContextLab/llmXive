"""
Batch processing logic for User Story 2 to handle memory constraints.

This module implements a batch processing pipeline that processes subjects
in chunks to keep peak RAM usage below 7GB. It coordinates loading,
processing, and saving of connectivity metrics without loading all
subjects into memory simultaneously.
"""
import os
import gc
import logging
from typing import List, Dict, Generator, Optional, Any, Tuple

import numpy as np
import pandas as pd

from code.config import get_config
from code.features.connectivity import extract_subject_connectivity_metrics
from code.features.aggregation import save_metrics_to_csv
from code.data.paths import get_processed_path, get_raw_path, ensure_dir
from code.utils.logging import log_error, log_warning, init_logging

logger = logging.getLogger(__name__)

# Configuration for batch processing
BATCH_SIZE = 50  # Process 50 subjects at a time
MEMORY_THRESHOLD_GB = 7.0  # Target peak RAM limit

def get_valid_subject_list() -> List[str]:
    """
    Get list of subjects that have been preprocessed and are ready for connectivity analysis.
    
    Returns:
        List of subject IDs that have valid preprocessed time-series data.
    """
    config = get_config()
    processed_path = get_processed_path()
    
    # Look for parcellated time-series files
    # Expected naming: <subject_id>_parcels.npy or similar
    valid_subjects = []
    
    if not os.path.exists(processed_path):
        logger.warning(f"Processed path does not exist: {processed_path}")
        return valid_subjects
    
    # Scan for subject directories or files
    # HCP subjects are typically named like 100307, 100408, etc.
    for item in os.listdir(processed_path):
        item_path = os.path.join(processed_path, item)
        if os.path.isdir(item_path):
            # Check if this directory contains expected data
            # Look for parcellated time-series file
            time_series_file = os.path.join(item_path, 'parcels_timeseries.npy')
            if os.path.exists(time_series_file):
                valid_subjects.append(item)
    
    logger.info(f"Found {len(valid_subjects)} valid subjects for processing")
    return valid_subjects

def load_subject_timeseries(subject_id: str) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load parcellated time-series for a single subject.
    
    Args:
        subject_id: The subject identifier.
        
    Returns:
        Tuple of (time_series_array, metadata_dict)
        time_series_array: Shape (n_timepoints, n_rois)
        metadata_dict: Subject metadata including age, sex, etc.
        
    Raises:
        FileNotFoundError: If the subject's time-series file is not found.
    """
    processed_path = get_processed_path()
    subject_dir = os.path.join(processed_path, subject_id)
    time_series_file = os.path.join(subject_dir, 'parcels_timeseries.npy')
    
    if not os.path.exists(time_series_file):
        raise FileNotFoundError(f"Time-series file not found for subject {subject_id}")
    
    # Load time-series data
    time_series = np.load(time_series_file)
    
    # Load metadata if available
    metadata_file = os.path.join(subject_dir, 'metadata.json')
    metadata = {}
    if os.path.exists(metadata_file):
        import json
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    
    logger.debug(f"Loaded time-series for {subject_id}: shape {time_series.shape}")
    return time_series, metadata

def process_subject_batch(subject_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Process a batch of subjects to compute connectivity metrics.
    
    Args:
        subject_ids: List of subject IDs to process.
        
    Returns:
        List of dictionaries containing metrics for each subject.
    """
    results = []
    
    for subject_id in subject_ids:
        try:
            logger.info(f"Processing subject {subject_id}")
            
            # Load time-series
            time_series, metadata = load_subject_timeseries(subject_id)
            
            # Compute connectivity metrics
            metrics = extract_subject_connectivity_metrics(time_series, subject_id)
            
            # Add metadata to results
            metrics.update(metadata)
            results.append(metrics)
            
            # Explicitly delete large arrays to free memory
            del time_series
            gc.collect()
            
        except Exception as e:
            logger.error(f"Failed to process subject {subject_id}: {str(e)}")
            # Continue with next subject rather than failing the entire batch
            continue
    
    return results

def run_batch_processing_pipeline() -> pd.DataFrame:
    """
    Run the full batch processing pipeline for all valid subjects.
    
    This function:
    1. Gets list of valid subjects
    2. Processes them in batches to manage memory
    3. Aggregates results and saves to CSV
    
    Returns:
        DataFrame containing all subject metrics.
    """
    config = get_config()
    init_logging()
    
    logger.info("Starting batch processing pipeline")
    
    # Get valid subjects
    valid_subjects = get_valid_subject_list()
    
    if not valid_subjects:
        logger.warning("No valid subjects found for processing")
        return pd.DataFrame()
    
    logger.info(f"Processing {len(valid_subjects)} subjects in batches of {BATCH_SIZE}")
    
    all_results = []
    
    # Process in batches
    for i in range(0, len(valid_subjects), BATCH_SIZE):
        batch_subjects = valid_subjects[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(valid_subjects) + BATCH_SIZE - 1) // BATCH_SIZE
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch_subjects)} subjects)")
        
        # Process batch
        batch_results = process_subject_batch(batch_subjects)
        all_results.extend(batch_results)
        
        # Force garbage collection between batches
        gc.collect()
        
        logger.info(f"Completed batch {batch_num}/{total_batches}")
    
    # Convert to DataFrame
    if all_results:
        results_df = pd.DataFrame(all_results)
        
        # Save metrics to CSV
        save_metrics_to_csv(results_df)
        
        logger.info(f"Successfully processed {len(results_df)} subjects")
        logger.info(f"Results saved to data/processed/metrics.csv")
        
        return results_df
    else:
        logger.warning("No results were generated from the batch processing")
        return pd.DataFrame()

def main():
    """Main entry point for batch processing."""
    logger.info("Batch processing module - main entry point")
    
    try:
        results = run_batch_processing_pipeline()
        
        if len(results) > 0:
            logger.info(f"Pipeline completed successfully. Processed {len(results)} subjects.")
            return 0
        else:
            logger.warning("Pipeline completed but no subjects were processed.")
            return 1
            
    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())