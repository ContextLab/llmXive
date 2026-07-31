"""
Entropy calculation module for AgenticSTS trajectories.

Calculates Shannon entropy of legal move distributions extracted by the parser.
Handles edge cases (NaN, Inf) by logging warnings and returning sentinel values.
"""

import numpy as np
import pandas as pd
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import sys

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
SENTINEL_VALUE = -1.0  # Sentinel for NaN/Inf cases to trigger "all-layers" fallback

def setup_logging():
    """Ensure logging is configured for the module."""
    pass  # Already configured in module init

def calculate_shannon_entropy(probabilities: np.ndarray) -> float:
    """
    Calculate Shannon entropy from a probability distribution.

    Args:
        probabilities: Array of probabilities (should sum to 1).

    Returns:
        Shannon entropy in bits. Returns -1.0 if distribution is invalid or results in NaN/Inf.
    """
    # Filter out zero probabilities to avoid log(0)
    p = probabilities[probabilities > 0]

    if len(p) == 0:
        logger.warning("Empty probability distribution encountered.")
        return SENTINEL_VALUE

    entropy = -np.sum(p * np.log2(p))

    if np.isnan(entropy) or np.isinf(entropy):
        logger.warning(f"Calculated entropy is NaN or Inf: {entropy}. Returning sentinel.")
        return SENTINEL_VALUE

    return float(entropy)

def extract_move_distribution(legal_moves_str: str) -> np.ndarray:
    """
    Extract probability distribution from a string representation of legal moves.

    Expected format: "move1:0.2,move2:0.5,move3:0.3" or similar JSON-like structure.
    If the string is a JSON list of counts, it will be normalized.

    Args:
        legal_moves_str: String representation of move distribution.

    Returns:
        Numpy array of probabilities.
    """
    try:
        # Try parsing as JSON first (list of counts or dict)
        data = json.loads(legal_moves_str)

        if isinstance(data, dict):
            # Extract values and normalize
            counts = np.array(list(data.values()), dtype=float)
        elif isinstance(data, list):
            counts = np.array(data, dtype=float)
        else:
            raise ValueError("Unexpected JSON structure")

        total = np.sum(counts)
        if total == 0:
            return np.zeros_like(counts)
        return counts / total

    except (json.JSONDecodeError, ValueError):
        # Fallback: try parsing as "key:value,key:value" format
        try:
            parts = legal_moves_str.split(',')
            counts = []
            for part in parts:
                if ':' in part:
                    _, val = part.split(':')
                    counts.append(float(val))
            if not counts:
                return np.array([])
            total = sum(counts)
            if total == 0:
                return np.zeros(len(counts))
            return np.array([c/total for c in counts])
        except Exception:
            logger.warning(f"Could not parse move distribution: {legal_moves_str}")
            return np.array([])

def calculate_entropy_for_trajectory(row: pd.Series) -> float:
    """
    Calculate entropy for a single trajectory row.

    Args:
        row: DataFrame row containing 'legal_moves' column.

    Returns:
        Calculated entropy or SENTINEL_VALUE if invalid.
    """
    legal_moves_str = row.get('legal_moves', '')
    if not legal_moves_str or pd.isna(legal_moves_str):
        logger.warning(f"Missing legal_moves for trajectory {row.get('trajectory_id', 'unknown')}")
        return SENTINEL_VALUE

    distribution = extract_move_distribution(str(legal_moves_str))
    if len(distribution) == 0:
        return SENTINEL_VALUE

    return calculate_shannon_entropy(distribution)

def process_trajectories(input_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Process all trajectories from input CSV and calculate entropy metrics.

    Args:
        input_path: Path to input metrics_with_moves.csv.
        output_path: Path to write entropy_metrics.csv.

    Returns:
        DataFrame with entropy metrics.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    if df.empty:
        logger.error("Input DataFrame is empty. Cannot calculate entropy.")
        # Create output with headers only to satisfy schema, but log the issue
        output_df = pd.DataFrame(columns=['trajectory_id', 'turn', 'entropy', 'is_valid'])
        output_df.to_csv(output_path, index=False)
        return output_df

    logger.info(f"Processing {len(df)} rows for entropy calculation")

    # Calculate entropy for each row
    df['entropy'] = df.apply(calculate_entropy_for_trajectory, axis=1)

    # Mark validity
    df['is_valid'] = df['entropy'] != SENTINEL_VALUE

    # Count valid/invalid
    valid_count = df['is_valid'].sum()
    invalid_count = len(df) - valid_count
    logger.info(f"Entropy calculation complete: {valid_count} valid, {invalid_count} invalid (sentinel)")

    # Select output columns
    output_cols = ['trajectory_id', 'turn', 'entropy', 'is_valid']
    # Ensure all required columns exist, fill missing with NaN if necessary
    for col in output_cols:
        if col not in df.columns:
            df[col] = np.nan

    output_df = df[output_cols].copy()

    # Write to output file
    output_df.to_csv(output_path, index=False)
    logger.info(f"Entropy metrics written to {output_path}")

    return output_df

def main():
    """Main entry point for entropy calculation task."""
    logger.info("Starting entropy calculation (T006b)")

    # Check for input file existence
    if not INPUT_FILE.exists():
        logger.warning(f"Input file {INPUT_FILE} does not exist. Skipping T006b.")
        logger.info("Skipping T006b as per skip condition: input file missing.")
        return

    try:
        process_trajectories(INPUT_FILE, OUTPUT_FILE)
        logger.info("T006b completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Critical error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during entropy calculation: {e}")
        raise

if __name__ == "__main__":
    main()
