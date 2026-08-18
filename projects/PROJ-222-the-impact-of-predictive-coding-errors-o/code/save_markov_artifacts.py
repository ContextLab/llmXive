import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import pandas as pd
import numpy as np
import hashlib

from config import get_data_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_standardized_data(data_dir: Path) -> pd.DataFrame:
    """
    Load the standardized CSV produced by T017.
    
    Args:
        data_dir: Path to the data/processed directory.
        
    Returns:
        DataFrame containing the standardized data.
        
    Raises:
        FileNotFoundError: If the standardized.csv file does not exist.
        ValueError: If required columns are missing.
    """
    input_path = data_dir / "standardized.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Standardized data not found at {input_path}. "
                                "Ensure T017 has been completed successfully.")
    
    df = pd.read_csv(input_path)
    required_cols = ['stimulus_sequence', 'duration_estimate', 'participant_id']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in standardized.csv: {missing}")
    
    logger.info(f"Loaded standardized data with {len(df)} rows from {input_path}")
    return df

def compute_transition_matrices(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute transition probability tables and Markov model state from the data.
    
    This function calculates the transition probabilities between consecutive stimuli
    for each participant and condition, effectively building the Markov model state.
    
    Args:
        df: DataFrame with 'stimulus_sequence', 'participant_id', and optionally 'condition'.
            
    Returns:
        Dictionary containing:
            - 'transitions': Dict mapping (participant_id, condition) to transition matrix (dict of dicts)
            - 'statistics': Summary statistics (counts, unique states)
            - 'metadata': Timestamp and version info
    """
    logger.info("Computing transition probability tables...")
    
    # Ensure stimulus_sequence is treated as strings for consistent hashing
    df['stimulus_sequence'] = df['stimulus_sequence'].astype(str)
    
    transitions = {}
    stats = {
        'total_sequences': 0,
        'unique_states_global': set(),
        'participant_count': df['participant_id'].nunique()
    }
    
    # Group by participant and optional condition to build per-subject models
    group_cols = ['participant_id']
    if 'condition' in df.columns:
        group_cols.append('condition')
        
    grouped = df.groupby(group_cols)
    
    for name, group in grouped:
        key = name if len(name) > 1 else name[0]
        sequences = group['stimulus_sequence'].tolist()
        
        # Flatten all sequences for this group to count transitions
        all_transitions = {}
        unique_states = set()
        
        for seq in sequences:
            # Handle sequence representation: could be list string or single token
            # Assuming sequences are comma-separated or space-separated strings
            # If the data is already tokenized per row, we need to reconstruct sequences
            # based on time or order. 
            # Given typical time-perception data, we assume 'stimulus_sequence' column 
            # contains the full sequence string for that trial, or we need to group by trial_id.
            # However, for Markov modeling of sequential stimuli, we usually look at 
            # transitions between consecutive stimuli IN A SEQUENCE.
            
            # If 'stimulus_sequence' is the full sequence (e.g., "A,B,C"), split it:
            if isinstance(seq, str) and ',' in seq:
                tokens = [t.strip() for t in seq.split(',')]
            else:
                tokens = [seq]
            
            unique_states.update(tokens)
            
            # Count transitions
            for i in range(len(tokens) - 1):
                src = tokens[i]
                dst = tokens[i+1]
                if src not in all_transitions:
                    all_transitions[src] = {}
                if dst not in all_transitions[src]:
                    all_transitions[src][dst] = 0
                all_transitions[src][dst] += 1
        
        # Convert counts to probabilities
        prob_matrix = {}
        for src, dst_counts in all_transitions.items():
            total = sum(dst_counts.values())
            prob_matrix[src] = {dst: count/total for dst, count in dst_counts.items()}
        
        transitions[str(key)] = prob_matrix
        stats['unique_states_global'].update(unique_states)
        
        # Estimate sequence count (heuristic: number of rows if one row per sequence)
        stats['total_sequences'] += len(sequences)
    
    # Convert set to list for JSON serialization
    stats['unique_states_global'] = list(stats['unique_states_global'])
    
    result = {
        'transitions': transitions,
        'statistics': stats,
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'version': '1.0.0',
            'method': 'empirical_frequency',
            'description': 'Transition probability tables derived from standardized time-perception data'
        }
    }
    
    logger.info(f"Computed transition matrices for {len(transitions)} participant/condition groups")
    return result

def save_markov_artifacts(artifacts: Dict[str, Any], output_dir: Path) -> str:
    """
    Save the Markov model artifacts to disk.
    
    Args:
        artifacts: Dictionary containing transition matrices and metadata.
        output_dir: Directory to save the artifacts.
        
    Returns:
        Path to the saved JSON file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "markov_model_state.json"
    
    with open(output_path, 'w') as f:
        json.dump(artifacts, f, indent=2, default=str)
    
    # Compute checksum
    with open(output_path, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
    
    logger.info(f"Saved Markov model state to {output_path} (SHA256: {checksum[:16]}...)")
    return str(output_path)

def run_t017b():
    """
    Main entry point for Task T017b: Save transition-probability tables and Markov model state.
    
    This function:
    1. Loads the standardized data from T017
    2. Computes transition probability tables
    3. Saves the artifacts to data/processed/
    """
    logger.info("Starting T017b: Save Markov artifacts")
    
    data_dir = get_data_dir() / "processed"
    
    try:
        # Load data
        df = load_standardized_data(data_dir)
        
        # Compute artifacts
        artifacts = compute_transition_matrices(df)
        
        # Save artifacts
        output_path = save_markov_artifacts(artifacts, data_dir)
        
        logger.info(f"T017b completed successfully. Output: {output_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data dependency error: {e}")
        logger.error("Please ensure T017 (generate_standardized_output) has been run first.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T017b execution: {e}")
        raise

if __name__ == "__main__":
    sys.exit(run_t017b())
