import os
import sys
import json
import logging
import time
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter

from config import get_processed_dir, get_data_dir, set_seed
from utils import load_dataset_chunked

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_dataset(dataset_id: str, source: str) -> Optional[pd.DataFrame]:
    """
    Load a dataset from the specified source (OpenML or HuggingFace).
    This is a placeholder for the actual loading logic which would be
    implemented in download.py or a dedicated loader module.
    For T016, we assume the data is already in 'data/processed/' as
    intermediate files or that the download step has populated the raw data.
    
    Since T012 failed, we need to handle the case where data might not be
    available. However, T016 depends on T015 which implies data should be
    preprocessed or at least available.
    
    In a real scenario, this would fetch from the source. Here, we attempt
    to load from a local path if available, or raise an error if not.
    """
    # This function is a stub to satisfy the dependency chain.
    # In the actual pipeline, T012 would have downloaded the data.
    # We assume for T016 that we are processing data that T015 has prepared
    # or that we are re-loading from the raw/processed directory.
    
    # Let's assume the data is in 'data/processed/' with a specific naming convention
    # or that we are loading from a cached location.
    # Since T012 failed, we might not have data.
    # However, the task requires implementing the Markov surprisal calculation.
    # We will implement the logic assuming data is available.
    
    # For now, we'll raise a NotImplementedError to indicate that the data
    # loading step (T012) is broken and needs to be fixed first.
    # But the task asks to implement the calculation.
    
    # Let's assume the data is in a file named after the dataset_id
    # e.g., data/processed/{dataset_id}.csv
    # This is a simplification.
    
    # Actually, looking at the error, T012 failed to download.
    # So we cannot load data.
    # But the task is to implement the calculation logic.
    # We will implement the function and assume it will be called with valid data
    # once T012 is fixed.
    
    # For the purpose of this task, we will simulate a dataset if not found,
    # but ONLY if we are in a test environment or if explicitly allowed.
    # However, the constraint says "Real data only".
    # So we will raise an error if data is not found.
    
    # Let's try to load from a standard location
    raw_data_dir = get_data_dir() / "raw"
    processed_data_dir = get_processed_dir()
    
    # Try to find a CSV file matching the dataset_id
    possible_paths = [
        raw_data_dir / f"{dataset_id}.csv",
        processed_data_dir / f"{dataset_id}.csv",
        raw_data_dir / f"{dataset_id}",
        processed_data_dir / f"{dataset_id}"
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Loading dataset from {path}")
            if path.suffix == '.csv':
                return pd.read_csv(path)
            else:
                # Assume it's a directory with CSV files or other formats
                # For simplicity, we'll assume it contains a single CSV
                csv_files = list(path.glob("*.csv"))
                if csv_files:
                    return pd.read_csv(csv_files[0])
    
    logger.error(f"Dataset {dataset_id} not found in {raw_data_dir} or {processed_data_dir}")
    return None

def is_sequential_stimuli(df: pd.DataFrame) -> bool:
    """
    Check if the dataset contains sequential stimuli.
    This is a placeholder implementation.
    """
    # Check for a column that indicates sequence or order
    seq_cols = ['sequence', 'trial_order', 'stimulus_order', 'order']
    for col in seq_cols:
        if col in df.columns:
            return True
    return False

def has_predictability_manipulation(df: pd.DataFrame) -> bool:
    """
    Check if the dataset has a predictability manipulation.
    This is a placeholder implementation.
    """
    # Check for a column that indicates predictability or condition
    pred_cols = ['condition', 'predictability', 'manipulation', 'type']
    for col in pred_cols:
        if col in df.columns:
            return True
    return False

def filter_datasets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the dataset to include only rows with required columns.
    Required columns: duration_estimate, stimulus_sequence, participant_id
    """
    required_cols = ['duration_estimate', 'stimulus_sequence', 'participant_id']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing required columns: {missing_cols}")
        # Try to map common column names
        col_mapping = {
            'duration_estimate': ['duration', 'estimate', 'time_estimate', 'reaction_time', 'rt'],
            'stimulus_sequence': ['stimulus', 'sequence', 'stim', 'item'],
            'participant_id': ['participant', 'subject', 'id', 'pid', 'participant_id']
        }
        for target, sources in col_mapping.items():
            if target not in df.columns:
                for source in sources:
                    if source in df.columns:
                        df = df.rename(columns={source: target})
                        logger.info(f"Mapped {source} to {target}")
                        break
        
        # Check again
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Still missing required columns after mapping: {missing_cols}")
    
    return df[required_cols]

def save_exclusion_log(dataset_id: str, reason: str, exclusion_log_path: Path):
    """
    Save an exclusion log entry.
    """
    exclusion_log = []
    if exclusion_log_path.exists():
        with open(exclusion_log_path, 'r') as f:
            exclusion_log = json.load(f)
    
    exclusion_log.append({
        'dataset_id': dataset_id,
        'reason': reason,
        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
    })
    
    with open(exclusion_log_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)

def enforce_sampling_limit(df: pd.DataFrame, max_trials: int = 5000) -> pd.DataFrame:
    """
    Enforce a sampling limit on the dataset.
    """
    if len(df) > max_trials:
        logger.info(f"Dataset has {len(df)} trials, sampling to {max_trials}")
        # Sample randomly
        df = df.sample(n=max_trials, random_state=42)
    return df

def compute_markov_surprisal(df: pd.DataFrame, stimulus_col: str = 'stimulus_sequence', 
                             order: int = 1) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Compute Markov surprisal on the stimulus sequence.
    
    Surprisal is defined as -log2(P(next_state | current_state)).
    We use Shannon entropy of the transition.
    
    Args:
        df: DataFrame with stimulus_sequence column
        stimulus_col: Name of the column containing the stimulus sequence
        order: Order of the Markov model (default 1)
    
    Returns:
        DataFrame with surprisal added, and Markov state dictionary
    """
    if stimulus_col not in df.columns:
        raise ValueError(f"Column {stimulus_col} not found in DataFrame")
    
    # Get unique states (alphabet)
    alphabet = sorted(df[stimulus_col].dropna().unique().astype(str))
    state_to_idx = {state: idx for idx, state in enumerate(alphabet)}
    idx_to_state = {idx: state for state, idx in state_to_idx.items()}
    
    # Convert sequence to indices
    sequence = df[stimulus_col].dropna().astype(str).map(state_to_idx).tolist()
    
    # Build transition matrix
    # For order 1: P(next | current)
    transition_counts = np.zeros((len(alphabet), len(alphabet)))
    
    for i in range(len(sequence) - 1):
        current_state = sequence[i]
        next_state = sequence[i + 1]
        if current_state < len(alphabet) and next_state < len(alphabet):
            transition_counts[current_state, next_state] += 1
    
    # Normalize to probabilities
    row_sums = transition_counts.sum(axis=1, keepdims=True)
    # Avoid division by zero
    row_sums[row_sums == 0] = 1
    transition_matrix = transition_counts / row_sums
    
    # Compute surprisal for each transition
    # Surprisal[i] = -log2(P(sequence[i+1] | sequence[i]))
    surprisal = []
    for i in range(len(sequence) - 1):
        current_state = sequence[i]
        next_state = sequence[i + 1]
        if current_state < len(alphabet) and next_state < len(alphabet):
            prob = transition_matrix[current_state, next_state]
            if prob > 0:
                s = -np.log2(prob)
            else:
                s = np.inf  # Or a large number
            surprisal.append(s)
        else:
            surprisal.append(np.nan)
    
    # Add a NaN for the first element (no previous state)
    surprisal = [np.nan] + surprisal
    
    # Align with original DataFrame (handling dropped NaNs in sequence)
    # We need to map back to the original rows
    # Since we dropped NaNs in stimulus_col, we need to be careful
    # Let's assume the original df has no NaNs in stimulus_col for simplicity
    # If there were NaNs, they were dropped in the sequence list
    
    # Create a new column for surprisal
    # We'll align by index
    df_surprisal = df.copy()
    df_surprisal['surprisal'] = np.nan
    
    # Get the indices of non-null stimulus_sequence
    valid_indices = df_surprisal[stimulus_col].dropna().index
    if len(valid_indices) > 1:
        df_surprisal.loc[valid_indices, 'surprisal'] = surprisal[:len(valid_indices)]
    
    # Build the Markov state dictionary
    markov_state = {
        'transition_matrix': {
            str(src): {str(dst): float(transition_matrix[src, dst]) 
                       for dst in range(len(alphabet))}
            for src in range(len(alphabet))
        },
        'alphabet': alphabet,
        'order': order
    }
    
    return df_surprisal, markov_state

def run_preprocessing_pipeline(dataset_ids: List[Tuple[str, str]], output_path: Path) -> None:
    """
    Run the full preprocessing pipeline.
    
    Args:
        dataset_ids: List of (dataset_id, source) tuples
        output_path: Path to save the standardized output
    """
    processed_dir = get_processed_dir()
    exclusion_log_path = processed_dir / "exclusion_log.json"
    
    all_data = []
    valid_datasets = []
    
    for dataset_id, source in dataset_ids:
        logger.info(f"Processing dataset {dataset_id} from {source}")
        
        try:
            # Load dataset
            df = load_dataset(dataset_id, source)
            if df is None:
                logger.warning(f"Dataset {dataset_id} not found, skipping")
                save_exclusion_log(dataset_id, "Dataset not found", exclusion_log_path)
                continue
            
            # Filter datasets
            df = filter_datasets(df)
            
            # Check for sequential stimuli
            if not is_sequential_stimuli(df):
                logger.warning(f"Dataset {dataset_id} does not have sequential stimuli, skipping")
                save_exclusion_log(dataset_id, "Not sequential stimuli", exclusion_log_path)
                continue
            
            # Check for predictability manipulation
            if not has_predictability_manipulation(df):
                logger.warning(f"Dataset {dataset_id} does not have predictability manipulation, skipping")
                save_exclusion_log(dataset_id, "No predictability manipulation", exclusion_log_path)
                continue
            
            # Enforce sampling limit
            df = enforce_sampling_limit(df)
            
            # Compute Markov surprisal
            df_surprisal, markov_state = compute_markov_surprisal(df)
            
            # Save Markov state
            markov_state_path = processed_dir / f"markov_state_{dataset_id}.json"
            with open(markov_state_path, 'w') as f:
                json.dump(markov_state, f, indent=2)
            logger.info(f"Saved Markov state to {markov_state_path}")
            
            # Add to all_data
            df_surprisal['dataset_id'] = dataset_id
            all_data.append(df_surprisal)
            valid_datasets.append(dataset_id)
            
        except Exception as e:
            logger.error(f"Error processing dataset {dataset_id}: {e}")
            save_exclusion_log(dataset_id, str(e), exclusion_log_path)
            continue
    
    if not all_data:
        raise ValueError("No datasets were successfully processed.")
    
    # Concatenate all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Save standardized output
    combined_df.to_csv(output_path, index=False)
    logger.info(f"Saved standardized output to {output_path}")
    
    # Save combined Markov state (if needed)
    # For now, we save individual states. If a combined state is needed, we can compute it here.
    # Let's compute a combined Markov state for the entire dataset
    if len(valid_datasets) == 1:
        # Use the single dataset's Markov state
        pass
    else:
        # Combine all data and compute a global Markov state
        global_df, global_markov_state = compute_markov_surprisal(combined_df)
        global_markov_state_path = processed_dir / "markov_state_combined.json"
        with open(global_markov_state_path, 'w') as f:
            json.dump(global_markov_state, f, indent=2)
        logger.info(f"Saved combined Markov state to {global_markov_state_path}")

def main():
    """
    Main entry point for the preprocessing pipeline.
    """
    set_seed(42)
    
    # Get dataset IDs from data/dataset_ids.txt
    dataset_ids_path = get_data_dir() / "dataset_ids.txt"
    if not dataset_ids_path.exists():
        logger.error(f"Dataset IDs file not found: {dataset_ids_path}")
        sys.exit(1)
    
    dataset_ids = []
    with open(dataset_ids_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split(':')
                if len(parts) == 2:
                    dataset_id, source = parts
                    dataset_ids.append((dataset_id.strip(), source.strip()))
                else:
                    logger.warning(f"Invalid line in dataset_ids.txt: {line}")
    
    if not dataset_ids:
        logger.error("No valid dataset IDs found in dataset_ids.txt")
        sys.exit(1)
    
    output_path = get_processed_dir() / "standardized.csv"
    
    try:
        run_preprocessing_pipeline(dataset_ids, output_path)
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()