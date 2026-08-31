import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
import hashlib
import sys

from config import get_data_dir, get_processed_dir, set_seed
from utils import load_dataset_chunked

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_dataset(dataset_id: str, source: str = 'openml') -> pd.DataFrame:
    """
    Load a dataset from OpenML or HuggingFace.
    
    Args:
        dataset_id: The ID of the dataset
        source: 'openml' or 'huggingface'
        
    Returns:
        DataFrame with the dataset
    """
    raw_dir = get_data_dir() / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = raw_dir / f"{dataset_id}.csv"
    
    if file_path.exists():
        logger.info(f"Loading cached dataset from {file_path}")
        return pd.read_csv(file_path)
    else:
        raise FileNotFoundError(f"Dataset {dataset_id} not found at {file_path}. "
                              "Please run download.py first to fetch the dataset.")

def is_sequential_stimuli(df: pd.DataFrame) -> bool:
    """
    Check if the dataset has sequential stimuli.
    
    Args:
        df: DataFrame to check
        
    Returns:
        True if sequential stimuli are present
    """
    required_cols = ['stimulus_sequence', 'raw_stimulus_sequence']
    has_seq = any(col in df.columns for col in required_cols)
    
    if not has_seq:
        logger.warning("Dataset lacks required sequential stimulus columns")
        
    return has_seq

def has_predictability_manipulation(df: pd.DataFrame) -> bool:
    """
    Check if the dataset has predictability manipulation.
    
    Args:
        df: DataFrame to check
        
    Returns:
        True if predictability manipulation is present
    """
    # Check for columns that indicate predictability manipulation
    predictability_cols = ['predictability', 'surprisal', 'probability', 'transition_prob']
    has_pred = any(col in df.columns for col in predictability_cols)
    
    if not has_pred:
        logger.warning("Dataset lacks predictability manipulation columns")
        
    return has_pred

def filter_datasets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataset for required columns.
    
    Args:
        df: DataFrame to filter
        
    Returns:
        Filtered DataFrame
    """
    required_cols = ['duration_estimate', 'stimulus_sequence', 'participant_id']
    
    # Check for alternative column names
    col_mapping = {
        'duration_estimate': ['duration_estimate', 'duration', 'time_estimate', 'response_time'],
        'stimulus_sequence': ['stimulus_sequence', 'raw_stimulus_sequence', 'stimulus'],
        'participant_id': ['participant_id', 'participant', 'subject_id', 'subject']
    }
    
    filtered_df = df.copy()
    
    for target, alternatives in col_mapping.items():
        found = False
        for alt in alternatives:
            if alt in filtered_df.columns:
                if alt != target:
                    filtered_df = filtered_df.rename(columns={alt: target})
                found = True
                break
        
        if not found:
            raise ValueError(f"Required column '{target}' not found in dataset")
    
    return filtered_df

def save_exclusion_log(dataset_id: str, reason: str, exclusion_log_path: Path) -> None:
    """
    Save exclusion log entry.
    
    Args:
        dataset_id: ID of the excluded dataset
        reason: Reason for exclusion
        exclusion_log_path: Path to the exclusion log file
    """
    log_entry = {
        'dataset_id': dataset_id,
        'reason': reason,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    if exclusion_log_path.exists():
        with open(exclusion_log_path, 'r') as f:
            exclusion_log = json.load(f)
    else:
        exclusion_log = []
    
    exclusion_log.append(log_entry)
    
    with open(exclusion_log_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    
    logger.info(f"Logged exclusion for {dataset_id}: {reason}")

def enforce_sampling_limit(df: pd.DataFrame, max_trials: Optional[int] = None) -> pd.DataFrame:
    """
    Enforce sampling limit if specified.
    
    Args:
        df: DataFrame to sample
        max_trials: Maximum number of trials to keep
        
    Returns:
        Sampled DataFrame
    """
    if max_trials is not None and len(df) > max_trials:
        logger.warning(f"Dataset has {len(df)} trials, sampling to {max_trials}")
        df = df.head(max_trials)
    
    return df

def compute_markov_surprisal(df: pd.DataFrame, order: int = 1) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """
    Compute Markov surprisal metrics using Shannon entropy of transitions.
    
    This implements a first-order Markov model where the surprisal of a state
    is calculated as -log2(P(next_state | current_state)).
    
    Args:
        df: DataFrame with 'stimulus_sequence' column
        order: Order of the Markov model (default 1)
        
    Returns:
        Tuple of (markov_state_dict, df_with_surprisal)
    """
    logger.info(f"Computing Markov surprisal (order={order})...")
    
    # Get the stimulus sequence
    if 'stimulus_sequence' not in df.columns:
        if 'raw_stimulus_sequence' in df.columns:
            sequence = df['raw_stimulus_sequence'].astype(str)
        else:
            raise ValueError("No stimulus sequence column found")
    else:
        sequence = df['stimulus_sequence'].astype(str)
    
    # Build alphabet from unique values
    alphabet = sorted(sequence.unique().tolist())
    logger.info(f"Alphabet size: {len(alphabet)}, unique values: {alphabet[:10]}...")
    
    # Build transition counts
    transition_counts = Counter()
    
    if order == 1:
        # First-order Markov: P(current | previous)
        for i in range(len(sequence) - 1):
            prev_state = sequence.iloc[i]
            curr_state = sequence.iloc[i + 1]
            transition_counts[(prev_state, curr_state)] += 1
    else:
        # Higher-order Markov: P(current | previous_order_states)
        for i in range(order, len(sequence)):
            prev_states = tuple(sequence.iloc[i-order:i].tolist())
            curr_state = sequence.iloc[i]
            transition_counts[(prev_states, curr_state)] += 1
    
    # Build transition matrix
    transition_matrix = {}
    transition_probs = {}
    
    if order == 1:
        # Group by previous state
        prev_states = set([k[0] for k in transition_counts.keys()])
        for prev in prev_states:
            total = sum(transition_counts[(prev, curr)] for curr in alphabet if (prev, curr) in transition_counts)
            transition_matrix[prev] = {}
            transition_probs[prev] = {}
            for curr in alphabet:
                count = transition_counts.get((prev, curr), 0)
                prob = count / total if total > 0 else 0.0
                transition_matrix[prev][curr] = count
                transition_probs[prev][curr] = prob
    else:
        # Group by previous states tuple
        prev_states = set([k[0] for k in transition_counts.keys()])
        for prev_tuple in prev_states:
            total = sum(transition_counts[(prev_tuple, curr)] for curr in alphabet if (prev_tuple, curr) in transition_counts)
            transition_matrix[str(prev_tuple)] = {}
            transition_probs[str(prev_tuple)] = {}
            for curr in alphabet:
                count = transition_counts.get((prev_tuple, curr), 0)
                prob = count / total if total > 0 else 0.0
                transition_matrix[str(prev_tuple)][curr] = count
                transition_probs[str(prev_tuple)][curr] = prob
    
    # Compute surprisal for each transition
    # Surprisal = -log2(P(current | previous))
    surprisal_values = []
    
    if order == 1:
        for i in range(len(sequence)):
            if i == 0:
                # First element: use uniform prior or marginal
                prob = 1.0 / len(alphabet)
            else:
                prev_state = sequence.iloc[i - 1]
                curr_state = sequence.iloc[i]
                prob = transition_probs.get(prev_state, {}).get(curr_state, 0.0)
                if prob == 0:
                    prob = 1e-10  # Smoothing to avoid log(0)
            
            surprisal = -np.log2(prob)
            surprisal_values.append(surprisal)
    else:
        for i in range(len(sequence)):
            if i < order:
                # Not enough history: use uniform prior
                prob = 1.0 / len(alphabet)
            else:
                prev_tuple = tuple(sequence.iloc[i-order:i].tolist())
                curr_state = sequence.iloc[i]
                prob = transition_probs.get(str(prev_tuple), {}).get(curr_state, 0.0)
                if prob == 0:
                    prob = 1e-10
            
            surprisal = -np.log2(prob)
            surprisal_values.append(surprisal)
    
    # Add surprisal to dataframe
    df_with_surprisal = df.copy()
    df_with_surprisal['surprisal'] = surprisal_values
    
    # Build markov_state dictionary
    markov_state = {
        'transition_matrix': transition_matrix,
        'alphabet': alphabet,
        'order': order,
        'transition_probs': transition_probs,
        'entropy': -sum(p * np.log2(p) for p in [sum(transition_probs.get(prev, {}).values()) > 0 
                                                  for prev in transition_probs] 
                        if sum(transition_probs.get(prev, {}).values()) > 0) if transition_probs else 0.0
    }
    
    # Calculate actual Shannon entropy of the transition distribution
    total_transitions = sum(transition_counts.values())
    if total_transitions > 0:
        entropy = 0.0
        for count in transition_counts.values():
            prob = count / total_transitions
            if prob > 0:
                entropy -= prob * np.log2(prob)
        markov_state['entropy'] = entropy
    
    logger.info(f"Markov surprisal computation complete. Entropy: {markov_state['entropy']:.4f}")
    
    return markov_state, df_with_surprisal

def run_preprocessing_pipeline(dataset_ids: List[str], output_path: Path) -> pd.DataFrame:
    """
    Run the full preprocessing pipeline.
    
    Args:
        dataset_ids: List of dataset IDs to process
        output_path: Path to save the standardized output
        
    Returns:
        Combined standardized DataFrame
    """
    logger.info(f"Starting preprocessing pipeline for {len(dataset_ids)} datasets")
    
    all_dataframes = []
    exclusion_log_path = get_processed_dir() / 'exclusion_log.json'
    
    for dataset_id in dataset_ids:
        try:
            logger.info(f"Processing dataset: {dataset_id}")
            
            # Load dataset
            df = load_dataset(dataset_id)
            
            # Check for sequential stimuli
            if not is_sequential_stimuli(df):
                save_exclusion_log(dataset_id, "Missing sequential stimulus columns", exclusion_log_path)
                continue
            
            # Check for predictability manipulation
            if not has_predictability_manipulation(df):
                save_exclusion_log(dataset_id, "Missing predictability manipulation", exclusion_log_path)
                continue
            
            # Filter for required columns
            df = filter_datasets(df)
            
            # Enforce sampling limit if needed
            df = enforce_sampling_limit(df)
            
            # Compute Markov surprisal
            markov_state, df_with_surprisal = compute_markov_surprisal(df)
            
            # Save markov state for this dataset
            markov_output_path = get_processed_dir() / f'markov_state_{dataset_id}.json'
            with open(markov_output_path, 'w') as f:
                json.dump(markov_state, f, indent=2)
            logger.info(f"Saved Markov state to {markov_output_path}")
            
            all_dataframes.append(df_with_surprisal)
            
        except Exception as e:
            logger.error(f"Failed to process {dataset_id}: {str(e)}")
            save_exclusion_log(dataset_id, str(e), exclusion_log_path)
    
    if not all_dataframes:
        raise ValueError("No datasets were successfully processed.")
    
    # Combine all dataframes
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    
    # Add dataset_id column if not present
    if 'dataset_id' not in combined_df.columns:
        combined_df['dataset_id'] = [dataset_ids[0]] * len(combined_df)
    
    # Save standardized output
    combined_df.to_csv(output_path, index=False)
    logger.info(f"Saved standardized output to {output_path} with {len(combined_df)} rows")
    
    return combined_df

def main():
    """Main entry point for preprocessing pipeline."""
    set_seed(42)
    
    # Get dataset IDs from data/README.md or use default
    # For now, use a placeholder - in real implementation, parse from README
    dataset_ids = ['time_perception_dataset_1']  # This would be parsed from data/README.md
    
    output_path = get_processed_dir() / 'standardized.csv'
    
    try:
        run_preprocessing_pipeline(dataset_ids, output_path)
        logger.info("Preprocessing pipeline completed successfully")
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()