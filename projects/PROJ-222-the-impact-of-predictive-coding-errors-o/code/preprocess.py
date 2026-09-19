"""
Preprocessing pipeline for time perception datasets.
Implements streaming for large datasets and online Markov matrix construction.
"""
import os
import sys
import json
import logging
import time
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Iterator
from collections import defaultdict
from datasets import load_dataset

# Import from local modules
from config import get_data_dir, get_processed_dir, get_config
from utils import load_dataset_chunked

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_TRIALS = 5000
LAPLACE_ALPHA = 1.0

def get_data_dir() -> Path:
    """Get the data directory path."""
    return Path("data")

def get_processed_dir() -> Path:
    """Get the processed data directory path."""
    return get_data_dir() / "processed"

def load_dataset_streaming(dataset_source: str, dataset_type: str = "huggingface") -> Iterator[Dict[str, Any]]:
    """
    Load dataset in streaming mode to avoid memory issues.
    
    Args:
        dataset_source: Dataset ID or path
        dataset_type: 'huggingface' or 'openml'
        
    Yields:
        Rows from the dataset as dictionaries
    """
    if dataset_type == "huggingface":
        try:
            ds = load_dataset(dataset_source, streaming=True)
            # Handle different split structures
            if isinstance(ds, dict):
                # If it's a dict of splits, iterate over the first available split
                for split_name, split_ds in ds.items():
                    for row in split_ds:
                        yield row
            else:
                # If it's a single dataset
                for row in ds:
                    yield row
        except Exception as e:
            logger.error(f"Failed to load HuggingFace dataset {dataset_source}: {e}")
            raise
    elif dataset_type == "openml":
        # For OpenML, we use chunked loading via utils
        try:
            # OpenML datasets are typically downloaded as CSV files
            # We'll use the chunked loader from utils
            raw_path = get_data_dir() / "raw" / f"{dataset_source}.csv"
            if not raw_path.exists():
                raise FileNotFoundError(f"OpenML dataset not found: {raw_path}")
            
            for chunk in load_dataset_chunked(str(raw_path)):
                for _, row in chunk.iterrows():
                    yield row.to_dict()
        except Exception as e:
            logger.error(f"Failed to load OpenML dataset {dataset_source}: {e}")
            raise
    else:
        raise ValueError(f"Unknown dataset type: {dataset_type}")

def is_sequential_stimuli(df: pd.DataFrame) -> bool:
    """Check if dataset contains sequential stimuli."""
    required_cols = ['stimulus_sequence', 'sequence_length']
    return all(col in df.columns for col in required_cols)

def has_predictability_manipulation(df: pd.DataFrame) -> bool:
    """Check if dataset has predictability manipulation."""
    return 'duration_estimate' in df.columns or 'surprisal' in df.columns

def filter_datasets(df: pd.DataFrame) -> pd.DataFrame:
    """Filter dataset for required columns and valid rows."""
    required_cols = [
        'duration_estimate', 'stimulus_sequence', 'participant_id',
        'sequence_length', 'stimulus_modality'
    ]
    
    # Check for required columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing required columns: {missing_cols}")
        return pd.DataFrame()
    
    # Filter out rows with missing values in required columns
    df = df.dropna(subset=required_cols)
    
    # Ensure sequence_length is numeric
    if 'sequence_length' in df.columns:
        df['sequence_length'] = pd.to_numeric(df['sequence_length'], errors='coerce')
        df = df.dropna(subset=['sequence_length'])
    
    return df

def save_exclusion_log(exclusion_log: List[Dict[str, Any]], output_path: Path) -> None:
    """Save exclusion log to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)

def enforce_sampling_limit(df: pd.DataFrame, max_trials: int = MAX_TRIALS) -> pd.DataFrame:
    """Enforce sampling limit if dataset is too large."""
    if len(df) > max_trials:
        logger.info(f"Dataset has {len(df)} rows, sampling to {max_trials}")
        df = df.sample(n=max_trials, random_state=42)
        logger.info(f"Sampling strategy: Random sample of N={max_trials}")
    return df

def compute_markov_surprisal(
    rows: Iterator[Dict[str, Any]],
    max_trials: int = MAX_TRIALS
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Compute Markov transition matrix and surprisal in a streaming fashion.
    
    Args:
        rows: Iterator of dataset rows
        max_trials: Maximum number of trials to process
        
    Returns:
      - transition_matrix: Dict mapping (state, next_state) to counts
      - processed_rows: List of processed rows with surprisal
      - alphabet: List of unique symbols
    """
    # Initialize count matrix for online aggregation
    # Using defaultdict for sparse representation
    transition_counts = defaultdict(lambda: defaultdict(int))
    symbol_counts = defaultdict(int)
    processed_rows = []
    trial_count = 0
    alphabet = set()
    
    for row in rows:
        if trial_count >= max_trials:
            logger.info(f"Reached max trials limit ({max_trials}), stopping streaming")
            break
        
        trial_count += 1
        
        # Extract sequence data
        sequence = row.get('stimulus_sequence', '')
        if not isinstance(sequence, str):
            sequence = str(sequence)
        
        if not sequence:
            continue
        
        # Convert sequence to list of symbols
        symbols = list(sequence)
        alphabet.update(symbols)
        
        # Build transition counts
        for i in range(len(symbols) - 1):
            current_symbol = symbols[i]
            next_symbol = symbols[i + 1]
            transition_counts[current_symbol][next_symbol] += 1
            symbol_counts[current_symbol] += 1
        
        # Store row for later surprisal calculation
        processed_rows.append({
            'participant_id': row.get('participant_id'),
            'stimulus_sequence': sequence,
            'duration_estimate': row.get('duration_estimate'),
            'sequence_length': row.get('sequence_length'),
            'stimulus_modality': row.get('stimulus_modality'),
            'symbols': symbols  # Keep for surprisal calculation
        })
        
        # Log progress
        if trial_count % 1000 == 0:
            logger.info(f"Processed {trial_count} trials")
    
    # Convert to regular dict for JSON serialization
    alphabet = sorted(list(alphabet))
    transition_matrix = {}
    for state, next_states in transition_counts.items():
        transition_matrix[state] = dict(next_states)
    
    return transition_matrix, processed_rows, alphabet

def apply_laplace_smoothing(
    transition_matrix: Dict[str, Dict[str, int]],
    alphabet: List[str],
    alpha: float = LAPLACE_ALPHA
) -> Dict[str, Dict[str, float]]:
    """Apply Laplace smoothing to transition matrix."""
    smoothed_matrix = {}
    total_states = len(alphabet)
    
    for state in alphabet:
        smoothed_matrix[state] = {}
        state_counts = transition_matrix.get(state, {})
        total_transitions = sum(state_counts.values())
        
        for next_state in alphabet:
            count = state_counts.get(next_state, 0)
            # Laplace smoothing: P(next|state) = (count + alpha) / (total + alpha * |alphabet|)
            prob = (count + alpha) / (total_transitions + alpha * total_states)
            smoothed_matrix[state][next_state] = prob
    
    return smoothed_matrix

def compute_surprisal(
    row: Dict[str, Any],
    smoothed_matrix: Dict[str, Dict[str, float]]
) -> float:
    """Compute surprisal for a sequence using smoothed transition matrix."""
    symbols = row.get('symbols', [])
    if len(symbols) < 2:
        return 0.0  # Cannot compute transitions for sequences < 2
    
    surprisals = []
    for i in range(len(symbols) - 1):
        current_symbol = symbols[i]
        next_symbol = symbols[i + 1]
        
        if current_symbol in smoothed_matrix and next_symbol in smoothed_matrix[current_symbol]:
            prob = smoothed_matrix[current_symbol][next_symbol]
            if prob > 0:
                surprisal = -np.log2(prob)
                surprisals.append(surprisal)
            else:
                surprisals.append(0.0)  # Avoid log(0)
        else:
            surprisals.append(0.0)  # Unknown transition
    
    return np.mean(surprisals) if surprisals else 0.0

def write_sampling_strategy(output_path: Path, strategy: str) -> None:
    """Write sampling strategy to README or log."""
    with open(output_path, 'a') as f:
        f.write(f"\n## Sampling Strategy\n")
        f.write(f"{strategy}\n")

def run_preprocessing_pipeline() -> bool:
    """
    Run the full preprocessing pipeline with streaming support.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Starting preprocessing pipeline with streaming support")
        
        # Ensure output directories exist
        processed_dir = get_processed_dir()
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Load dataset IDs
        ids_file = get_data_dir() / "dataset_ids.txt"
        if not ids_file.exists():
            logger.error(f"Dataset IDs file not found: {ids_file}")
            return False
        
        with open(ids_file, 'r') as f:
            dataset_ids = [line.strip() for line in f if line.strip()]
        
        if not dataset_ids:
            logger.error("No dataset IDs found in dataset_ids.txt")
            return False
        
        logger.info(f"Found {len(dataset_ids)} dataset IDs to process")
        
        # Exclusion log
        exclusion_log = []
        all_processed_rows = []
        global_transition_matrix = defaultdict(lambda: defaultdict(int))
        global_symbol_counts = defaultdict(int)
        global_alphabet = set()
        total_trials_processed = 0
        
        # Process each dataset
        for dataset_id in dataset_ids:
            logger.info(f"Processing dataset: {dataset_id}")
            
            # Determine dataset type (heuristic based on ID format)
            dataset_type = "huggingface" if "/" in dataset_id else "openml"
            
            try:
                # Load dataset in streaming mode
                rows = load_dataset_streaming(dataset_id, dataset_type)
                
                # Process in streaming fashion
                transition_matrix, processed_rows, alphabet = compute_markov_surprisal(
                    rows, max_trials=MAX_TRIALS
                )
                
                if not processed_rows:
                    exclusion_log.append({
                        "dataset_id": dataset_id,
                        "reason": "No valid rows after streaming",
                        "status": "excluded"
                    })
                    logger.warning(f"Dataset {dataset_id} excluded: No valid rows")
                    continue
                
                # Update global counts for online aggregation
                for state, next_states in transition_matrix.items():
                    for next_state, count in next_states.items():
                        global_transition_matrix[state][next_state] += count
                        global_symbol_counts[state] += count
                        global_alphabet.add(state)
                        global_alphabet.add(next_state)
                
                all_processed_rows.extend(processed_rows)
                total_trials_processed += len(processed_rows)
                
                logger.info(f"Dataset {dataset_id}: processed {len(processed_rows)} rows")
                
            except Exception as e:
                exclusion_log.append({
                    "dataset_id": dataset_id,
                    "reason": str(e),
                    "status": "excluded"
                })
                logger.error(f"Failed to process dataset {dataset_id}: {e}")
                continue
        
        if not all_processed_rows:
            logger.error("No data processed from any dataset")
            # Write exclusion log even if empty
            exclusion_log_path = processed_dir / "exclusion_log.json"
            save_exclusion_log(exclusion_log, exclusion_log_path)
            return False
        
        logger.info(f"Total trials processed: {total_trials_processed}")
        
        # Apply Laplace smoothing to global transition matrix
        alphabet = sorted(list(global_alphabet))
        smoothed_matrix = apply_laplace_smoothing(
            dict(global_transition_matrix),
            alphabet,
            alpha=LAPLACE_ALPHA
        )
        
        # Compute surprisal for each row
        for row in all_processed_rows:
            row['surprisal'] = compute_surprisal(row, smoothed_matrix)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_processed_rows)
        
        # Drop temporary 'symbols' column
        if 'symbols' in df.columns:
            df = df.drop(columns=['symbols'])
        
        # Ensure required columns exist
        required_cols = [
            'duration_estimate', 'stimulus_sequence', 'participant_id',
            'surprisal', 'sequence_length', 'stimulus_modality'
        ]
        for col in required_cols:
            if col not in df.columns:
                logger.warning(f"Column {col} missing in final output")
        
        # Write exclusion log
        exclusion_log_path = processed_dir / "exclusion_log.json"
        save_exclusion_log(exclusion_log, exclusion_log_path)
        logger.info(f"Exclusion log written to {exclusion_log_path}")
        
        # Write intermediate counts (for T041 verification)
        counts_path = processed_dir / "markov_counts.json"
        counts_data = {
            "transition_counts": {k: dict(v) for k, v in global_transition_matrix.items()},
            "symbol_counts": dict(global_symbol_counts),
            "total_trials": total_trials_processed
        }
        with open(counts_path, 'w') as f:
            json.dump(counts_data, f, indent=2)
        logger.info(f"Markov counts written to {counts_path}")
        
        # Write final Markov state
        markov_state_path = processed_dir / "markov_state.json"
        markov_state_data = {
            "transition_matrix": smoothed_matrix,
            "alphabet": alphabet,
            "order": 1,
            "laplace_alpha": LAPLACE_ALPHA,
            "total_states": len(alphabet)
        }
        with open(markov_state_path, 'w') as f:
            json.dump(markov_state_data, f, indent=2)
        logger.info(f"Markov state written to {markov_state_path}")
        
        # Write standardized CSV
        standardized_path = processed_dir / "standardized.csv"
        df.to_csv(standardized_path, index=False)
        logger.info(f"Standardized CSV written to {standardized_path}")
        
        # Write sampling strategy
        strategy = f"Streaming full dataset(s) with max_trials={MAX_TRIALS} cap. Total trials processed: {total_trials_processed}"
        readme_path = get_data_dir() / "README.md"
        write_sampling_strategy(readme_path, strategy)
        
        logger.info("Preprocessing pipeline completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}", exc_info=True)
        return False

def main():
    """Main entry point for preprocessing pipeline."""
    success = run_preprocessing_pipeline()
    if not success:
        logger.error("Preprocessing pipeline failed")
        sys.exit(1)
    else:
        logger.info("Preprocessing pipeline completed successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()