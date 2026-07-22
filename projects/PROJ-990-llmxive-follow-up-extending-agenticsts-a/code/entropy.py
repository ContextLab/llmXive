import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import json
import os

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_shannon_entropy(probs: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Shannon entropy H = -sum(p_i * log(p_i)) for a given probability distribution.
    
    Args:
        probs: List or array of probabilities (must sum to 1.0, non-negative).
    
    Returns:
        float: Entropy value. Returns float('inf') if calculation results in NaN or Inf.
    """
    # Convert to numpy array for vectorized operations
    p = np.array(probs, dtype=float)
    
    # Filter out zero probabilities to avoid log(0)
    # p * log(p) where p=0 is defined as 0 in entropy calculation
    non_zero_mask = p > 0
    p_non_zero = p[non_zero_mask]
    
    if len(p_non_zero) == 0:
        # All probabilities are zero or empty distribution
        logger.warning("Empty probability distribution detected.")
        return float('inf')
    
    # Calculate entropy: -sum(p * log(p))
    # Using natural log (base e) as is standard for Shannon entropy in information theory
    # If base 2 is needed, use np.log2(p) instead
    entropy = -np.sum(p_non_zero * np.log(p_non_zero))
    
    # Check for NaN or Inf
    if np.isnan(entropy) or np.isinf(entropy):
        return float('inf')
    
    return float(entropy)

def extract_move_distribution(row: pd.Series) -> Optional[List[float]]:
    """
    Extract the legal move distribution from a dataframe row.
    
    The move distribution is expected to be stored as a JSON string or a list of floats
    in a column named 'legal_move_distribution' or similar.
    
    Args:
        row: A pandas Series representing a single trajectory turn.
    
    Returns:
        List[float]: The probability distribution of legal moves, or None if not found.
    """
    # Try common column names for move distribution
    possible_columns = ['legal_move_distribution', 'move_distribution', 'probabilities', 'move_probs']
    
    for col in possible_columns:
        if col in row.index:
            value = row[col]
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    logger.debug(f"Could not parse JSON in column {col}")
                    continue
            elif isinstance(value, (list, np.ndarray)):
                return list(value)
    
    # If no distribution found, return None
    return None

def calculate_entropy_for_trajectory(trajectory_id: str, turns: List[Dict]) -> List[Tuple[int, float]]:
    """
    Calculate entropy for each turn in a trajectory.
    
    Args:
        trajectory_id: Unique identifier for the trajectory.
        turns: List of dictionaries, each representing a turn with move distribution.
    
    Returns:
        List[Tuple[int, float]]: List of (turn_index, entropy_value) tuples.
    """
    results = []
    for turn_idx, turn_data in enumerate(turns):
        # Extract move distribution
        if 'legal_move_distribution' in turn_data:
            probs = turn_data['legal_move_distribution']
        elif 'move_distribution' in turn_data:
            probs = turn_data['move_distribution']
        else:
            # Try to get from a nested structure
            probs = turn_data.get('distribution', None)
        
        if probs is None or len(probs) == 0:
            # No valid distribution, assign NaN or skip
            logger.debug(f"Trajectory {trajectory_id}, turn {turn_idx}: No move distribution found.")
            continue
        
        # Calculate entropy
        entropy = calculate_shannon_entropy(probs)
        
        # Log warnings for edge cases
        if np.isnan(entropy) or np.isinf(entropy):
            logger.warning(f"Warning: NaN/Inf entropy detected at trajectory {trajectory_id}, turn {turn_idx}")
        
        results.append((turn_idx, entropy))
    
    return results

def process_trajectories(input_path: Union[str, Path], output_path: Union[str, Path]) -> pd.DataFrame:
    """
    Process all trajectories from input CSV, calculate entropy, and write to output CSV.
    
    Args:
        input_path: Path to input CSV containing trajectory metrics with move distributions.
        output_path: Path to output CSV where entropy results will be written.
    
    Returns:
        pd.DataFrame: The resulting dataframe with entropy calculations.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load the input data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Ensure we have the necessary columns
    required_cols = ['trajectory_id', 'turn_index']
    # Check for move distribution column
    move_dist_col = None
    possible_move_cols = ['legal_move_distribution', 'move_distribution', 'probabilities']
    for col in possible_move_cols:
        if col in df.columns:
            move_dist_col = col
            break
    
    if move_dist_col is None:
        raise ValueError(f"Could not find move distribution column in {input_path}. "
                       f"Expected one of: {possible_move_cols}")
    
    logger.info(f"Found move distribution column: {move_dist_col}")
    
    # Initialize list to store results
    results = []
    warnings_logged = []
    
    # Process each row
    for idx, row in df.iterrows():
        traj_id = row['trajectory_id']
        turn_idx = row['turn_index']
        
        # Extract probabilities
        probs = row[move_dist_col]
        
        # Handle string representations of lists
        if isinstance(probs, str):
            try:
                probs = json.loads(probs)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse move distribution for {traj_id}, turn {turn_idx}")
                continue
        
        if not isinstance(probs, (list, np.ndarray)) or len(probs) == 0:
            logger.warning(f"Invalid move distribution for {traj_id}, turn {turn_idx}")
            continue
        
        # Calculate entropy
        entropy = calculate_shannon_entropy(probs)
        
        # Check for edge cases and log warnings
        if np.isnan(entropy) or np.isinf(entropy):
            warning_msg = f"Warning: NaN/Inf entropy detected at trajectory {traj_id}, turn {turn_idx}"
            warnings_logged.append(warning_msg)
            logger.warning(warning_msg)
        
        results.append({
            'trajectory_id': traj_id,
            'turn_index': turn_idx,
            'entropy': entropy,
            'num_moves': len(probs) if isinstance(probs, (list, np.ndarray)) else 0
        })
    
    # Create output dataframe
    result_df = pd.DataFrame(results)
    
    # Write edge case warnings to log file
    if warnings_logged:
        log_path = Path(output_path).parent / 'edge_case_warnings.log'
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a') as f:
            for warning in warnings_logged:
                f.write(warning + '\n')
        logger.info(f"Wrote {len(warnings_logged)} entropy warnings to {log_path}")
    
    # Write output CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_path, index=False)
    logger.info(f"Entropy calculations written to {output_path}")
    
    return result_df

def main():
    """
    Main entry point for the entropy calculation task.
    Reads from data/processed/metrics_with_moves.csv and writes to data/processed/entropy_results.csv.
    """
    # Define paths
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / 'data' / 'processed' / 'metrics_with_moves.csv'
    output_path = base_dir / 'data' / 'processed' / 'entropy_results.csv'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Process trajectories and calculate entropy
        result_df = process_trajectories(input_path, output_path)
        
        # Log summary statistics
        logger.info(f"Processed {len(result_df)} turns")
        logger.info(f"Entropy range: [{result_df['entropy'].min():.4f}, {result_df['entropy'].max():.4f}]")
        logger.info(f"Mean entropy: {result_df['entropy'].mean():.4f}")
        
        return 0
    except Exception as e:
        logger.error(f"Error processing trajectories: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
