import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from config import get_data_dir, get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_dataset(filepath: str) -> pd.DataFrame:
    """
    Load a dataset from a CSV file.
    
    Args:
        filepath: Path to the CSV file.
        
    Returns:
        DataFrame containing the dataset.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {filepath}")
    
    logger.info(f"Loading dataset from {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
    return df


def is_sequential_stimuli(df: pd.DataFrame, sequence_col: str = 'stimulus_sequence') -> bool:
    """
    Check if the dataset contains sequential stimuli.
    
    Args:
        df: The dataset DataFrame.
        sequence_col: The name of the column containing stimulus sequence data.
        
    Returns:
        True if sequential stimuli are present, False otherwise.
    """
    if sequence_col not in df.columns:
        logger.warning(f"Sequence column '{sequence_col}' not found in dataset")
        return False
    
    # Check if the sequence column contains ordered or categorical data
    # For simplicity, we check if there are multiple unique values
    unique_vals = df[sequence_col].nunique()
    is_sequential = unique_vals > 1
    
    if is_sequential:
        logger.info(f"Dataset contains sequential stimuli ({unique_vals} unique values)")
    else:
        logger.warning("Dataset does not appear to contain sequential stimuli")
        
    return is_sequential


def has_predictability_manipulation(df: pd.DataFrame, condition_col: str = 'condition') -> bool:
    """
    Check if the dataset contains predictability manipulations.
    
    Args:
        df: The dataset DataFrame.
        condition_col: The name of the column containing condition labels.
        
    Returns:
        True if predictability manipulations are present, False otherwise.
    """
    if condition_col not in df.columns:
        logger.warning(f"Condition column '{condition_col}' not found in dataset")
        return False
    
    unique_conditions = df[condition_col].nunique()
    has_manipulation = unique_conditions > 1
    
    if has_manipulation:
        logger.info(f"Dataset contains predictability manipulations ({unique_conditions} conditions)")
    else:
        logger.warning("Dataset does not appear to contain predictability manipulations")
        
    return has_manipulation


def filter_datasets(
    datasets: List[pd.DataFrame], 
    conditions: List[Dict[str, Any]]
) -> List[pd.DataFrame]:
    """
    Filter datasets based on specified conditions.
    
    Args:
        datasets: List of DataFrames to filter.
        conditions: List of condition dictionaries with 'type' and 'params'.
        
    Returns:
        List of filtered DataFrames.
    """
    filtered = []
    
    for i, df in enumerate(datasets):
        keep = True
        reasons = []
        
        for cond in conditions:
            if cond['type'] == 'sequential_stimuli':
                if not is_sequential_stimuli(df, cond.get('column', 'stimulus_sequence')):
                    keep = False
                    reasons.append("Missing sequential stimuli")
                    
            elif cond['type'] == 'predictability_manipulation':
                if not has_predictability_manipulation(df, cond.get('column', 'condition')):
                    keep = False
                    reasons.append("Missing predictability manipulation")
                    
            elif cond['type'] == 'min_rows':
                if len(df) < cond['value']:
                    keep = False
                    reasons.append(f"Dataset has fewer than {cond['value']} rows")
                    
        if keep:
            filtered.append(df)
            logger.info(f"Dataset {i} passed all filters")
        else:
            logger.warning(f"Dataset {i} excluded: {'; '.join(reasons)}")
            
    return filtered


def compute_markov_surprisal(
    df: pd.DataFrame,
    sequence_col: str = 'stimulus_sequence',
    order: int = 1
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Compute Markov surprisal based on Shannon entropy of transitions.
    
    This function calculates the surprisal (negative log probability) of each
    stimulus in the sequence based on the transition probabilities from the
    previous 'order' stimuli.
    
    Args:
        df: The dataset DataFrame.
        sequence_col: The name of the column containing the stimulus sequence.
        order: The order of the Markov model (1 for first-order, 2 for second-order, etc.)
        
    Returns:
        A tuple containing:
        - DataFrame with added 'surprisal' column
        - Dictionary containing the transition probability table and model state
    """
    if sequence_col not in df.columns:
        raise ValueError(f"Sequence column '{sequence_col}' not found in dataset")
    
    sequence = df[sequence_col].values
    n = len(sequence)
    
    if n == 0:
        logger.warning("Empty sequence provided")
        df['surprisal'] = np.nan
        return df, {'transition_table': {}, 'model_state': {}}
    
    # Build transition probability table
    # Key: tuple of previous 'order' stimuli -> Value: dict of next stimulus counts
    transition_counts = {}
    
    for i in range(order, n):
        # Get the context (previous 'order' stimuli)
        context = tuple(sequence[i-order:i])
        next_stimulus = sequence[i]
        
        if context not in transition_counts:
            transition_counts[context] = {}
        
        if next_stimulus not in transition_counts[context]:
            transition_counts[context][next_stimulus] = 0
        
        transition_counts[context][next_stimulus] += 1
    
    # Convert counts to probabilities
    transition_probs = {}
    for context, next_counts in transition_counts.items():
        total = sum(next_counts.values())
        transition_probs[context] = {
            stimulus: count / total 
            for stimulus, count in next_counts.items()
        }
    
    # Calculate surprisal for each stimulus (starting from index 'order')
    surprisals = np.full(n, np.nan)
    
    for i in range(order, n):
        context = tuple(sequence[i-order:i])
        next_stimulus = sequence[i]
        
        if context in transition_probs and next_stimulus in transition_probs[context]:
            prob = transition_probs[context][next_stimulus]
            # Surprisal = -log2(probability)
            # Using log base 2 for information theoretic units (bits)
            if prob > 0:
                surprisals[i] = -np.log2(prob)
            else:
                surprisals[i] = np.inf  # Impossible transition
        else:
            # Unseen transition - assign maximum surprisal based on context
            # Use the inverse of the number of possible next stimuli
            # Or simply assign a high value (e.g., log2 of total unique stimuli)
            unique_stimuli = len(np.unique(sequence))
            surprisals[i] = np.log2(unique_stimuli) if unique_stimuli > 1 else 0
    
    # Add surprisal column to DataFrame
    df = df.copy()
    df['surprisal'] = surprisals
    
    # Prepare model state for output
    model_state = {
        'order': order,
        'sequence_length': n,
        'unique_stimuli': int(np.unique(sequence).size),
        'transitions_observed': len(transition_probs),
        'surprisal_range': {
            'min': float(np.nanmin(surprisals)),
            'max': float(np.nanmax(surprisals)),
            'mean': float(np.nanmean(surprisals)),
            'std': float(np.nanstd(surprisals))
        }
    }
    
    # Convert transition_probs keys (tuples) to strings for JSON serialization
    transition_table_serializable = {
        str(k): v for k, v in transition_probs.items()
    }
    
    logger.info(f"Computed Markov surprisal (order={order}) for {n} stimuli")
    logger.info(f"Surprisal range: {model_state['surprisal_range']['min']:.2f} to {model_state['surprisal_range']['max']:.2f}")
    
    return df, {
        'transition_table': transition_table_serializable,
        'model_state': model_state
    }


def run_preprocessing_pipeline(
    input_dir: str,
    output_dir: str,
    conditions: Optional[List[Dict[str, Any]]] = None,
    markov_order: int = 1
) -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline:
    1. Load datasets from input directory
    2. Filter based on conditions
    3. Compute Markov surprisal
    4. Save standardized output and artifacts
    
    Args:
        input_dir: Directory containing input CSV files.
        output_dir: Directory to save processed outputs.
        conditions: List of filtering conditions (optional, defaults to basic checks).
        markov_order: Order of the Markov model for surprisal calculation.
        
    Returns:
        Dictionary containing pipeline results and metadata.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Default conditions if none provided
    if conditions is None:
        conditions = [
            {'type': 'sequential_stimuli', 'column': 'stimulus_sequence'},
            {'type': 'predictability_manipulation', 'column': 'condition'},
            {'type': 'min_rows', 'value': 100}
        ]
    
    # Find all CSV files in input directory
    csv_files = list(input_path.glob('*.csv'))
    if not csv_files:
        logger.warning(f"No CSV files found in {input_dir}")
        return {'status': 'no_data', 'message': 'No input files found'}
    
    logger.info(f"Found {len(csv_files)} CSV files in {input_dir}")
    
    # Load all datasets
    datasets = []
    file_paths = []
    
    for csv_file in csv_files:
        try:
            df = load_dataset(str(csv_file))
            datasets.append(df)
            file_paths.append(csv_file.name)
        except Exception as e:
            logger.error(f"Failed to load {csv_file}: {e}")
    
    if not datasets:
        return {'status': 'error', 'message': 'No datasets loaded successfully'}
    
    # Filter datasets
    filtered_datasets = filter_datasets(datasets, conditions)
    
    if not filtered_datasets:
        return {'status': 'filtered_out', 'message': 'All datasets excluded by filters'}
    
    logger.info(f"Filtered to {len(filtered_datasets)} datasets")
    
    # Compute Markov surprisal for each dataset
    processed_datasets = []
    artifacts = []
    
    for i, (df, filename) in enumerate(zip(filtered_datasets, file_paths)):
        try:
            processed_df, model_artifact = compute_markov_surprisal(
                df, 
                sequence_col='stimulus_sequence', 
                order=markov_order
            )
            processed_datasets.append(processed_df)
            
            # Save transition table and model state
            artifact_path = output_path / f"{Path(filename).stem}_markov_artifact.json"
            with open(artifact_path, 'w') as f:
                json.dump(model_artifact, f, indent=2)
            artifacts.append(str(artifact_path))
            
        except Exception as e:
            logger.error(f"Failed to compute surprisal for {filename}: {e}")
            continue
    
    if not processed_datasets:
        return {'status': 'error', 'message': 'No datasets processed successfully'}
    
    # Concatenate all processed datasets
    combined_df = pd.concat(processed_datasets, ignore_index=True)
    
    # Save standardized output
    output_file = output_path / 'standardized.csv'
    combined_df.to_csv(output_file, index=False)
    
    # Save checksum
    import hashlib
    with open(output_file, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
    
    checksum_file = output_path / 'standardized.csv.sha256'
    with open(checksum_file, 'w') as f:
        f.write(checksum)
    
    logger.info(f"Saved standardized output to {output_file}")
    logger.info(f"Total rows: {len(combined_df)}")
    logger.info(f"Checksum: {checksum}")
    
    return {
        'status': 'success',
        'output_file': str(output_file),
        'checksum': checksum,
        'rows_processed': len(combined_df),
        'datasets_processed': len(processed_datasets),
        'artifacts': artifacts
    }