"""
Preprocessing module for time perception data.
Implements data loading, filtering, sampling, and Markov surprisal calculation.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

from config import get_data_dir, set_seed
from utils import load_dataset_chunked

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_dataset(dataset_id: str, raw_dir: Path) -> pd.DataFrame:
    """
    Load a dataset from the raw directory.
    
    Args:
        dataset_id: Identifier for the dataset (e.g., 'dataset_1')
        raw_dir: Path to the raw data directory
        
    Returns:
        DataFrame containing the dataset
        
    Raises:
        FileNotFoundError: If the dataset file is not found
    """
    # Try common file extensions
    extensions = ['.csv', '.tsv', '.parquet']
    for ext in extensions:
        file_path = raw_dir / f"{dataset_id}{ext}"
        if file_path.exists():
            logger.info(f"Loading dataset {dataset_id} from {file_path}")
            if ext == '.parquet':
                return pd.read_parquet(file_path)
            elif ext == '.tsv':
                return pd.read_csv(file_path, sep='\t')
            else:
                return pd.read_csv(file_path)
    
    raise FileNotFoundError(f"Dataset {dataset_id} not found in {raw_dir} with supported extensions")

def is_sequential_stimuli(df: pd.DataFrame) -> bool:
    """
    Check if the dataset contains sequential stimuli.
    
    Args:
        df: DataFrame to check
        
    Returns:
        True if sequential stimuli are present, False otherwise
    """
    # Check for columns that indicate sequential stimuli
    sequential_columns = ['stimulus_sequence', 'raw_stimulus_sequence', 'trial_order', 'stimulus_order']
    return any(col in df.columns for col in sequential_columns)

def has_predictability_manipulation(df: pd.DataFrame) -> bool:
    """
    Check if the dataset contains predictability manipulations.
    
    Args:
        df: DataFrame to check
        
    Returns:
        True if predictability manipulation is present, False otherwise
    """
    # Check for columns that indicate predictability manipulation
    predictability_columns = ['condition', 'predictability', 'probability', 'surprisal', 'transition_prob']
    return any(col in df.columns for col in predictability_columns)

def filter_datasets(dataset_ids: List[str], raw_dir: Path) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Filter datasets based on sequential stimuli and predictability manipulation.
    
    Args:
        dataset_ids: List of dataset IDs to filter
        raw_dir: Path to the raw data directory
        
    Returns:
        Tuple of (valid_dataset_ids, exclusion_log)
    """
    valid_ids = []
    exclusion_log = []
    
    for dataset_id in dataset_ids:
        try:
            df = load_dataset(dataset_id, raw_dir)
            
            # Check for sequential stimuli
            if not is_sequential_stimuli(df):
                reason = "Missing sequential stimuli columns"
                exclusion_log.append({
                    'dataset_id': dataset_id,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                })
                logger.warning(f"Excluding {dataset_id}: {reason}")
                continue
            
            # Check for predictability manipulation
            if not has_predictability_manipulation(df):
                reason = "Missing predictability manipulation columns"
                exclusion_log.append({
                    'dataset_id': dataset_id,
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                })
                logger.warning(f"Excluding {dataset_id}: {reason}")
                continue
            
            valid_ids.append(dataset_id)
            logger.info(f"Included {dataset_id}: meets all criteria")
            
        except Exception as e:
            reason = f"Error loading dataset: {str(e)}"
            exclusion_log.append({
                'dataset_id': dataset_id,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            })
            logger.error(f"Failed to process {dataset_id}: {reason}")
    
    return valid_ids, exclusion_log

def save_exclusion_log(exclusion_log: List[Dict[str, Any]], processed_dir: Path) -> None:
    """
    Save the exclusion log to a JSON file.
    
    Args:
        exclusion_log: List of exclusion records
        processed_dir: Path to the processed data directory
    """
    exclusion_path = processed_dir / 'exclusion_log.json'
    with open(exclusion_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Exclusion log saved to {exclusion_path}")

def enforce_sampling_limit(df: pd.DataFrame, max_trials: int = 5000) -> pd.DataFrame:
    """
    Enforce a sampling limit on the dataset.
    
    Args:
        df: DataFrame to sample
        max_trials: Maximum number of trials to keep
        
    Returns:
        Sampled DataFrame
    """
    if len(df) <= max_trials:
        return df
    
    logger.info(f"Sampling dataset from {len(df)} to {max_trials} trials")
    # Use a deterministic seed for reproducibility
    np.random.seed(42)
    sampled_indices = np.random.choice(len(df), size=max_trials, replace=False)
    return df.iloc[sampled_indices].reset_index(drop=True)

def compute_markov_surprisal(df: pd.DataFrame, stimulus_col: str = 'stimulus_sequence') -> pd.DataFrame:
    """
    Compute Markov surprisal using Shannon entropy of the transition.
    
    This implements a first-order Markov model where the surprisal of a stimulus
    is calculated as -log2(P(current_stimulus | previous_stimulus)).
    
    Args:
        df: DataFrame containing the data
        stimulus_col: Name of the column containing the stimulus sequence
        
    Returns:
        DataFrame with added 'surprisal' column
    """
    if stimulus_col not in df.columns:
        raise ValueError(f"Column '{stimulus_col}' not found in DataFrame")
    
    # Get the stimulus sequence
    sequence = df[stimulus_col].values
    
    # Build transition counts
    transition_counts = {}
    alphabet = sorted(list(set(sequence)))
    
    for i in range(1, len(sequence)):
        prev_stim = sequence[i-1]
        curr_stim = sequence[i]
        
        if prev_stim not in transition_counts:
            transition_counts[prev_stim] = {}
        
        if curr_stim not in transition_counts[prev_stim]:
            transition_counts[prev_stim][curr_stim] = 0
        
        transition_counts[prev_stim][curr_stim] += 1
    
    # Calculate transition probabilities
    transition_probs = {}
    for prev_stim in transition_counts:
        total = sum(transition_counts[prev_stim].values())
        transition_probs[prev_stim] = {}
        for curr_stim in transition_counts[prev_stim]:
            transition_probs[prev_stim][curr_stim] = transition_counts[prev_stim][curr_stim] / total
    
    # Compute surprisal for each transition
    surprisal_values = []
    for i in range(len(sequence)):
        if i == 0:
            # First element has no previous context, use uniform prior or skip
            # For consistency, we'll use a small epsilon to avoid log(0)
            surprisal_values.append(0.0)  # Or could use -log2(1/len(alphabet))
        else:
            prev_stim = sequence[i-1]
            curr_stim = sequence[i]
            
            if prev_stim in transition_probs and curr_stim in transition_probs[prev_stim]:
                prob = transition_probs[prev_stim][curr_stim]
                # Shannon entropy: -log2(p)
                surprisal = -np.log2(prob) if prob > 0 else 0.0
            else:
                # Unseen transition, use a small probability
                surprisal = -np.log2(1e-6)
            
            surprisal_values.append(surprisal)
    
    # Add surprisal column to the dataframe
    df = df.copy()
    df['surprisal'] = surprisal_values
    
    return df

def run_preprocessing_pipeline(
    dataset_ids: List[str],
    output_path: Path,
    max_trials: int = 5000
) -> None:
    """
    Run the full preprocessing pipeline.
    
    Args:
        dataset_ids: List of dataset IDs to process
        output_path: Path to save the standardized output
        max_trials: Maximum number of trials per dataset
    """
    data_dir = get_data_dir()
    raw_dir = data_dir / 'raw'
    processed_dir = data_dir / 'processed'
    
    # Ensure processed directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Filter datasets
    valid_ids, exclusion_log = filter_datasets(dataset_ids, raw_dir)
    
    # Save exclusion log
    save_exclusion_log(exclusion_log, processed_dir)
    
    if not valid_ids:
        raise ValueError("No datasets were successfully processed.")
    
    # Process each dataset
    all_data = []
    
    for dataset_id in valid_ids:
        try:
            logger.info(f"Processing dataset: {dataset_id}")
            
            # Load dataset
            df = load_dataset(dataset_id, raw_dir)
            
            # Enforce sampling limit
            df = enforce_sampling_limit(df, max_trials)
            
            # Compute Markov surprisal
            # Try common column names for stimulus sequence
            stimulus_col = None
            for col in ['stimulus_sequence', 'raw_stimulus_sequence', 'stimulus', 'sequence']:
                if col in df.columns:
                    stimulus_col = col
                    break
            
            if stimulus_col is None:
                raise ValueError("No stimulus sequence column found")
            
            df = compute_markov_surprisal(df, stimulus_col)
            
            # Add dataset ID column
            df['dataset_id'] = dataset_id
            
            all_data.append(df)
            logger.info(f"Successfully processed {dataset_id}: {len(df)} rows")
            
        except Exception as e:
            logger.error(f"Failed to process {dataset_id}: {str(e)}")
            # Continue with other datasets
            continue
    
    if not all_data:
        raise ValueError("No datasets were successfully processed.")
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Ensure required columns exist
    required_columns = ['duration_estimate', 'stimulus_sequence', 'participant_id', 'surprisal']
    for col in required_columns:
        if col not in combined_df.columns:
            # Try to find similar columns
            similar_cols = [c for c in combined_df.columns if col.lower() in c.lower()]
            if similar_cols:
                logger.warning(f"Column '{col}' not found, using '{similar_cols[0]}'")
                combined_df = combined_df.rename(columns={similar_cols[0]: col})
            else:
                raise ValueError(f"Required column '{col}' not found in processed data")
    
    # Save standardized output
    combined_df.to_csv(output_path, index=False)
    logger.info(f"Standardized output saved to {output_path}")

def main():
    """Main entry point for preprocessing pipeline."""
    set_seed(42)
    
    # Get dataset IDs from data/README.md or use default
    # For now, we'll use a default list that should be updated based on Gate 0 results
    dataset_ids = ['dataset_1', 'dataset_2']  # This should be replaced with actual IDs from Gate 0
    
    output_path = get_data_dir() / 'processed' / 'standardized.csv'
    
    try:
        run_preprocessing_pipeline(dataset_ids, output_path)
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()