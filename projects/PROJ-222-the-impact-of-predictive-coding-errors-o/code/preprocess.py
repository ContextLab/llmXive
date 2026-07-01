"""
Preprocessing module for time perception datasets.
Implements filtering logic (FR-002) and Markov surprisal calculation (FR-003).
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

# Import config utilities
from config import get_data_dir, set_seed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SEQUENTIAL_STIMULI_THRESHOLD = 0.5  # Minimum proportion of sequential pairs to consider "sequential"
PREDICTABILITY_THRESHOLD = 0.1      # Minimum entropy reduction to consider "predictable"

def load_dataset(file_path: str) -> pd.DataFrame:
    """Load a dataset from CSV or other supported formats."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    suffix = path.suffix.lower()
    if suffix == '.csv':
        return pd.read_csv(path)
    elif suffix in ['.parquet', '.pq']:
        return pd.read_parquet(path)
    elif suffix in ['.json', '.jsonl']:
        return pd.read_json(path)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

def is_sequential_stimuli(df: pd.DataFrame, stimulus_col: str = 'stimulus_sequence') -> Tuple[bool, float]:
    """
    Check if the dataset contains sequential stimuli.
    
    A dataset is considered to have sequential stimuli if there is a non-random
    temporal or logical ordering in the stimulus sequence that can be predicted.
    
    Args:
        df: DataFrame containing the dataset
        stimulus_col: Column name containing stimulus sequence data
        
    Returns:
        Tuple of (is_sequential, sequential_score)
    """
    if stimulus_col not in df.columns:
        return False, 0.0
    
    sequence = df[stimulus_col].dropna()
    if len(sequence) < 3:
        return False, 0.0
    
    # Check for temporal ordering (e.g., time series, ordered events)
    # Calculate autocorrelation at lag 1
    try:
        # Convert to numeric if possible
        numeric_seq = pd.to_numeric(sequence, errors='ignore')
        if numeric_seq.dtype == 'object':
            # For categorical sequences, convert to codes
            unique_vals = pd.unique(sequence)
            mapping = {v: i for i, v in enumerate(unique_vals)}
            numeric_seq = sequence.map(mapping)
        
        # Calculate autocorrelation
        if len(numeric_seq) > 1:
            autocorr = np.corrcoef(numeric_seq[:-1], numeric_seq[1:])[0, 1]
            if np.isnan(autocorr):
                autocorr = 0.0
        else:
            autocorr = 0.0
    except Exception:
        autocorr = 0.0
    
    # Check for patterns in the sequence
    # Calculate transition probabilities
    transitions = []
    for i in range(len(sequence) - 1):
        transitions.append((sequence.iloc[i], sequence.iloc[i+1]))
    
    if len(transitions) == 0:
        return False, 0.0
    
    # Calculate entropy of transitions
    transition_counts = Counter(transitions)
    total_transitions = len(transitions)
    
    # Calculate entropy
    entropy = 0.0
    for count in transition_counts.values():
        prob = count / total_transitions
        if prob > 0:
            entropy -= prob * np.log2(prob)
    
    # Maximum possible entropy for the number of unique transitions
    unique_transitions = len(transition_counts)
    max_entropy = np.log2(max(unique_transitions, 2))
    
    # Normalized entropy (lower = more predictable)
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 1.0
    
    # Sequential score combines autocorrelation and predictability
    sequential_score = (abs(autocorr) + (1 - normalized_entropy)) / 2
    
    is_sequential = sequential_score >= SEQUENTIAL_STIMULI_THRESHOLD
    
    return is_sequential, sequential_score

def has_predictability_manipulation(df: pd.DataFrame, 
                                   stimulus_col: str = 'stimulus_sequence',
                                   predictability_col: str = None) -> Tuple[bool, float]:
    """
    Check if the dataset contains predictability manipulations.
    
    A dataset has predictability manipulations if it explicitly varies the
    predictability of stimuli (e.g., high vs low probability conditions).
    
    Args:
        df: DataFrame containing the dataset
        stimulus_col: Column name containing stimulus sequence
        predictability_col: Optional column name containing predictability labels
        
    Returns:
        Tuple of (has_manipulation, manipulation_score)
    """
    # Check if there's an explicit predictability column
    if predictability_col and predictability_col in df.columns:
        unique_vals = df[predictability_col].nunique()
        if unique_vals >= 2:
            return True, 1.0
    
    # Infer from sequence patterns
    # Check if there are distinct blocks or conditions with different predictability
    sequence = df[stimulus_col].dropna() if stimulus_col in df.columns else None
    
    if sequence is None or len(sequence) < 10:
        return False, 0.0
    
    # Try to detect blocks with different transition patterns
    block_size = max(10, len(sequence) // 10)
    blocks = []
    
    for i in range(0, len(sequence), block_size):
        block = sequence.iloc[i:i+block_size]
        if len(block) > 1:
            blocks.append(block)
    
    if len(blocks) < 2:
        return False, 0.0
    
    # Calculate entropy for each block
    block_entropies = []
    for block in blocks:
        transitions = []
        for j in range(len(block) - 1):
            transitions.append((block.iloc[j], block.iloc[j+1]))
        
        if len(transitions) > 0:
            transition_counts = Counter(transitions)
            total = len(transitions)
            entropy = 0.0
            for count in transition_counts.values():
                prob = count / total
                if prob > 0:
                    entropy -= prob * np.log2(prob)
            block_entropies.append(entropy)
    
    if len(block_entropies) < 2:
        return False, 0.0
    
    # Check for significant variation in entropy across blocks
    entropy_std = np.std(block_entropies)
    entropy_mean = np.mean(block_entropies)
    
    # Coefficient of variation
    cv = entropy_std / entropy_mean if entropy_mean > 0 else 0.0
    
    # Higher CV indicates more variation in predictability across blocks
    manipulation_score = min(cv, 1.0)  # Cap at 1.0
    
    has_manipulation = manipulation_score >= PREDICTABILITY_THRESHOLD
    
    return has_manipulation, manipulation_score

def filter_datasets(input_dir: str, 
                   output_dir: str,
                   exclusion_log_path: str) -> Dict[str, Any]:
    """
    Filter datasets based on sequential stimuli and predictability criteria (FR-002).
    
    Args:
        input_dir: Directory containing raw datasets
        output_dir: Directory to save filtered datasets
        exclusion_log_path: Path to save exclusion log
        
    Returns:
        Dictionary with filtering statistics
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    exclusion_log = []
    stats = {
        'total_datasets': 0,
        'kept_datasets': 0,
        'excluded_datasets': 0,
        'exclusion_reasons': {}
    }
    
    # Find all dataset files
    dataset_files = list(input_path.glob('*.csv')) + list(input_path.glob('*.parquet')) + list(input_path.glob('*.json'))
    
    for file_path in dataset_files:
        stats['total_datasets'] += 1
        filename = file_path.name
        logger.info(f"Processing dataset: {filename}")
        
        try:
            df = load_dataset(str(file_path))
            
            # Check for required columns
            required_cols = ['stimulus_sequence', 'participant_id']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                reason = f"Missing required columns: {', '.join(missing_cols)}"
                exclusion_log.append({
                    'dataset': filename,
                    'reason': reason,
                    'type': 'missing_columns'
                })
                stats['exclusion_reasons'][reason] = stats['exclusion_reasons'].get(reason, 0) + 1
                stats['excluded_datasets'] += 1
                continue
            
            # Check for sequential stimuli
            is_sequential, sequential_score = is_sequential_stimuli(df)
            
            if not is_sequential:
                reason = f"Insufficient sequential structure (score: {sequential_score:.3f})"
                exclusion_log.append({
                    'dataset': filename,
                    'reason': reason,
                    'score': sequential_score,
                    'type': 'non_sequential'
                })
                stats['exclusion_reasons'][reason] = stats['exclusion_reasons'].get(reason, 0) + 1
                stats['excluded_datasets'] += 1
                continue
            
            # Check for predictability manipulations
            has_manipulation, manipulation_score = has_predictability_manipulation(df)
            
            if not has_manipulation:
                reason = f"No predictability manipulation detected (score: {manipulation_score:.3f})"
                exclusion_log.append({
                    'dataset': filename,
                    'reason': reason,
                    'score': manipulation_score,
                    'type': 'no_predictability'
                })
                stats['exclusion_reasons'][reason] = stats['exclusion_reasons'].get(reason, 0) + 1
                stats['excluded_datasets'] += 1
                continue
            
            # Dataset passed all filters
            output_file = output_path / filename
            df.to_csv(output_file, index=False)
            stats['kept_datasets'] += 1
            logger.info(f"  ✓ Kept: {filename}")
            
        except Exception as e:
            reason = f"Error processing dataset: {str(e)}"
            exclusion_log.append({
                'dataset': filename,
                'reason': reason,
                'type': 'processing_error'
            })
            stats['exclusion_reasons'][reason] = stats['exclusion_reasons'].get(reason, 0) + 1
            stats['excluded_datasets'] += 1
            logger.error(f"  ✗ Error: {filename} - {str(e)}")
    
    # Write exclusion log
    with open(exclusion_log_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    
    # Update stats with exclusion log
    stats['exclusion_log_path'] = exclusion_log_path
    
    logger.info(f"Filtering complete: {stats['kept_datasets']} kept, {stats['excluded_datasets']} excluded")
    return stats

def compute_markov_surprisal(df: pd.DataFrame, 
                            stimulus_col: str = 'stimulus_sequence',
                            output_col: str = 'surprisal') -> pd.DataFrame:
    """
    Compute Markov surprisal (Shannon entropy of transition) for each stimulus.
    
    Surprisal = -log2(P(transition)), where P(transition) is the probability
    of the observed transition given the previous stimulus.
    
    Args:
        df: DataFrame containing stimulus sequence
        stimulus_col: Column name containing stimulus sequence
        output_col: Column name for the computed surprisal values
        
    Returns:
        DataFrame with added surprisal column
    """
    df = df.copy()
    sequence = df[stimulus_col].dropna().reset_index(drop=True)
    
    if len(sequence) < 2:
        df[output_col] = np.nan
        return df
    
    # Calculate transition probabilities
    transitions = []
    for i in range(len(sequence) - 1):
        transitions.append((sequence.iloc[i], sequence.iloc[i+1]))
    
    transition_counts = Counter(transitions)
    total_transitions = len(transitions)
    
    # Calculate probability for each transition
    transition_probs = {}
    for trans, count in transition_counts.items():
        transition_probs[trans] = count / total_transitions
    
    # Compute surprisal for each position (starting from index 1)
    surprisal_values = [np.nan]  # First element has no previous transition
    for i in range(1, len(sequence)):
        prev_stim = sequence.iloc[i-1]
        curr_stim = sequence.iloc[i]
        transition = (prev_stim, curr_stim)
        
        prob = transition_probs.get(transition, 1e-10)  # Avoid log(0)
        surprisal = -np.log2(prob)
        surprisal_values.append(surprisal)
    
    # Map back to original DataFrame
    # Create a mapping from original index to surprisal value
    original_indices = df[df[stimulus_col].notna()].index.tolist()
    
    # Create a series for surprisal aligned with original DataFrame
    surprisal_series = pd.Series(np.nan, index=df.index)
    
    for i, orig_idx in enumerate(original_indices):
        if i < len(surprisal_values):
            surprisal_series[orig_idx] = surprisal_values[i]
    
    df[output_col] = surprisal_series
    
    return df

def run_preprocessing_pipeline(raw_input_dir: str, 
                              filtered_output_dir: str,
                              processed_output_dir: str,
                              exclusion_log_path: str) -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline:
    1. Filter datasets (FR-002)
    2. Compute Markov surprisal (FR-003)
    3. Generate standardized output
    
    Args:
        raw_input_dir: Directory with raw downloaded datasets
        filtered_output_dir: Directory for filtered datasets
        processed_output_dir: Directory for final processed data
        exclusion_log_path: Path for exclusion log
        
    Returns:
        Dictionary with pipeline statistics
    """
    logger.info("Starting preprocessing pipeline...")
    
    # Step 1: Filter datasets
    filter_stats = filter_datasets(raw_input_dir, filtered_output_dir, exclusion_log_path)
    
    # Step 2: Compute surprisal and standardize
    processed_files = []
    processed_stats = {
        'total_processed': 0,
        'surprisal_computed': 0,
        'errors': []
    }
    
    filtered_path = Path(filtered_output_dir)
    processed_path = Path(processed_output_dir)
    processed_path.mkdir(parents=True, exist_ok=True)
    
    for file_path in filtered_path.glob('*.csv'):
        try:
            df = pd.read_csv(file_path)
            
            # Compute surprisal
            if 'stimulus_sequence' in df.columns:
                df = compute_markov_surprisal(df)
                processed_stats['surprisal_computed'] += 1
            
            # Standardize column names if needed
            # Ensure required columns exist
            required_cols = ['duration_estimate', 'stimulus_sequence', 'participant_id', 'surprisal']
            existing_cols = df.columns.tolist()
            
            # Add missing required columns with NaN if not present
            for col in required_cols:
                if col not in existing_cols:
                    df[col] = np.nan
            
            # Reorder columns
            final_cols = [col for col in required_cols if col in df.columns]
            other_cols = [col for col in df.columns if col not in required_cols]
            df = df[final_cols + other_cols]
            
            # Save standardized output
            output_file = processed_path / file_path.name
            df.to_csv(output_file, index=False)
            processed_files.append(str(output_file))
            processed_stats['total_processed'] += 1
            
            logger.info(f"  Processed: {file_path.name}")
            
        except Exception as e:
            processed_stats['errors'].append({
                'file': str(file_path),
                'error': str(e)
            })
            logger.error(f"  Error processing {file_path.name}: {str(e)}")
    
    # Generate combined standardized CSV
    if processed_files:
        combined_df = pd.concat([pd.read_csv(f) for f in processed_files], ignore_index=True)
        combined_output = processed_path / 'standardized.csv'
        combined_df.to_csv(combined_output, index=False)
        logger.info(f"Combined standardized output: {combined_output}")
    
    # Update stats
    processed_stats['exclusion_log'] = exclusion_log_path
    processed_stats['filter_stats'] = filter_stats
    
    logger.info("Preprocessing pipeline complete.")
    return {
        'filter_stats': filter_stats,
        'processed_stats': processed_stats,
        'output_file': str(Path(processed_output_dir) / 'standardized.csv')
    }

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run preprocessing pipeline')
    parser.add_argument('--raw-input', default='data/raw', help='Directory with raw datasets')
    parser.add_argument('--filtered-output', default='data/filtered', help='Directory for filtered datasets')
    parser.add_argument('--processed-output', default='data/processed', help='Directory for processed data')
    parser.add_argument('--exclusion-log', default='data/exclusion_log.json', help='Path for exclusion log')
    
    args = parser.parse_args()
    
    results = run_preprocessing_pipeline(
        raw_input_dir=args.raw_input,
        filtered_output_dir=args.filtered_output,
        processed_output_dir=args.processed_output,
        exclusion_log_path=args.exclusion_log
    )
    
    print(json.dumps(results, indent=2, default=str))
