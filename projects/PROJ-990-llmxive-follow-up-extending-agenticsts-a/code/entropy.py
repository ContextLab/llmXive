"""
Entropy calculation module for AgenticSTS.

Calculates Shannon entropy of legal move distributions from trajectory data.
Implements edge case handling for NaN/Inf values by triggering full-layer retrieval.
"""
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import json

from config import load_config_from_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sentinel value for invalid entropy calculations
ENTROPY_INVALID_SENTINEL = -1.0

def calculate_shannon_entropy(probabilities: Union[np.ndarray, List[float]]) -> float:
    """
    Calculate Shannon entropy of a probability distribution.
    
    Args:
        probabilities: Array of probabilities (must sum to 1.0)
        
    Returns:
        Shannon entropy value, or ENTROPY_INVALID_SENTINEL if calculation fails
    """
    # Convert to numpy array
    probs = np.array(probabilities, dtype=float)
    
    # Filter out zero probabilities (log(0) is undefined)
    probs = probs[probs > 0]
    
    if len(probs) == 0:
        logger.warning("No valid probabilities found in distribution")
        return ENTROPY_INVALID_SENTINEL
    
    # Normalize to ensure sum is 1.0 (handle floating point errors)
    probs = probs / probs.sum()
    
    try:
        # Calculate entropy: H = -sum(p * log(p))
        entropy = -np.sum(probs * np.log2(probs))
        
        # Check for NaN or Inf
        if np.isnan(entropy) or np.isinf(entropy):
            logger.warning(f"Entropy calculation resulted in {entropy} for probabilities {probs}")
            return ENTROPY_INVALID_SENTINEL
        
        return float(entropy)
        
    except Exception as e:
        logger.warning(f"Entropy calculation failed: {e}")
        return ENTROPY_INVALID_SENTINEL

def extract_move_distribution(trajectory_row: pd.Series) -> Dict[str, float]:
    """
    Extract legal move probabilities from a trajectory row.
    
    Args:
        trajectory_row: A single row from the trajectories DataFrame
        
    Returns:
        Dictionary mapping move_id to probability
    """
    # Expected format: move_distribution column contains JSON string or dict
    # Format: {"move_1": 0.3, "move_2": 0.5, "move_3": 0.2}
    
    move_dist_raw = trajectory_row.get('move_distribution', '{}')
    
    if isinstance(move_dist_raw, str):
        try:
            move_dist = json.loads(move_dist_raw)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse move distribution: {move_dist_raw}")
            return {}
    elif isinstance(move_dist_raw, dict):
        move_dist = move_dist_raw
    else:
        logger.warning(f"Unexpected move distribution type: {type(move_dist_raw)}")
        return {}
    
    return move_dist

def calculate_entropy_for_trajectory(
    trajectory_row: pd.Series,
    use_log_base: int = 2
) -> Tuple[float, bool, str]:
    """
    Calculate entropy for a single trajectory turn.
    
    Args:
        trajectory_row: A single row from the trajectories DataFrame
        use_log_base: Log base for entropy calculation (default 2)
        
    Returns:
        Tuple of (entropy_value, is_valid, error_message)
    """
    move_dist = extract_move_distribution(trajectory_row)
    
    if not move_dist:
        logger.warning(f"No move distribution found for turn {trajectory_row.get('turn', 'unknown')}")
        return (ENTROPY_INVALID_SENTINEL, False, "No move distribution")
    
    probabilities = list(move_dist.values())
    
    if len(probabilities) == 0:
        return (ENTROPY_INVALID_SENTINEL, False, "Empty probability list")
    
    # Calculate entropy
    entropy = calculate_shannon_entropy(probabilities)
    
    is_valid = entropy != ENTROPY_INVALID_SENTINEL
    error_msg = "" if is_valid else f"Entropy calculation failed for turn {trajectory_row.get('turn', 'unknown')}"
    
    if not is_valid:
        logger.warning(f"Invalid entropy detected for turn {trajectory_row.get('turn', 'unknown')}: triggering full-layer retrieval")
    
    return (entropy, is_valid, error_msg)

def process_trajectories(
    input_path: str,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Process trajectory file and calculate entropy for each turn.
    
    Args:
        input_path: Path to input trajectories CSV
        output_path: Optional path to write output CSV with entropy values
        
    Returns:
        DataFrame with added entropy column
    """
    config = load_config_from_file()
    
    # Load trajectories
    logger.info(f"Loading trajectories from {input_path}")
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Calculate entropy for each row
    results = []
    invalid_count = 0
    
    for idx, row in df.iterrows():
        entropy, is_valid, error_msg = calculate_entropy_for_trajectory(row)
        
        if not is_valid:
            invalid_count += 1
            # Log specific error details
            logger.warning(f"Row {idx}: {error_msg} - triggering full 'all-layers' set retrieval")
        
        results.append({
            'row_index': idx,
            'turn': row.get('turn', None),
            'entropy': entropy,
            'is_valid': is_valid,
            'requires_full_layers': not is_valid
        })
    
    entropy_df = pd.DataFrame(results)
    
    # Merge with original dataframe
    df_with_entropy = df.merge(entropy_df, left_index=True, right_on='row_index', how='left')
    df_with_entropy.drop(columns=['row_index'], inplace=True)
    
    # Summary statistics
    logger.info(f"Processed {len(df)} rows: {len(df) - invalid_count} valid, {invalid_count} invalid (triggering full-layer retrieval)")
    
    if output_path:
        df_with_entropy.to_csv(output_path, index=False)
        logger.info(f"Saved entropy results to {output_path}")
    
    return df_with_entropy

def main():
    """Main entry point for entropy calculation."""
    config = load_config_from_file()
    
    input_path = config.get('paths', {}).get('raw_trajectories', 'data/raw/trajectories.csv')
    output_path = config.get('paths', {}).get('processed_entropy', 'data/processed/entropy_results.csv')
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        result_df = process_trajectories(input_path, output_path)
        
        # Print summary
        valid_count = result_df['is_valid'].sum()
        invalid_count = len(result_df) - valid_count
        
        print(f"Entropy Calculation Complete:")
        print(f"  Total rows: {len(result_df)}")
        print(f"  Valid entropy: {valid_count}")
        print(f"  Invalid (triggering full-layer retrieval): {invalid_count}")
        
        if invalid_count > 0:
            print(f"  WARNING: {invalid_count} rows have invalid entropy and will trigger full 'all-layers' set retrieval")
            
    except Exception as e:
        logger.error(f"Entropy calculation failed: {e}")
        raise

if __name__ == "__main__":
    main()
