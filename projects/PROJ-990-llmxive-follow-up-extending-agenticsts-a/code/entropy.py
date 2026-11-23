"""
Entropy calculation module for AgenticSTS trajectories.

This module calculates Shannon entropy of legal move distributions extracted
from trajectory logs. It handles edge cases (NaN, Infinity) by logging warnings
and returning sentinel values as specified in T006b.
"""
import numpy as np
import pandas as pd
import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "metrics_with_moves.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "entropy_metrics.csv"
WARNING_LOG_PATH = PROJECT_ROOT / "data" / "processed" / "edge_case_warnings.log"

def setup_logging():
    """Setup logging configuration for entropy calculations."""
    logger.setLevel(logging.INFO)
    # Ensure warning log directory exists
    WARNING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

def calculate_shannon_entropy(probabilities: np.ndarray) -> float:
    """
    Calculate Shannon entropy of a probability distribution.

    Args:
        probabilities: Array of probabilities (must sum to 1).

    Returns:
        Shannon entropy value in bits. Returns float('nan') if invalid.
    """
    # Filter out zero probabilities to avoid log(0)
    p = probabilities[probabilities > 0]
    if len(p) == 0:
        return float('nan')
    
    try:
        entropy = -np.sum(p * np.log2(p))
        # Check for NaN or Infinity
        if np.isnan(entropy) or np.isinf(entropy):
            return float('nan')
        return float(entropy)
    except Exception as e:
        logger.warning(f"Entropy calculation failed: {e}")
        return float('nan')

def extract_move_distribution(row: pd.Series) -> np.ndarray:
    """
    Extract legal move distribution from a trajectory row.

    Args:
        row: DataFrame row containing move distribution data.

    Returns:
        Array of probabilities for each legal move.
    """
    # Expected columns based on T006a output: move_distribution or similar
    # The input CSV from T006a should have a column with move probabilities
    # If the column is JSON string, parse it; if it's a list/array, use directly
    if 'move_distribution' in row.index:
        dist = row['move_distribution']
        if isinstance(dist, str):
            try:
                dist = json.loads(dist)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse move_distribution for trajectory {row.get('trajectory_id', 'unknown')}")
                return np.array([])
        elif isinstance(dist, (list, tuple)):
            dist = list(dist)
        else:
            # Try to convert to list if it's a numpy array or similar
            dist = list(dist) if hasattr(dist, '__iter__') else []
        
        if len(dist) == 0:
            return np.array([])
        
        # Normalize to ensure it's a valid probability distribution
        total = sum(dist)
        if total > 0:
            return np.array([p / total for p in dist])
        else:
            return np.array([1.0 / len(dist)] * len(dist)) if len(dist) > 0 else np.array([])
    
    # Fallback: if no move_distribution column, try to reconstruct from move counts
    # This assumes columns like move_0, move_1, etc. exist
    move_cols = [col for col in row.index if str(col).startswith('move_')]
    if move_cols:
        counts = [row[col] for col in move_cols]
        total = sum(counts)
        if total > 0:
            return np.array([c / total for c in counts])
        else:
            return np.array([1.0 / len(counts)] * len(counts))
    
    logger.warning(f"No move distribution found for trajectory {row.get('trajectory_id', 'unknown')}")
    return np.array([])

def calculate_entropy_for_trajectory(row: pd.Series) -> float:
    """
    Calculate entropy for a single trajectory's move distribution.

    Args:
        row: DataFrame row with move distribution data.

    Returns:
        Shannon entropy value, or float('nan') if invalid.
    """
    distribution = extract_move_distribution(row)
    if len(distribution) == 0:
        return float('nan')
    
    entropy = calculate_shannon_entropy(distribution)
    return entropy

def process_trajectories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process all trajectories and calculate entropy metrics.

    Args:
        df: DataFrame with trajectory data including move distributions.

    Returns:
        DataFrame with added entropy column.
    """
    logger.info(f"Processing {len(df)} trajectories for entropy calculation...")
    
    entropy_values = []
    nan_count = 0
    inf_count = 0
    
    for idx, row in df.iterrows():
        entropy = calculate_entropy_for_trajectory(row)
        entropy_values.append(entropy)
        
        # Log edge cases
        if np.isnan(entropy):
            nan_count += 1
            warning_msg = f"NaN entropy for trajectory {row.get('trajectory_id', 'unknown')} at turn {row.get('turn', 'unknown')}"
            logger.warning(warning_msg)
            write_warning_log(warning_msg)
        elif np.isinf(entropy):
            inf_count += 1
            warning_msg = f"Inf entropy for trajectory {row.get('trajectory_id', 'unknown')} at turn {row.get('turn', 'unknown')}"
            logger.warning(warning_msg)
            write_warning_log(warning_msg)
    
    # Add entropy column to DataFrame
    df['entropy'] = entropy_values
    
    logger.info(f"Entropy calculation complete. NaN cases: {nan_count}, Inf cases: {inf_count}")
    return df

def write_warning_log(message: str):
    """
    Write a warning message to the edge case warnings log.

    Args:
        message: Warning message to log.
    """
    try:
        with open(WARNING_LOG_PATH, 'a') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp} - WARNING - {message}\n")
    except Exception as e:
        logger.error(f"Failed to write to warning log: {e}")

def load_input_data() -> pd.DataFrame:
    """
    Load input data from the metrics CSV.

    Returns:
        DataFrame with trajectory metrics.
    
    Raises:
        FileNotFoundError: If input file doesn't exist.
    """
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Ensure T006a has been executed successfully to generate metrics_with_moves.csv."
        )
    
    logger.info(f"Loading input data from {INPUT_PATH}")
    df = pd.read_csv(INPUT_PATH)
    logger.info(f"Loaded {len(df)} rows from input file")
    return df

def save_output_data(df: pd.DataFrame):
    """
    Save processed data with entropy calculations to output file.

    Args:
        df: DataFrame with entropy column added.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Saved entropy metrics to {OUTPUT_PATH}")

def main():
    """
    Main entry point for entropy calculation task.
    
    Reads metrics_with_moves.csv, calculates Shannon entropy for each trajectory's
    move distribution, handles edge cases (NaN/Inf), and writes entropy_metrics.csv.
    """
    setup_logging()
    
    try:
        # Load input data
        df = load_input_data()
        
        # Process trajectories and calculate entropy
        df_with_entropy = process_trajectories(df)
        
        # Save output
        save_output_data(df_with_entropy)
        
        logger.info("Entropy calculation task completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input data error: {e}")
        # Re-raise to fail loudly as per constraints
        raise
    except Exception as e:
        logger.error(f"Unexpected error during entropy calculation: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
