import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from collections import defaultdict

from config import get_data_dir, set_seed
from utils import load_dataset_chunked

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_dataset(dataset_id: str, source: str = 'openml') -> pd.DataFrame:
    """
    Load a dataset from the specified source.
    Note: This is a placeholder for the actual implementation which would
    interface with the download.py module to fetch real data.
    For T016, we assume the data is already available in data/raw/ or data/processed/
    as per the pipeline flow from T012/T013/T014.
    """
    # In a real scenario, this would call fetch_openml_dataset or fetch_huggingface_dataset
    # For now, we assume the data has been downloaded and filtered by previous tasks.
    # We expect the data to be in data/raw/ or data/processed/
    data_dir = get_data_dir()
    raw_dir = data_dir / 'raw'
    
    # Look for the dataset file
    possible_paths = [
        raw_dir / f"{dataset_id}.csv",
        raw_dir / f"{dataset_id}.parquet",
        raw_dir / f"{dataset_id}.json"
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Loading dataset from {path}")
            if path.suffix == '.csv':
                return pd.read_csv(path)
            elif path.suffix == '.parquet':
                return pd.read_parquet(path)
            elif path.suffix == '.json':
                return pd.read_json(path)
    
    raise FileNotFoundError(f"Dataset {dataset_id} not found in {raw_dir}")

def is_sequential_stimuli(df: pd.DataFrame) -> bool:
    """
    Check if the dataset contains sequential stimuli.
    This is a heuristic check based on the presence of a 'stimulus_sequence' column
    or similar temporal ordering.
    """
    # Check for common column names indicating sequential data
    sequential_cols = ['stimulus_sequence', 'trial_sequence', 'stimulus_order', 'sequence_id']
    return any(col in df.columns for col in sequential_cols) or len(df) > 1

def has_predictability_manipulation(df: pd.DataFrame) -> bool:
    """
    Check if the dataset contains a predictability manipulation.
    This is a heuristic check based on the presence of a 'condition' or 'predictability' column.
    """
    predictability_cols = ['condition', 'predictability', 'stimulus_type', 'manipulation']
    return any(col in df.columns for col in predictability_cols)

def filter_datasets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataset to ensure it meets the requirements for sequential stimuli
    and predictability manipulation.
    """
    if not is_sequential_stimuli(df):
        raise ValueError("Dataset does not contain sequential stimuli.")
    if not has_predictability_manipulation(df):
        raise ValueError("Dataset does not contain a predictability manipulation.")
    return df

def enforce_sampling_limit(df: pd.DataFrame, max_trials: int = 5000) -> pd.DataFrame:
    """
    Enforce a sampling limit on the dataset to ensure it fits within memory constraints.
    """
    if len(df) > max_trials:
        logger.info(f"Dataset has {len(df)} trials, sampling to {max_trials} trials.")
        # Sample randomly but deterministically
        np.random.seed(42)  # Fixed seed for reproducibility
        return df.sample(n=max_trials, random_state=42)
    return df

def compute_markov_surprisal(df: pd.DataFrame, stimulus_col: str = 'stimulus_sequence', 
                             condition_col: str = 'condition', 
                             participant_col: str = 'participant_id') -> pd.DataFrame:
    """
    Compute Markov surprisal for the dataset using Shannon entropy of the transition.
    
    This function:
    1. Groups data by participant and condition (if applicable).
    2. Computes first-order transition probabilities for the stimulus sequence.
    3. Calculates the surprisal (negative log probability) for each transition.
    4. Adds the surprisal metric to the dataframe.
    
    Args:
        df: Input DataFrame with stimulus sequence and other relevant columns.
        stimulus_col: Name of the column containing the stimulus sequence.
        condition_col: Name of the column containing condition labels (optional).
        participant_col: Name of the column containing participant IDs.
        
    Returns:
        DataFrame with an additional 'surprisal' column.
    """
    logger.info("Computing Markov surprisal...")
    
    # Ensure the stimulus column is categorical for efficient transition counting
    df = df.copy()
    df[stimulus_col] = df[stimulus_col].astype(str)
    
    # Group by participant and condition if available
    if condition_col in df.columns:
        groups = df.groupby([participant_col, condition_col])
    else:
        groups = df.groupby(participant_col)
    
    surprisal_list = []
    
    for group_name, group_df in groups:
        # Extract the stimulus sequence for this group
        sequence = group_df[stimulus_col].values
        
        # Compute transition counts
        transition_counts = defaultdict(lambda: defaultdict(int))
        for i in range(len(sequence) - 1):
            current = sequence[i]
            next_stim = sequence[i + 1]
            transition_counts[current][next_stim] += 1
        
        # Compute transition probabilities
        transition_probs = {}
        for current, next_stims in transition_counts.items():
            total = sum(next_stims.values())
            transition_probs[current] = {next_stim: count / total 
                                         for next_stim, count in next_stims.items()}
        
        # Compute surprisal for each transition
        group_surprisal = []
        for i in range(len(sequence) - 1):
            current = sequence[i]
            next_stim = sequence[i + 1]
            
            if current in transition_probs and next_stim in transition_probs[current]:
                prob = transition_probs[current][next_stim]
                surprisal = -np.log2(prob) if prob > 0 else 0
            else:
                # If transition is unseen, assign a high surprisal (or handle as needed)
                surprisal = -np.log2(1e-10)  # Small probability fallback
            
            group_surprisal.append(surprisal)
        
        # Add a NaN for the last trial (no next state)
        group_surprisal.append(np.nan)
        
        # Assign surprisal values back to the group
        group_df = group_df.copy()
        group_df['surprisal'] = group_surprisal
        surprisal_list.append(group_df)
    
    # Concatenate all groups back together
    result_df = pd.concat(surprisal_list, ignore_index=True)
    
    logger.info(f"Markov surprisal computed. Shape: {result_df.shape}")
    return result_df

def run_preprocessing_pipeline(dataset_ids: List[str], output_path: Path) -> None:
    """
    Run the full preprocessing pipeline:
    1. Load datasets.
    2. Filter for sequential stimuli and predictability.
    3. Enforce sampling limit.
    4. Compute Markov surprisal.
    5. Save the standardized output.
    
    Args:
        dataset_ids: List of dataset IDs to process.
        output_path: Path to save the standardized output CSV.
    """
    all_dataframes = []
    
    for dataset_id in dataset_ids:
        logger.info(f"Processing dataset: {dataset_id}")
        try:
            # Load dataset
            df = load_dataset(dataset_id)
            
            # Filter datasets
            df = filter_datasets(df)
            
            # Enforce sampling limit
            df = enforce_sampling_limit(df)
            
            # Compute Markov surprisal
            df = compute_markov_surprisal(df)
            
            all_dataframes.append(df)
            logger.info(f"Successfully processed {dataset_id}.")
        except Exception as e:
            logger.error(f"Failed to process {dataset_id}: {e}")
            continue
    
    if not all_dataframes:
        raise ValueError("No datasets were successfully processed.")
    
    # Concatenate all processed dataframes
    standardized_df = pd.concat(all_dataframes, ignore_index=True)
    
    # Ensure required columns are present
    required_cols = ['duration_estimate', 'stimulus_sequence', 'participant_id', 'surprisal']
    missing_cols = [col for col in required_cols if col not in standardized_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Save to output path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    standardized_df.to_csv(output_path, index=False)
    logger.info(f"Standardized output saved to {output_path}")

def main():
    """
    Main entry point for the preprocessing pipeline.
    """
    set_seed(42)
    
    # Get dataset IDs from data/README.md or a configuration file
    # For now, we assume a list of dataset IDs is provided or hardcoded
    # In a real scenario, this would be read from data/README.md
    dataset_ids = ['dataset_1', 'dataset_2']  # Placeholder, replace with real IDs
    
    output_path = get_data_dir() / 'processed' / 'standardized.csv'
    
    run_preprocessing_pipeline(dataset_ids, output_path)

if __name__ == '__main__':
    main()