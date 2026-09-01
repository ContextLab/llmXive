import numpy as np
import pandas as pd
import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/edge_case_warnings.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
INPUT_FILE = Path("data/processed/metrics_with_moves.csv")
OUTPUT_FILE = Path("data/processed/entropy_metrics.csv")
LOG_FILE = Path("data/processed/edge_case_warnings.log")
SENTINEL_VALUE = -1.0  # Sentinel for NaN/Inf to trigger fallback

def setup_logging():
    """Ensure log directory exists and logger is configured."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def calculate_shannon_entropy(probabilities: np.ndarray) -> float:
    """
    Calculate Shannon entropy of a probability distribution.
    
    Args:
        probabilities: Array of probabilities (must sum to 1).
        
    Returns:
        Shannon entropy in bits. Returns -1.0 if distribution is invalid (NaN/Inf).
    """
    # Filter out zero probabilities to avoid log(0)
    p = probabilities[probabilities > 0]
    
    if len(p) == 0:
        # No moves available? This is an edge case.
        logger.warning("Empty probability distribution encountered.")
        return SENTINEL_VALUE

    try:
        entropy = -np.sum(p * np.log2(p))
        
        # Check for NaN or Infinity
        if np.isnan(entropy) or np.isinf(entropy):
            logger.warning(f"Calculated entropy is NaN or Infinity: {entropy}. Returning sentinel.")
            return SENTINEL_VALUE
        
        return float(entropy)
    except Exception as e:
        logger.error(f"Error calculating entropy: {e}")
        return SENTINEL_VALUE

def extract_move_distribution(row: pd.Series) -> np.ndarray:
    """
    Extract move distribution from a row.
    
    Expected columns: 'legal_moves' (list of moves) and 'move_counts' (list of counts).
    If 'move_counts' is missing, assume uniform distribution.
    
    Args:
        row: A row from the metrics dataframe.
        
    Returns:
        Normalized probability distribution.
    """
    legal_moves = row.get('legal_moves')
    move_counts = row.get('move_counts')
    
    if not legal_moves:
        logger.warning(f"No legal moves found in row {row.get('trajectory_id', 'unknown')}.")
        return np.array([])
    
    if move_counts is None or len(move_counts) == 0:
        # Assume uniform distribution if counts are missing
        n = len(legal_moves)
        return np.ones(n) / n
    
    # Convert to numpy array and normalize
    counts = np.array(move_counts, dtype=float)
    total = np.sum(counts)
    
    if total == 0:
        logger.warning(f"Zero total counts for trajectory {row.get('trajectory_id', 'unknown')}.")
        return np.ones(len(counts)) / len(counts)
    
    return counts / total

def calculate_entropy_for_trajectory(row: pd.Series) -> float:
    """
    Calculate entropy for a single trajectory row.
    
    Args:
        row: A row from the metrics dataframe.
        
    Returns:
        Entropy value or SENTINEL_VALUE if invalid.
    """
    distribution = extract_move_distribution(row)
    
    if len(distribution) == 0:
        return SENTINEL_VALUE
        
    return calculate_shannon_entropy(distribution)

def process_trajectories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process the dataframe to calculate entropy for each trajectory.
    
    Args:
        df: Input dataframe with trajectory metrics.
        
    Returns:
        Dataframe with added 'entropy' column.
    """
    logger.info(f"Processing {len(df)} trajectories for entropy calculation.")
    
    entropies = []
    for idx, row in df.iterrows():
        entropy_val = calculate_entropy_for_trajectory(row)
        entropies.append(entropy_val)
        
        # Log specific edge cases
        if entropy_val == SENTINEL_VALUE:
            logger.warning(
                f"Trajectory {row.get('trajectory_id', 'unknown')} produced invalid entropy. "
                f"Triggering all-layers fallback in downstream tasks."
            )
    
    df['entropy'] = entropies
    return df

def main():
    """Main entry point for the entropy calculation task."""
    setup_logging()
    
    # Check if input file exists
    if not INPUT_FILE.exists():
        logger.error(f"Input file {INPUT_FILE} does not exist. Skipping entropy calculation.")
        # Create an empty output file to indicate the task was skipped
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w') as f:
            f.write("trajectory_id,entropy,valid\n")
        return

    try:
        # Load the metrics data
        logger.info(f"Loading metrics from {INPUT_FILE}")
        df = pd.read_csv(INPUT_FILE)
        
        if df.empty:
            logger.warning("Input dataframe is empty. No data to process.")
            OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(OUTPUT_FILE, 'w') as f:
                f.write("trajectory_id,entropy,valid\n")
            return
        
        # Validate required columns
        required_cols = ['trajectory_id']
        if 'legal_moves' not in df.columns and 'move_counts' not in df.columns:
            logger.warning("Missing 'legal_moves' or 'move_counts' columns. Assuming uniform distribution for all.")
            # Add dummy columns if missing
            if 'legal_moves' not in df.columns:
                df['legal_moves'] = [['move_a', 'move_b']] * len(df)
            if 'move_counts' not in df.columns:
                df['move_counts'] = [[1, 1]] * len(df)

        # Calculate entropy
        df = process_trajectories(df)
        
        # Add validity flag
        df['valid'] = df['entropy'] != SENTINEL_VALUE
        
        # Select output columns
        output_cols = ['trajectory_id', 'entropy', 'valid']
        # Include other relevant columns if they exist
        for col in ['turn', 'win', 'loss', 'initial_state_hash']:
            if col in df.columns:
                output_cols.append(col)
        
        output_df = df[output_cols]
        
        # Save to CSV
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        output_df.to_csv(OUTPUT_FILE, index=False)
        
        logger.info(f"Entropy calculation complete. Output saved to {OUTPUT_FILE}")
        logger.info(f"Total trajectories: {len(output_df)}, Valid: {output_df['valid'].sum()}, Invalid: {(~output_df['valid']).sum()}")
        
    except Exception as e:
        logger.critical(f"Failed to process trajectories: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
