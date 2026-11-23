import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import get_data_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_data_dir() -> Path:
    """Get the project data directory."""
    return get_data_dir()

def get_processed_dir() -> Path:
    """Get the processed data directory."""
    data_dir = get_data_dir()
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir

def load_exclusion_log() -> List[Dict[str, Any]]:
    """Load existing exclusion log if it exists."""
    processed_dir = get_processed_dir()
    log_path = processed_dir / "exclusion_log.json"
    if log_path.exists():
        with open(log_path, 'r') as f:
            return json.load(f)
    return []

def save_exclusion_log(exclusion_log: List[Dict[str, Any]]) -> None:
    """Save exclusion log to JSON file."""
    processed_dir = get_processed_dir()
    log_path = processed_dir / "exclusion_log.json"
    with open(log_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Exclusion log saved to {log_path}")

def log_exclusion(dataset_id: str, reason: str) -> Dict[str, Any]:
    """Log an exclusion event."""
    entry = {
        "dataset_id": dataset_id,
        "reason": reason,
        "timestamp": datetime.utcnow().isoformat()
    }
    logger.warning(f"Excluded dataset {dataset_id}: {reason}")
    return entry

def log_inclusion(dataset_id: str) -> None:
    """Log an inclusion event."""
    logger.info(f"Dataset {dataset_id} passed filtering criteria.")

def check_sequential_stimuli(df: pd.DataFrame, dataset_id: str) -> Optional[str]:
    """
    Check if dataset contains sequential stimuli.
    
    A dataset is considered sequential if:
    1. It has a 'stimulus_sequence' or 'raw_stimulus_sequence' column
    2. OR it has a 'stimulus_onset' or 'stimulus_timing' column that implies sequence
    3. OR the data can be ordered by a 'trial_id' or 'time' column with multiple distinct stimuli
    
    Returns None if sequential stimuli are found, otherwise returns a reason string.
    """
    required_cols = ['stimulus_sequence', 'raw_stimulus_sequence', 'stimulus_onset', 'stimulus_timing', 'trial_id', 'time', 'stimulus']
    available_cols = set(df.columns)
    
    # Check for explicit sequence columns
    if 'stimulus_sequence' in available_cols or 'raw_stimulus_sequence' in available_cols:
        # Verify the sequence is not empty or constant
        seq_col = 'stimulus_sequence' if 'stimulus_sequence' in available_cols else 'raw_stimulus_sequence'
        if df[seq_col].dropna().nunique() > 1:
            log_inclusion(dataset_id)
            return None
        else:
            return "Stimulus sequence exists but contains only one unique value (no variation)."
    
    # Check for timing columns that imply sequence
    if 'stimulus_onset' in available_cols or 'stimulus_timing' in available_cols:
        timing_col = 'stimulus_onset' if 'stimulus_onset' in available_cols else 'stimulus_timing'
        if df[timing_col].dropna().nunique() > 1:
            log_inclusion(dataset_id)
            return None
        else:
            return "Stimulus timing exists but contains only one unique value."
    
    # Check for trial-based structure with multiple stimuli
    if 'trial_id' in available_cols or 'time' in available_cols:
        id_col = 'trial_id' if 'trial_id' in available_cols else 'time'
        if df[id_col].nunique() > 1:
            # Check if there's a stimulus column
            if 'stimulus' in available_cols:
                if df['stimulus'].dropna().nunique() > 1:
                    log_inclusion(dataset_id)
                    return None
                else:
                    return "Multiple trials exist but all have the same stimulus."
            else:
                # No explicit stimulus column, but multiple trials exist
                # This is ambiguous, but we'll accept it as sequential if there are many trials
                if df[id_col].nunique() > 5:
                    log_inclusion(dataset_id)
                    return None
                else:
                    return "Multiple trials exist but no stimulus column and trial count is low."
    
    # No sequential structure found
    return "Dataset lacks sequential stimuli structure (no sequence, timing, or multi-trial stimulus columns)."

def check_predictability_manipulation(df: pd.DataFrame, dataset_id: str) -> Optional[str]:
    """
    Check if dataset contains predictability manipulations.
    
    A dataset has predictability manipulation if:
    1. It has a 'condition' or 'predictability' column with multiple distinct values
    2. OR it has a 'surprisal' or 'probability' column that varies
    3. OR the stimulus sequence shows statistical structure (e.g., Markov chains)
    
    Returns None if predictability manipulation is found, otherwise returns a reason string.
    """
    required_cols = ['condition', 'predictability', 'surprisal', 'probability', 'stimulus']
    available_cols = set(df.columns)
    
    # Check for explicit condition/predictability columns
    cond_cols = ['condition', 'predictability']
    for col in cond_cols:
        if col in available_cols:
            if df[col].dropna().nunique() > 1:
                log_inclusion(dataset_id)
                return None
    
    # Check for surprisal/probability columns
    prob_cols = ['surprisal', 'probability']
    for col in prob_cols:
        if col in available_cols:
            if df[col].dropna().nunique() > 1:
                log_inclusion(dataset_id)
                return None
    
    # Check if stimulus column has multiple values (implies potential predictability structure)
    if 'stimulus' in available_cols:
        if df['stimulus'].dropna().nunique() > 1:
            # Further check: if we have a sequence, we can compute transition probabilities
            # For now, if there are multiple stimuli, we assume predictability manipulation exists
            log_inclusion(dataset_id)
            return None
    
    # No predictability manipulation found
    return "Dataset lacks predictability manipulations (no condition, predictability, surprisal, or variable stimulus columns)."

def filter_datasets(dataset_ids: List[str], exclusion_log: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter datasets based on sequential stimuli and predictability manipulation criteria.
    
    Args:
        dataset_ids: List of dataset identifiers to filter
        exclusion_log: Existing exclusion log entries
        
    Returns:
        Updated exclusion log with new entries
    """
    data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    
    for dataset_id in dataset_ids:
        # Look for dataset file in raw directory
        possible_paths = [
            raw_dir / f"{dataset_id}.csv",
            raw_dir / f"{dataset_id}.parquet",
            raw_dir / f"dataset_{dataset_id}.csv",
            raw_dir / dataset_id / "data.csv",
            raw_dir / dataset_id / "dataset.csv"
        ]
        
        dataset_path = None
        for path in possible_paths:
            if path.exists():
                dataset_path = path
                break
        
        if dataset_path is None:
            # Dataset not found, log as excluded
            entry = log_exclusion(dataset_id, "Dataset file not found in raw directory.")
            exclusion_log.append(entry)
            continue
        
        try:
            # Load dataset
            if dataset_path.suffix == '.csv':
                df = pd.read_csv(dataset_path)
            elif dataset_path.suffix == '.parquet':
                df = pd.read_parquet(dataset_path)
            else:
                entry = log_exclusion(dataset_id, f"Unsupported file format: {dataset_path.suffix}")
                exclusion_log.append(entry)
                continue
            
            # Check for sequential stimuli
            seq_reason = check_sequential_stimuli(df, dataset_id)
            if seq_reason:
                entry = log_exclusion(dataset_id, seq_reason)
                exclusion_log.append(entry)
                continue
            
            # Check for predictability manipulation
            pred_reason = check_predictability_manipulation(df, dataset_id)
            if pred_reason:
                entry = log_exclusion(dataset_id, pred_reason)
                exclusion_log.append(entry)
                continue
            
            # Dataset passed all checks
            log_inclusion(dataset_id)
            
        except Exception as e:
            entry = log_exclusion(dataset_id, f"Error processing dataset: {str(e)}")
            exclusion_log.append(entry)
            logger.error(f"Failed to process dataset {dataset_id}: {e}")
    
    return exclusion_log

def run_filtering_pipeline(dataset_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Run the full filtering pipeline.
    
    Args:
        dataset_ids: List of dataset identifiers to process
        
    Returns:
        Final exclusion log
    """
    logger.info("Starting dataset filtering pipeline...")
    
    # Load existing exclusion log
    exclusion_log = load_exclusion_log()
    
    # Filter datasets
    exclusion_log = filter_datasets(dataset_ids, exclusion_log)
    
    # Save updated exclusion log
    save_exclusion_log(exclusion_log)
    
    logger.info(f"Filtering pipeline complete. {len(exclusion_log)} exclusion entries recorded.")
    return exclusion_log

def main():
    """Main entry point for the filtering script."""
    from config import get_config
    
    config = get_config()
    dataset_ids = config.get('dataset_ids', [])
    
    if not dataset_ids:
        logger.error("No dataset IDs provided in configuration.")
        sys.exit(1)
    
    exclusion_log = run_filtering_pipeline(dataset_ids)
    
    # Print summary
    print(f"\nFiltering Summary:")
    print(f"  Total datasets processed: {len(dataset_ids)}")
    print(f"  Exclusions recorded: {len(exclusion_log)}")
    print(f"  Exclusion log saved to: {get_processed_dir() / 'exclusion_log.json'}")

if __name__ == "__main__":
    main()
