"""
Entropy module for calculating Shannon entropy of legal move distributions.
Handles edge cases (NaN, Inf) by returning a sentinel value and logging warnings.
"""
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import json

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sentinel value for edge cases (NaN/Inf) to trigger full "all-layers" retrieval
ENTROPY_SENTINEL = -999.0

def calculate_shannon_entropy(probabilities: Union[np.ndarray, List[float]]) -> float:
    """
    Calculate Shannon entropy of a probability distribution.

    Args:
        probabilities: Array or list of probabilities (must sum to 1).

    Returns:
        Shannon entropy value. Returns ENTROPY_SENTINEL if calculation results in NaN or Inf.
    """
    if not probabilities or len(probabilities) == 0:
        logger.warning("Empty probability distribution provided. Returning sentinel value.")
        return ENTROPY_SENTINEL

    probs = np.array(probabilities, dtype=float)

    # Filter out zeros to avoid log(0)
    probs = probs[probs > 0]

    if len(probs) == 0:
        logger.warning("No positive probabilities found. Returning sentinel value.")
        return ENTROPY_SENTINEL

    # Normalize just in case
    probs = probs / np.sum(probs)

    try:
        entropy = -np.sum(probs * np.log2(probs))
    except (ValueError, RuntimeWarning) as e:
        logger.warning(f"Error during entropy calculation: {e}. Returning sentinel value.")
        return ENTROPY_SENTINEL

    # Check for NaN or Inf
    if np.isnan(entropy) or np.isinf(entropy):
        logger.warning(f"Calculated entropy is NaN or Inf. Returning sentinel value. Input: {probabilities}")
        return ENTROPY_SENTINEL

    return float(entropy)

def extract_move_distribution(turn_data: Dict) -> List[float]:
    """
    Extract the probability distribution of legal moves from turn data.

    Args:
        turn_data: Dictionary containing turn information, including legal moves and their probabilities.

    Returns:
        List of probabilities for each legal move.
    """
    if 'legal_moves' not in turn_data or 'move_probabilities' not in turn_data:
        logger.warning(f"Turn data missing 'legal_moves' or 'move_probabilities'. Data: {turn_data}")
        return []

    moves = turn_data['legal_moves']
    probs = turn_data['move_probabilities']

    if len(moves) != len(probs):
        logger.warning(f"Mismatch between number of moves ({len(moves)}) and probabilities ({len(probs)}).")
        return []

    return probs

def calculate_entropy_for_trajectory(turns: List[Dict]) -> List[Tuple[int, float, bool]]:
    """
    Calculate entropy for each turn in a trajectory.

    Args:
        turns: List of turn dictionaries.

    Returns:
        List of tuples: (turn_index, entropy_value, is_edge_case).
        is_edge_case is True if entropy is the sentinel value.
    """
    results = []
    for idx, turn in enumerate(turns):
        probs = extract_move_distribution(turn)
        entropy = calculate_shannon_entropy(probs)
        is_edge_case = (entropy == ENTROPY_SENTINEL)

        if is_edge_case:
            logger.warning(f"Turn {idx} in trajectory triggered edge case handling (NaN/Inf). "
                           f"Sentinel value {ENTROPY_SENTINEL} returned. This will trigger full 'all-layers' retrieval.")

        results.append((idx, entropy, is_edge_case))

    return results

def process_trajectories(input_path: Union[str, Path]) -> pd.DataFrame:
    """
    Process a CSV file of trajectories to calculate entropy for each turn.

    Args:
        input_path: Path to the input CSV file (data/raw/trajectories.csv).

    Returns:
        DataFrame with trajectory_id, turn_index, entropy, and is_edge_case columns.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading trajectories from {input_path}")
    df = pd.read_csv(input_path)

    if 'trajectory_id' not in df.columns or 'turn_data' not in df.columns:
        raise ValueError("Input CSV must contain 'trajectory_id' and 'turn_data' columns.")

    results = []

    for _, row in df.iterrows():
        traj_id = row['trajectory_id']
        try:
            # Assuming turn_data is a JSON string or a dict
            if isinstance(row['turn_data'], str):
                turns = json.loads(row['turn_data'])
            else:
                turns = row['turn_data']

            if not isinstance(turns, list):
                logger.warning(f"Trajectory {traj_id} has invalid turn_data format. Skipping.")
                continue

            turn_entropy_results = calculate_entropy_for_trajectory(turns)
            for turn_idx, entropy, is_edge in turn_entropy_results:
                results.append({
                    'trajectory_id': traj_id,
                    'turn_index': turn_idx,
                    'entropy': entropy,
                    'is_edge_case': is_edge
                })
        except Exception as e:
            logger.error(f"Error processing trajectory {traj_id}: {e}")
            continue

    if not results:
        logger.warning("No valid entropy results were generated.")
        return pd.DataFrame(columns=['trajectory_id', 'turn_index', 'entropy', 'is_edge_case'])

    return pd.DataFrame(results)

def main():
    """
    Main entry point for the entropy calculation script.
    Reads data/raw/trajectories.csv and outputs data/processed/entropy_results.csv.
    """
    input_file = Path("data/raw/trajectories.csv")
    output_file = Path("data/processed/entropy_results.csv")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        result_df = process_trajectories(input_file)
        result_df.to_csv(output_file, index=False)
        logger.info(f"Entropy calculation complete. Results saved to {output_file}")
        print(f"Processed {len(result_df)} turns. Edge cases: {result_df['is_edge_case'].sum()}")
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during processing: {e}")
        raise

if __name__ == "__main__":
    main()
