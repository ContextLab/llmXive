"""
Implementation of T014: Filtering logic to exclude datasets lacking sequential stimuli
or predictability manipulations.

This module implements FR-002 by checking for sequential stimulus properties and
predictability manipulations in loaded datasets. It logs exclusion reasons and
produces a filtered dataset.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from config import get_data_dir
from preprocess import load_dataset, is_sequential_stimuli, has_predictability_manipulation

EXCLUSION_LOG_PATH = Path("data/exclusion_log.json")

def load_exclusion_log() -> List[Dict[str, Any]]:
    """Load existing exclusion log or return empty list."""
    if EXCLUSION_LOG_PATH.exists():
        with open(EXCLUSION_LOG_PATH, 'r') as f:
            return json.load(f)
    return []

def save_exclusion_log(log_entries: List[Dict[str, Any]]) -> None:
    """Save exclusion log to file."""
    EXCLUSION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EXCLUSION_LOG_PATH, 'w') as f:
        json.dump(log_entries, f, indent=2)

def log_exclusion(dataset_id: str, reason: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log an exclusion reason."""
    log_entries = load_exclusion_log()
    entry = {
        "dataset_id": dataset_id,
        "reason": reason,
        "details": details or {},
        "status": "excluded"
    }
    log_entries.append(entry)
    save_exclusion_log(log_entries)
    logger.warning(f"Excluded dataset {dataset_id}: {reason}")

def log_inclusion(dataset_id: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log that a dataset passed all filters."""
    log_entries = load_exclusion_log()
    entry = {
        "dataset_id": dataset_id,
        "reason": "passed_filters",
        "details": details or {},
        "status": "included"
    }
    log_entries.append(entry)
    save_exclusion_log(log_entries)
    logger.info(f"Included dataset {dataset_id}")

def check_sequential_stimuli(df: pd.DataFrame, dataset_id: str) -> Tuple[bool, Optional[str]]:
    """
    Check if dataset has sequential stimuli.
    
    Returns (is_sequential, reason_if_not).
    """
    # Check for sequential stimulus columns
    sequential_columns = ['stimulus_sequence', 'stimulus_order', 'trial_order', 'sequence_index']
    has_seq_col = any(col in df.columns for col in sequential_columns)
    
    if not has_seq_col:
        return False, "Missing sequential stimulus column (stimulus_sequence, stimulus_order, trial_order, or sequence_index)"
    
    # Check if the sequence column has meaningful sequential data
    seq_col = next(col for col in sequential_columns if col in df.columns)
    unique_values = df[seq_col].nunique()
    total_rows = len(df)
    
    if unique_values < 2:
        return False, f"Stimulus sequence column '{seq_col}' has only {unique_values} unique value(s), no sequential variation"
    
    # Check for temporal ordering (if time columns exist)
    time_columns = ['timestamp', 'time', 'reaction_time', 'response_time', 'duration']
    has_time_col = any(col in df.columns for col in time_columns)
    
    if has_time_col:
        time_col = next(col for col in time_columns if col in df.columns)
        if df[time_col].isna().all():
            logger.warning(f"Dataset {dataset_id}: Time column '{time_col}' exists but all values are NaN")
    
    return True, None

def check_predictability_manipulation(df: pd.DataFrame, dataset_id: str) -> Tuple[bool, Optional[str]]:
    """
    Check if dataset has predictability manipulations.
    
    Returns (has_manipulation, reason_if_not).
    """
    # Check for predictability-related columns
    predictability_columns = [
        'predictability', 'surprisal', 'probability', 'transition_prob',
        'condition', 'manipulation', 'predictive_cue', 'context',
        'expected', 'prediction_error'
    ]
    
    has_pred_col = any(col in df.columns for col in predictability_columns)
    
    if not has_pred_col:
        # Check if we can infer predictability from stimulus patterns
        sequential_columns = ['stimulus_sequence', 'stimulus_order', 'trial_order', 'sequence_index']
        seq_col = next((col for col in sequential_columns if col in df.columns), None)
        
        if seq_col:
            # Check if there are repeated patterns that suggest predictability
            unique_patterns = df[seq_col].nunique()
            if unique_patterns > 10:  # Arbitrary threshold for "complex" sequences
                logger.info(f"Dataset {dataset_id}: No explicit predictability column, but has {unique_patterns} unique sequence values")
                # Still require some form of predictability manipulation
                return False, "No explicit predictability manipulation column found and sequence complexity insufficient"
            else:
                return False, "No explicit predictability manipulation column found"
        else:
            return False, "No predictability manipulation column and no sequential stimulus column"
    
    # Verify the predictability column has meaningful variation
    pred_col = next(col for col in predictability_columns if col in df.columns)
    pred_data = df[pred_col]
    
    if pred_data.isna().all():
        return False, f"Predictability column '{pred_col}' contains only NaN values"
    
    unique_pred = pred_data.nunique()
    if unique_pred < 2:
        return False, f"Predictability column '{pred_col}' has only {unique_pred} unique value(s), no variation for manipulation"
    
    # Check for condition labels that might indicate manipulation groups
    condition_columns = ['condition', 'group', 'manipulation_type', 'trial_type']
    has_condition = any(col in df.columns for col in condition_columns)
    
    if not has_condition:
        logger.warning(f"Dataset {dataset_id}: No condition column found, assuming single-group analysis")
    
    return True, None

def filter_datasets(datasets: List[Dict[str, Any]], processed_dir: Path) -> List[Dict[str, Any]]:
    """
    Filter datasets based on sequential stimuli and predictability manipulation criteria.
    
    Args:
        datasets: List of dataset metadata dictionaries
        processed_dir: Directory to save processed data
        
    Returns:
        List of datasets that passed all filters
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    filtered_datasets = []
    
    for dataset_meta in datasets:
        dataset_id = dataset_meta.get('dataset_id', 'unknown')
        file_path = dataset_meta.get('file_path')
        
        if not file_path or not Path(file_path).exists():
            logger.error(f"Dataset {dataset_id}: File not found at {file_path}")
            log_exclusion(dataset_id, "file_not_found", {"file_path": file_path})
            continue
        
        try:
            df = load_dataset(file_path)
            
            # Check sequential stimuli
            is_seq, seq_reason = check_sequential_stimuli(df, dataset_id)
            if not is_seq:
                log_exclusion(dataset_id, "non_sequential_stimuli", {"reason": seq_reason})
                continue
            
            # Check predictability manipulation
            has_pred, pred_reason = check_predictability_manipulation(df, dataset_id)
            if not has_pred:
                log_exclusion(dataset_id, "no_predictability_manipulation", {"reason": pred_reason})
                continue
            
            # Dataset passed all filters
            dataset_meta['status'] = 'included'
            dataset_meta['filter_results'] = {
                'sequential_stimuli': True,
                'predictability_manipulation': True
            }
            filtered_datasets.append(dataset_meta)
            log_inclusion(dataset_id, dataset_meta['filter_results'])
            
            # Save filtered dataset
            output_path = processed_dir / f"{dataset_id}_filtered.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"Saved filtered dataset to {output_path}")
            
        except Exception as e:
            logger.error(f"Error processing dataset {dataset_id}: {str(e)}")
            log_exclusion(dataset_id, "processing_error", {"error": str(e)})
            continue
    
    return filtered_datasets

def run_filtering_pipeline() -> Dict[str, Any]:
    """
    Run the complete filtering pipeline.
    
    Returns:
        Dictionary with pipeline results
    """
    logger.info("Starting filtering pipeline (T014)")
    
    data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    # Load datasets from README
    from download import parse_readme_datasets
    datasets = parse_readme_datasets()
    
    if not datasets:
        logger.error("No datasets found in README. Please ensure data/README.md contains verified dataset IDs.")
        return {"status": "error", "message": "No datasets found"}
    
    logger.info(f"Found {len(datasets)} datasets to process")
    
    # Filter datasets
    filtered_datasets = filter_datasets(datasets, processed_dir)
    
    logger.info(f"Filtering complete: {len(filtered_datasets)}/{len(datasets)} datasets passed")
    
    # Update README with exclusion log
    from update_readme_exclusions import run_t018
    run_t018()
    
    return {
        "status": "success",
        "total_datasets": len(datasets),
        "filtered_datasets": len(filtered_datasets),
        "excluded_datasets": len(datasets) - len(filtered_datasets),
        "exclusion_log_path": str(EXCLUSION_LOG_PATH)
    }

if __name__ == "__main__":
    result = run_filtering_pipeline()
    print(json.dumps(result, indent=2))
