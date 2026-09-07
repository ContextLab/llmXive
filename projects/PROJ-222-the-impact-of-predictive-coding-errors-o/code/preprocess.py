import os
import sys
import json
import logging
import time
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from config import get_data_dir, get_processed_dir, set_seed
from utils import load_dataset_chunked

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/preprocess.log')
    ]
)
logger = logging.getLogger(__name__)

def load_markov_state(markov_path: Path) -> Dict[str, Any]:
    """Load the Markov state file containing transition matrix and alphabet."""
    if not markov_path.exists():
        raise FileNotFoundError(f"Markov state file not found at {markov_path}")
    
    with open(markov_path, 'r') as f:
        state = json.load(f)
    
    # Validate structure
    assert 'transition_matrix' in state, "Missing 'transition_matrix' in markov_state.json"
    assert 'alphabet' in state, "Missing 'alphabet' in markov_state.json"
    assert state.get('order', 0) == 1, "Only order=1 Markov models are supported"
    
    return state

def compute_surprisal_probability(
    current_state: str,
    prev_state: str,
    transition_matrix: Dict[str, Dict[str, float]],
    alphabet: List[str],
    alpha: float = 1.0
) -> float:
    """
    Compute surprisal (-log2 probability) for a transition.
    
    Uses Laplace smoothing: P(next|prev) = (count(prev->next) + alpha) / (sum(count(prev->*)) + alpha * |alphabet|)
    """
    if prev_state not in transition_matrix:
        # If previous state never seen, use uniform prior over alphabet
        prob = 1.0 / len(alphabet)
    else:
        transitions_from_prev = transition_matrix[prev_state]
        
        # Get count for this specific transition (default 0 if not seen)
        count_transition = transitions_from_prev.get(current_state, 0)
        
        # Calculate total transitions from prev_state with smoothing
        total_transitions = sum(transitions_from_prev.values())
        smoothing_denominator = total_transitions + alpha * len(alphabet)
        
        # Apply Laplace smoothing
        prob = (count_transition + alpha) / smoothing_denominator
    
    if prob <= 0:
        # Avoid log(0) - should not happen with Laplace smoothing but safety check
        prob = 1e-10
    
    return -np.log2(prob)

def compute_surprisal(
    input_path: Path,
    output_path: Path,
    markov_path: Path,
    chunk_size: int = 10000
) -> Path:
    """
    Compute surprisal for each trial and write to standardized.csv.
    
    Logic:
    1. Check if 'surprisal' column already exists -> skip if present.
    2. Load Markov state (transition matrix, alphabet).
    3. Stream input CSV in chunks.
    4. For each trial, compute surprisal using history (previous stimulus).
    5. Append surprisal and write to output.
    """
    logger.info(f"Starting surprisal computation for {input_path}")
    
    # 1. Conditional Check: Skip if already present
    try:
        # Peek at first chunk to check columns
        first_chunk = pd.read_csv(input_path, nrows=chunk_size)
        if 'surprisal' in first_chunk.columns:
            logger.info("Surprisal column already present. Skipping computation.")
            # Copy input to output if not already there (idempotent)
            if not output_path.exists() or not output_path.samefile(input_path):
                input_path.rename(output_path) if output_path.exists() else None
                if not output_path.exists():
                    input_path.rename(output_path)
            return output_path
    except Exception as e:
        logger.error(f"Error checking columns: {e}")
        raise
    
    # 2. Load Markov state
    logger.info(f"Loading Markov state from {markov_path}")
    markov_state = load_markov_state(markov_path)
    transition_matrix = markov_state['transition_matrix']
    alphabet = markov_state['alphabet']
    
    # Identify the stimulus column (assumed to be 'stimulus_sequence' based on schema)
    stimulus_col = 'stimulus_sequence'
    if stimulus_col not in first_chunk.columns:
        raise ValueError(f"Required column '{stimulus_col}' not found in input data")
    
    # 3. Process in chunks and compute surprisal
    logger.info("Processing data in chunks to compute surprisal...")
    
    # We need to maintain state between chunks (the last stimulus of previous chunk)
    last_stimulus: Optional[str] = None
    
    # Prepare output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use a flag to determine if header should be written
    write_header = True
    
    # Stream input and write output
    # We'll accumulate chunks to write in batches for efficiency
    processed_chunks = []
    batch_size = 5  # Write every 5 processed chunks to disk
    
    for chunk_idx, chunk in enumerate(load_dataset_chunked(input_path, chunk_size=chunk_size)):
        surprisal_values = []
        
        for idx, row in chunk.iterrows():
            current_stimulus = str(row[stimulus_col])
            
            if last_stimulus is None:
                # First trial: no previous state, use uniform probability
                # Or skip? Spec says "current history". For first trial, history is empty.
                # We'll assume uniform prior for the first trial of a sequence.
                # However, typically surprisal is defined for transitions.
                # Let's use the alphabet size for the first trial (1/|alphabet|)
                prob = 1.0 / len(alphabet)
                surprisal = -np.log2(prob) if prob > 0 else 0.0
            else:
                # Compute surprisal for transition: last_stimulus -> current_stimulus
                surprisal = compute_surprisal_probability(
                    current_stimulus,
                    last_stimulus,
                    transition_matrix,
                    alphabet,
                    alpha=1.0
                )
            
            surprisal_values.append(surprisal)
            last_stimulus = current_stimulus  # Update state for next row
        
        # Add surprisal column to chunk
        chunk['surprisal'] = surprisal_values
        processed_chunks.append(chunk)
        
        # Write batch to disk
        if (chunk_idx + 1) % batch_size == 0:
            df_batch = pd.concat(processed_chunks, ignore_index=True)
            df_batch.to_csv(output_path, mode='a', header=write_header, index=False)
            write_header = False
            processed_chunks = []
            logger.info(f"Written batch {chunk_idx + 1} to {output_path}")
    
    # Write remaining chunks
    if processed_chunks:
        df_remaining = pd.concat(processed_chunks, ignore_index=True)
        df_remaining.to_csv(output_path, mode='a', header=write_header, index=False)
        logger.info("Written final batch to output")
    
    logger.info(f"Surprisal computation complete. Output written to {output_path}")
    
    # Validate output
    final_df = pd.read_csv(output_path, nrows=10)
    assert 'surprisal' in final_df.columns, "Surprisal column missing in output"
    
    return output_path

def run_preprocessing_pipeline(
    dataset_ids: List[str],
    output_path: Optional[Path] = None
) -> Path:
    """
    Run the full preprocessing pipeline for a list of dataset IDs.
    
    This function orchestrates:
    1. Loading datasets (via T015 logic, assumed pre-processed to streamed_temp.csv)
    2. Computing transition matrix (T016a, assumed pre-computed to markov_state.json)
    3. Computing surprisal (this task)
    
    For T016b specifically, we assume T015 and T016a have already run.
    We read from data/processed/streamed_temp.csv and data/processed/markov_state.json.
    """
    data_dir = get_data_dir()
    processed_dir = get_processed_dir()
    
    # Paths
    input_path = processed_dir / "streamed_temp.csv"
    markov_path = processed_dir / "markov_state.json"
    
    if output_path is None:
        output_path = processed_dir / "standardized.csv"
    
    # Check prerequisites
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. Did T015 run?")
    if not markov_path.exists():
        raise FileNotFoundError(f"Markov state not found: {markov_path}. Did T016a run?")
    
    # Run surprisal computation
    result_path = compute_surprisal(
        input_path=input_path,
        output_path=output_path,
        markov_path=markov_path
    )
    
    return result_path

def main():
    """Entry point for T016b execution."""
    set_seed(42)
    
    try:
        logger.info("Starting T016b: Compute Surprisal & Write Output")
        
        # Read dataset IDs if needed (though for T016b we rely on pre-processed files)
        # The task specifically says: "Read data/processed/streamed_temp.csv"
        # So we don't need to fetch datasets again here.
        
        output_path = run_preprocessing_pipeline(dataset_ids=[])
        
        logger.info(f"Pipeline complete. Output: {output_path}")
        
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()