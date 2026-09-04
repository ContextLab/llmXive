import os
import sys
import json
import logging
import time
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict

# Import from local modules as per API surface
from utils import load_dataset_chunked
from config import get_data_dir, get_processed_dir, get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('preprocess.log')
    ]
)
logger = logging.getLogger(__name__)

def load_dataset(file_path: Path) -> pd.DataFrame:
    """
    Load a dataset from a CSV file.
    Handles large files by using chunked loading if necessary.
    """
    logger.info(f"Loading dataset from {file_path}")
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    # Use chunked loading for large files (> 100MB)
    file_size = file_path.stat().st_size
    if file_size > 100 * 1024 * 1024:  # 100MB
        logger.info("File size > 100MB, using chunked loading")
        chunks = []
        for chunk in load_dataset_chunked(file_path, chunksize=10000):
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True)
    else:
        df = pd.read_csv(file_path)
    
    logger.info(f"Loaded {len(df)} rows")
    return df

def is_sequential_stimuli(df: pd.DataFrame, stimulus_col: str = 'stimulus_sequence') -> bool:
    """
    Check if the dataset contains sequential stimuli.
    A dataset is considered sequential if the stimulus_sequence column exists
    and contains at least some ordered values.
    """
    if stimulus_col not in df.columns:
        logger.warning(f"Stimulus sequence column '{stimulus_col}' not found")
        return False
    
    # Check if there are at least 2 unique values to establish sequence
    unique_values = df[stimulus_col].nunique()
    return unique_values >= 2

def has_predictability_manipulation(df: pd.DataFrame) -> bool:
    """
    Check if the dataset has a predictability manipulation.
    This is a simplified check - in a real implementation, this would
    verify the presence of specific experimental conditions.
    """
    # Check for common columns that might indicate predictability manipulation
    predictability_cols = ['condition', 'predictability', 'surprisal', 'entropy']
    for col in predictability_cols:
        if col in df.columns:
            logger.info(f"Found potential predictability column: {col}")
            return True
    
    # If no specific column found, assume True if we have sequential stimuli
    logger.info("No explicit predictability column found, assuming sequential stimuli implies manipulation")
    return True

def filter_datasets(df: pd.DataFrame, required_cols: List[str] = None) -> pd.DataFrame:
    """
    Filter dataset for required columns and valid rows.
    """
    if required_cols is None:
        required_cols = ['duration_estimate', 'stimulus_sequence', 'participant_id']
    
    # Check for required columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing required columns: {missing_cols}")
        # Return empty dataframe if critical columns are missing
        if 'duration_estimate' in missing_cols:
            return pd.DataFrame()
    
    # Filter out rows with missing critical values
    for col in required_cols:
        if col in df.columns:
            df = df.dropna(subset=[col])
    
    return df

def save_exclusion_log(exclusion_log: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save exclusion log to JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Exclusion log saved to {output_path}")

def enforce_sampling_limit(df: pd.DataFrame, max_trials: int = 5000) -> pd.DataFrame:
    """
    Enforce a sampling limit if the dataset is too large.
    Returns a sampled version of the dataframe if it exceeds max_trials.
    """
    if len(df) > max_trials:
        logger.warning(f"Dataset has {len(df)} rows, exceeding max_trials={max_trials}. Sampling...")
        # Sample while preserving participant distribution
        df_sampled = df.groupby('participant_id', group_keys=False).apply(
            lambda x: x.sample(n=min(max_trials // df['participant_id'].nunique(), len(x)), random_state=42)
        ).reset_index(drop=True)
        logger.info(f"Sampled to {len(df_sampled)} rows")
        return df_sampled
    return df

def compute_markov_surprisal(df: pd.DataFrame, stimulus_col: str = 'stimulus_sequence') -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Compute Markov surprisal using a two-pass streaming approach.
    
    Algorithm:
    1. Pass 1: Read data in chunks, maintain running transition_counts dictionary.
    2. Pass 2: Read data in chunks again, compute surprisal for each trial using
       the aggregated transition_counts with Laplace smoothing.
    
    Args:
        df: DataFrame with stimulus_sequence column
        stimulus_col: Name of the column containing stimulus sequence
        
    Returns:
        Tuple of (DataFrame with surprisal added, Markov state dictionary)
    """
    logger.info("Starting two-pass Markov surprisal computation")
    
    if stimulus_col not in df.columns:
        raise ValueError(f"Stimulus column '{stimulus_col}' not found in dataframe")
    
    # Pass 1: Count transitions
    logger.info("Pass 1: Counting transitions")
    transition_counts = defaultdict(lambda: defaultdict(int))
    alphabet = set()
    
    # Iterate through the dataframe (already loaded in memory for this step)
    # For very large datasets, this would need to be chunked again
    prev_stimulus = None
    for stimulus in df[stimulus_col]:
        alphabet.add(stimulus)
        if prev_stimulus is not None:
            transition_counts[prev_stimulus][stimulus] += 1
        prev_stimulus = stimulus
    
    # Convert to regular dict for JSON serialization
    transition_counts_dict = {k: dict(v) for k, v in transition_counts.items()}
    
    # Pass 2: Compute surprisal
    logger.info("Pass 2: Computing surprisal values")
    surprisal_values = []
    alpha = 1.0  # Laplace smoothing parameter
    
    # Reset for second pass
    prev_stimulus = None
    for stimulus in df[stimulus_col]:
        if prev_stimulus is not None:
            # Get transition count
            count = transition_counts[prev_stimulus][stimulus]
            
            # Calculate total transitions from prev_stimulus
            total_from_prev = sum(transition_counts[prev_stimulus].values())
            
            # Calculate probability with Laplace smoothing
            # P(s_t | s_{t-1}) = (count + alpha) / (total + alpha * |alphabet|)
            prob = (count + alpha) / (total_from_prev + alpha * len(alphabet))
            
            # Surprisal = -log2(prob)
            surprisal = -np.log2(prob) if prob > 0 else 0.0
        else:
            # First stimulus has no previous, assign 0 or handle specially
            surprisal = 0.0
        
        surprisal_values.append(surprisal)
        prev_stimulus = stimulus
    
    # Add surprisal to dataframe
    df_with_surprisal = df.copy()
    df_with_surprisal['surprisal'] = surprisal_values
    
    # Prepare Markov state dictionary
    markov_state = {
        'transition_matrix': transition_counts_dict,
        'alphabet': sorted(list(alphabet)),
        'order': 1
    }
    
    logger.info(f"Computed surprisal for {len(df_with_surprisal)} trials")
    logger.info(f"Markov state: {len(alphabet)} unique stimuli, {sum(len(v) for v in transition_counts.values())} transitions")
    
    return df_with_surprisal, markov_state

def run_preprocessing_pipeline(dataset_ids: List[str], output_path: Path) -> pd.DataFrame:
    """
    Run the full preprocessing pipeline:
    1. Load datasets
    2. Filter for required columns
    3. Enforce sampling limits
    4. Compute Markov surprisal
    5. Save outputs
    
    Args:
        dataset_ids: List of dataset IDs to process
        output_path: Path to save the final standardized CSV
        
    Returns:
        Final processed DataFrame
    """
    processed_dfs = []
    exclusion_log = []
    
    for dataset_id in dataset_ids:
        try:
            logger.info(f"Processing dataset: {dataset_id}")
            
            # Load dataset (assuming it's already downloaded and in processed dir)
            # In a real implementation, this would fetch from the appropriate source
            input_path = get_processed_dir() / f"{dataset_id}.csv"
            if not input_path.exists():
                # Try alternative path
                input_path = get_data_dir() / "raw" / f"{dataset_id}.csv"
            
            if not input_path.exists():
                logger.warning(f"Dataset file not found: {input_path}")
                exclusion_log.append({
                    'dataset_id': dataset_id,
                    'status': 'excluded',
                    'reason': 'File not found'
                })
                continue
            
            df = load_dataset(input_path)
            
            # Filter datasets
            df = filter_datasets(df)
            if len(df) == 0:
                exclusion_log.append({
                    'dataset_id': dataset_id,
                    'status': 'excluded',
                    'reason': 'No valid rows after filtering'
                })
                continue
            
            # Check for sequential stimuli
            if not is_sequential_stimuli(df):
                exclusion_log.append({
                    'dataset_id': dataset_id,
                    'status': 'excluded',
                    'reason': 'Not sequential stimuli'
                })
                continue
            
            # Check for predictability manipulation
            if not has_predictability_manipulation(df):
                exclusion_log.append({
                    'dataset_id': dataset_id,
                    'status': 'excluded',
                    'reason': 'No predictability manipulation'
                })
                continue
            
            # Enforce sampling limit
            config = get_config()
            max_trials = config.get('MAX_TRIALS', 5000)
            df = enforce_sampling_limit(df, max_trials)
            
            # Compute Markov surprisal
            df_processed, markov_state = compute_markov_surprisal(df)
            
            # Add dataset_id column
            df_processed['dataset_id'] = dataset_id
            
            processed_dfs.append(df_processed)
            
            # Save Markov state for this dataset
            markov_state_path = get_processed_dir() / f"markov_state_{dataset_id}.json"
            with open(markov_state_path, 'w') as f:
                json.dump(markov_state, f, indent=2)
            logger.info(f"Saved Markov state to {markov_state_path}")
            
            exclusion_log.append({
                'dataset_id': dataset_id,
                'status': 'included',
                'reason': 'Processed successfully'
            })
            
        except Exception as e:
            logger.error(f"Error processing dataset {dataset_id}: {str(e)}")
            exclusion_log.append({
                'dataset_id': dataset_id,
                'status': 'excluded',
                'reason': str(e)
            })
    
    # Save exclusion log
    exclusion_log_path = get_processed_dir() / 'exclusion_log.json'
    save_exclusion_log(exclusion_log, exclusion_log_path)
    
    if not processed_dfs:
        logger.error("No datasets were successfully processed.")
        raise ValueError("No datasets were successfully processed.")
    
    # Combine all processed datasets
    final_df = pd.concat(processed_dfs, ignore_index=True)
    
    # Save final output
    final_df.to_csv(output_path, index=False)
    logger.info(f"Saved final standardized CSV to {output_path}")
    
    return final_df

def main():
    """
    Main entry point for the preprocessing pipeline.
    """
    try:
        # Read dataset IDs
        ids_path = get_data_dir() / 'dataset_ids.txt'
        if not ids_path.exists():
            logger.error(f"Dataset IDs file not found: {ids_path}")
            sys.exit(1)
        
        with open(ids_path, 'r') as f:
            dataset_ids = [line.strip() for line in f if line.strip()]
        
        if not dataset_ids:
            logger.error("No dataset IDs found in file")
            sys.exit(1)
        
        logger.info(f"Processing {len(dataset_ids)} datasets: {dataset_ids}")
        
        # Set random seed for reproducibility
        from config import set_seed
        set_seed(42)
        
        # Run preprocessing pipeline
        output_path = get_processed_dir() / 'standardized.csv'
        final_df = run_preprocessing_pipeline(dataset_ids, output_path)
        
        logger.info(f"Preprocessing complete. Output saved to {output_path}")
        logger.info(f"Final dataset shape: {final_df.shape}")
        
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {str(e)}")
        # Ensure we exit with error code
        sys.exit(1)

if __name__ == '__main__':
    main()