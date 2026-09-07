"""
Preprocessing pipeline for time perception datasets.
Implements streaming for large datasets (T041) and Markov transition matrix construction.
"""
import os
import sys
import json
import logging
import time
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Iterator, Tuple
from collections import defaultdict

# Import config utilities
try:
    from config import get_data_dir, get_processed_dir, get_config
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_data_dir, get_processed_dir, get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_TRIALS = 5000
LAPLACE_ALPHA = 1.0
SEQUENCE_COLUMN = 'stimulus_sequence'
PARTICIPANT_COLUMN = 'participant_id'
DURATION_COLUMN = 'duration_estimate'
MODALITY_COLUMN = 'stimulus_modality'
LENGTH_COLUMN = 'sequence_length'

def get_data_dir() -> Path:
    """Get the data directory path."""
    data_dir = os.getenv('DATA_DIR', 'data')
    return Path(data_dir)

def get_processed_dir() -> Path:
    """Get the processed data directory path."""
    processed_dir = os.getenv('PROCESSED_DIR', 'data/processed')
    return Path(processed_dir)

def load_dataset_streaming(dataset_id: str, source: str = 'huggingface') -> Iterator[pd.DataFrame]:
    """
    Load dataset in streaming mode to avoid loading full dataset into RAM.
    
    Args:
        dataset_id: The ID of the dataset to load
        source: 'huggingface' or 'openml'
        
    Yields:
        DataFrame chunks of the dataset
    """
    if source == 'huggingface':
        try:
            from datasets import load_dataset
            # Use streaming mode for HuggingFace datasets
            dataset = load_dataset(dataset_id, streaming=True)
            
            # Iterate through the dataset in chunks
            for split in dataset:
                for batch in dataset[split]:
                    # Convert batch dict to DataFrame
                    df = pd.DataFrame([batch])
                    yield df
                    
        except ImportError:
            logger.error("datasets library not installed. Install with: pip install datasets")
            raise
        except Exception as e:
            logger.error(f"Error loading HuggingFace dataset {dataset_id}: {e}")
            raise
            
    elif source == 'openml':
        try:
            import openml
            # Load dataset metadata
            dataset = openml.datasets.get_dataset(dataset_id)
            # Get data in chunks
            X, y, categorical_indicator, attribute_names = dataset.get_data(
                dataset_format='dataframe',
                target=dataset.default_target_attribute
            )
            # For OpenML, we load in chunks if possible
            # Since openml doesn't support native streaming, we use pandas chunked reading
            # if the data is saved as CSV, otherwise we load the full dataset
            # and iterate in chunks
            chunk_size = 1000
            for i in range(0, len(X), chunk_size):
                chunk = X.iloc[i:i+chunk_size]
                if y is not None:
                    chunk = chunk.copy()
                    chunk[dataset.default_target_attribute] = y.iloc[i:i+chunk_size]
                yield chunk
                
        except ImportError:
            logger.error("openml library not installed. Install with: pip install openml")
            raise
        except Exception as e:
            logger.error(f"Error loading OpenML dataset {dataset_id}: {e}")
            raise
    else:
        raise ValueError(f"Unknown source: {source}")

def is_sequential_stimuli(df: pd.DataFrame) -> bool:
    """Check if dataset contains sequential stimuli."""
    return SEQUENCE_COLUMN in df.columns and df[SEQUENCE_COLUMN].notna().any()

def has_predictability_manipulation(df: pd.DataFrame) -> bool:
    """Check if dataset has predictability manipulation."""
    # Check for relevant columns or conditions
    relevant_cols = ['condition', 'predictability', 'surprisal', 'probability']
    return any(col in df.columns for col in relevant_cols)

def filter_datasets(df: pd.DataFrame) -> pd.DataFrame:
    """Filter dataset to required columns and valid rows."""
    required_cols = [
        DURATION_COLUMN, SEQUENCE_COLUMN, PARTICIPANT_COLUMN,
        LENGTH_COLUMN, MODALITY_COLUMN
    ]
    
    # Keep only rows with required columns present
    mask = df[required_cols].notna().all(axis=1)
    filtered = df[mask].copy()
    
    # Ensure required columns exist
    for col in required_cols:
        if col not in filtered.columns:
            logger.warning(f"Column {col} not found in dataset")
            
    return filtered

def save_exclusion_log(exclusions: List[Dict[str, Any]], output_path: Path):
    """Save exclusion log to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(exclusions, f, indent=2)
    logger.info(f"Exclusion log saved to {output_path}")

def enforce_sampling_limit(df: pd.DataFrame, max_trials: int = MAX_TRIALS) -> pd.DataFrame:
    """Enforce sampling limit if dataset is too large."""
    if len(df) > max_trials:
        logger.info(f"Dataset has {len(df)} rows, sampling to {max_trials} trials")
        # Sample randomly with a fixed seed for reproducibility
        sampled = df.sample(n=max_trials, random_state=42)
        return sampled
    return df

def compute_markov_surprisal(
    df: pd.DataFrame,
    sequence_col: str = SEQUENCE_COLUMN,
    alpha: float = LAPLACE_ALPHA
) -> Tuple[pd.DataFrame, Dict[str, Any], Dict[str, Any]]:
    """
    Compute Markov transition matrix and surprisal values using streaming aggregation.
    
    Args:
        df: DataFrame with stimulus sequences
        sequence_col: Name of the sequence column
        alpha: Laplace smoothing parameter
        
    Returns:
        Tuple of (df_with_surprisal, transition_counts, alphabet_info)
    """
    # Extract sequences
    sequences = df[sequence_col].dropna().astype(str).tolist()
    
    if not sequences:
        logger.warning("No valid sequences found")
        df['surprisal'] = 0.0
        return df, {}, {'alphabet': [], 'order': 1}
    
    # Build transition counts with online aggregation
    # Use defaultdict for efficient counting
    transition_counts = defaultdict(lambda: defaultdict(int))
    alphabet = set()
    
    for seq in sequences:
        # Handle different sequence formats (list, string, etc.)
        if isinstance(seq, str):
            # Try to parse as list
            try:
                items = eval(seq) if seq.startswith('[') and seq.endswith(']') else list(seq)
            except:
                items = list(seq)
        elif isinstance(seq, (list, tuple)):
            items = list(seq)
        else:
            items = [str(seq)]
        
        # Update alphabet
        alphabet.update(str(item) for item in items)
        
        # Build transitions (first-order Markov)
        for i in range(len(items) - 1):
            current = str(items[i])
            next_item = str(items[i + 1])
            transition_counts[current][next_item] += 1
    
    # Convert to regular dict for serialization
    transition_counts_dict = {k: dict(v) for k, v in transition_counts.items()}
    
    # Compute probabilities with Laplace smoothing
    alphabet_list = sorted(list(alphabet))
    n_alphabet = len(alphabet_list)
    
    # Build transition matrix
    transition_matrix = {}
    for current_state in transition_counts_dict:
        total_transitions = sum(transition_counts_dict[current_state].values())
        transition_matrix[current_state] = {}
        for next_state in alphabet_list:
            count = transition_counts_dict[current_state].get(next_state, 0)
            # Apply Laplace smoothing
            prob = (count + alpha) / (total_transitions + alpha * n_alphabet)
            transition_matrix[current_state][next_state] = prob
    
    # Compute surprisal for each trial
    surprisals = []
    for seq in sequences:
        if isinstance(seq, str):
            try:
                items = eval(seq) if seq.startswith('[') and seq.endswith(']') else list(seq)
            except:
                items = list(seq)
        elif isinstance(seq, (list, tuple)):
            items = list(seq)
        else:
            items = [str(seq)]
        
        items = [str(item) for item in items]
        trial_surprisal = 0.0
        for i in range(len(items) - 1):
            current = items[i]
            next_item = items[i + 1]
            if current in transition_matrix and next_item in transition_matrix[current]:
                prob = transition_matrix[current][next_item]
                # Compute surprisal: -log2(prob)
                if prob > 0:
                    surprisal = -np.log2(prob)
                    trial_surprisal += surprisal
            else:
                # Unseen transition, use smoothed probability
                prob = alpha / (sum(transition_matrix.get(current, {}).values()) + alpha * n_alphabet)
                if prob > 0:
                    trial_surprisal -= np.log2(prob)
        
        surprisals.append(trial_surprisal)
    
    # Map surprisals back to original dataframe
    # Create a mapping from sequence to surprisal
    seq_to_surprisal = {}
    for seq, surprisal in zip(sequences, surprisals):
        seq_str = str(seq)
        seq_to_surprisal[seq_str] = surprisal
    
    # Add surprisal column to dataframe
    df = df.copy()
    df['surprisal'] = df[sequence_col].apply(lambda x: seq_to_surprisal.get(str(x), 0.0))
    
    alphabet_info = {
        'alphabet': alphabet_list,
        'order': 1,
        'n_states': len(alphabet_list)
    }
    
    return df, transition_counts_dict, alphabet_info

def write_sampling_strategy(strategy: str, output_path: Path):
    """Write sampling strategy to file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({'sampling_strategy': strategy}, f, indent=2)
    logger.info(f"Sampling strategy written to {output_path}")

def run_preprocessing_pipeline():
    """Run the full preprocessing pipeline with streaming support."""
    logger.info("Starting preprocessing pipeline with streaming support")
    
    data_dir = get_data_dir()
    processed_dir = get_processed_dir()
    
    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Read dataset IDs
    ids_file = data_dir / 'dataset_ids.txt'
    if not ids_file.exists():
        logger.error(f"Dataset IDs file not found: {ids_file}")
        return False
    
    with open(ids_file, 'r') as f:
        dataset_ids = [line.strip() for line in f if line.strip()]
    
    if not dataset_ids:
        logger.error("No dataset IDs found")
        return False
    
    logger.info(f"Processing {len(dataset_ids)} datasets")
    
    all_data = []
    exclusions = []
    
    for dataset_id in dataset_ids:
        logger.info(f"Processing dataset: {dataset_id}")
        
        try:
            # Determine source (could be extended to detect from ID format)
            source = 'huggingface' if 'hf' in dataset_id.lower() or 'huggingface' in dataset_id.lower() else 'openml'
            
            # Load dataset in streaming mode
            chunk_iterator = load_dataset_streaming(dataset_id, source)
            
            # Process chunks and aggregate
            chunk_data = []
            for chunk in chunk_iterator:
                if is_sequential_stimuli(chunk) and has_predictability_manipulation(chunk):
                    filtered = filter_datasets(chunk)
                    if len(filtered) > 0:
                        chunk_data.append(filtered)
                
                # Apply sampling limit during processing if needed
                if len(pd.concat(chunk_data, ignore_index=True)) > MAX_TRIALS:
                    logger.info("Sampling limit reached during streaming")
                    break
            
            if chunk_data:
                full_chunk = pd.concat(chunk_data, ignore_index=True)
                if len(full_chunk) > MAX_TRIALS:
                    full_chunk = enforce_sampling_limit(full_chunk, MAX_TRIALS)
                    write_sampling_strategy(f"Random sample of N={MAX_TRIALS} from streaming dataset {dataset_id}", processed_dir / 'sampling_strategy.json')
                all_data.append(full_chunk)
            else:
                exclusions.append({
                    'dataset_id': dataset_id,
                    'reason': 'No valid sequential stimuli or predictability manipulation found',
                    'status': 'excluded'
                })
                
        except Exception as e:
            logger.error(f"Error processing dataset {dataset_id}: {e}")
            exclusions.append({
                'dataset_id': dataset_id,
                'reason': str(e),
                'status': 'error'
            })
    
    if not all_data:
        logger.error("No valid data found after filtering")
        # Write exclusion log
        save_exclusion_log(exclusions, processed_dir / 'exclusion_log.json')
        return False
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    logger.info(f"Combined dataset size: {len(combined_df)} rows")
    
    # Compute Markov surprisal with streaming-friendly aggregation
    logger.info("Computing Markov transition matrix and surprisal values")
    start_time = time.time()
    
    df_with_surprisal, transition_counts, alphabet_info = compute_markov_surprisal(combined_df)
    
    elapsed = time.time() - start_time
    logger.info(f"Markov computation completed in {elapsed:.2f} seconds")
    
    # Save incremental counts
    counts_path = processed_dir / 'markov_counts.json'
    with open(counts_path, 'w') as f:
        json.dump(transition_counts, f, indent=2)
    logger.info(f"Transition counts saved to {counts_path}")
    
    # Save final Markov state
    markov_state = {
        'transition_matrix': transition_counts,
        'alphabet': alphabet_info['alphabet'],
        'order': alphabet_info['order'],
        'n_states': alphabet_info['n_states']
    }
    state_path = processed_dir / 'markov_state.json'
    with open(state_path, 'w') as f:
        json.dump(markov_state, f, indent=2)
    logger.info(f"Markov state saved to {state_path}")
    
    # Write standardized CSV
    standardized_path = processed_dir / 'standardized.csv'
    df_with_surprisal.to_csv(standardized_path, index=False)
    logger.info(f"Standardized CSV saved to {standardized_path}")
    
    # Write sampling strategy
    write_sampling_strategy(f"Streaming full dataset with online aggregation (N={len(df_with_surprisal)} trials)", processed_dir / 'sampling_strategy.json')
    
    # Write exclusion log
    save_exclusion_log(exclusions, processed_dir / 'exclusion_log.json')
    
    logger.info("Preprocessing pipeline completed successfully")
    return True

def main():
    """Main entry point for preprocessing script."""
    try:
        success = run_preprocessing_pipeline()
        if success:
            logger.info("Preprocessing completed successfully")
            sys.exit(0)
        else:
            logger.error("Preprocessing failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()