import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import json
import os

# Configure logging to file for edge case warnings as per T005 requirement
LOG_FILE_PATH = Path("data/processed/edge_case_warnings.log")

def setup_logging():
    """Ensure the log directory exists and configure file logging."""
    LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing handlers to avoid duplicates in repeated runs
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE_PATH, mode='w'),
            logging.StreamHandler()
        ]
    )

def calculate_shannon_entropy(move_counts: Dict[str, int]) -> float:
    """
    Calculate Shannon entropy H = -sum(p_i * log(p_i)).
    
    Args:
        move_counts: Dictionary mapping move identifiers to their counts/frequencies.
                    
    Returns:
        Shannon entropy value. Returns float('inf') if calculation results in NaN/Inf
        (e.g., empty moves or log(0) issues).
    """
    if not move_counts:
        return float('inf')
    
    total = sum(move_counts.values())
    if total == 0:
        return float('inf')
    
    entropy = 0.0
    for count in move_counts.values():
        if count > 0:
            p = count / total
            # Log of probability. If p is 0, term is 0. 
            # If p is 1, log(1)=0.
            try:
                term = p * np.log(p)
                if np.isnan(term) or np.isinf(term):
                    return float('inf')
                entropy -= term
            except (ValueError, ZeroDivisionError):
                return float('inf')
    
    # Final check for NaN/Inf
    if np.isnan(entropy) or np.isinf(entropy):
        return float('inf')
        
    return entropy

def extract_move_distribution(legal_moves: List[str]) -> Dict[str, int]:
    """
    Reconstruct the probability distribution from a list of legal moves.
    Assuming uniform distribution over the available legal moves for a specific turn.
    
    Args:
        legal_moves: List of legal move strings.
        
    Returns:
        Dictionary with move as key and count as value (uniform count=1 for each).
    """
    if not legal_moves:
        return {}
    # Uniform distribution: each available move has probability 1/|moves|
    # For entropy calculation, we just need the counts to derive probabilities.
    return {move: 1 for move in legal_moves}

def calculate_entropy_for_trajectory(trajectory_id: str, turn: int, legal_moves: List[str]) -> float:
    """
    Calculate entropy for a single trajectory turn.
    
    Args:
        trajectory_id: ID of the trajectory.
        turn: Turn number.
        legal_moves: List of legal moves at this turn.
        
    Returns:
        Calculated entropy or float('inf') for edge cases.
    """
    distribution = extract_move_distribution(legal_moves)
    entropy = calculate_shannon_entropy(distribution)
    
    if entropy == float('inf'):
        logging.warning(
            f"Warning: NaN/Inf entropy detected at trajectory {trajectory_id}, turn {turn}"
        )
        
    return entropy

def process_trajectories(input_path: Union[str, Path]) -> pd.DataFrame:
    """
    Process the metrics CSV from T006, calculate entropy, and update the DataFrame.
    If entropy is NaN/Inf, log warning to file and keep sentinel.
    
    Args:
        input_path: Path to data/processed/metrics_with_moves.csv
        
    Returns:
        DataFrame with 'move_entropy' column populated.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Setup logging to file
    setup_logging()
    
    df = pd.read_csv(input_path)
    
    # Ensure we have the necessary columns
    required_cols = ['trajectory_id', 'turn', 'legal_moves']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Input CSV missing required columns: {missing_cols}")
    
    entropy_values = []
    
    for _, row in df.iterrows():
        traj_id = str(row['trajectory_id'])
        turn = int(row['turn'])
        
        # Parse legal_moves if it's a string representation of a list
        legal_moves = row['legal_moves']
        if isinstance(legal_moves, str):
            try:
                legal_moves = json.loads(legal_moves)
            except json.JSONDecodeError:
                # Fallback if string format is not JSON list
                legal_moves = []
        
        if not isinstance(legal_moves, list):
            legal_moves = []
        
        ent = calculate_entropy_for_trajectory(traj_id, turn, legal_moves)
        entropy_values.append(ent)
    
    df['move_entropy'] = entropy_values
    
    return df

def main():
    """
    Main entry point for T005.
    Reads data/processed/metrics_with_moves.csv, calculates entropy,
    writes warnings to data/processed/edge_case_warnings.log,
    and outputs the updated CSV.
    """
    input_file = Path("data/processed/metrics_with_moves.csv")
    output_file = Path("data/processed/metrics_with_moves.csv") # Overwrite or update? Task says input, usually implies update or new file. 
    # T005 says "Input: ... Output: ...". T006 output is metrics_with_moves.csv. 
    # T005 calculates entropy of legal move distributions extracted by T006.
    # The task description for T005 doesn't explicitly name a NEW output file path, 
    # but implies updating the existing one or creating a derived one. 
    # Given T006 produces metrics_with_moves.csv, and T005 adds move_entropy, 
    # we will overwrite/update the file to include the new column, 
    # or strictly follow T005 if it implies a new file. 
    # Re-reading T005: "Input: data/processed/metrics_with_moves.csv". 
    # It doesn't specify a new output path in the text, but T006's output is the input.
    # However, T005's purpose is to calculate entropy. 
    # Let's assume we update the same file or write to a new one if specified.
    # Looking at T006: Output is metrics_with_moves.csv.
    # Looking at T005: "Input: data/processed/metrics_with_moves.csv".
    # It does not specify a new output file name. 
    # However, the task says "Implement code/entropy.py to calculate...".
    # To be safe and avoid overwriting T006's work if T005 is run independently,
    # we will write to the SAME file (updating it) as it is the logical extension,
    # OR we can write to a new file if the task implies a new artifact.
    # The task description for T005 does NOT list a new output file path.
    # It says "Input: ...".
    # Let's assume the output is the updated CSV with the entropy column.
    # Wait, T005 says "Skip Condition: If data/processed/metrics_with_moves.csv does not exist... skip".
    # This implies it expects the file to exist.
    # We will write the result back to the same file path to ensure downstream tasks (like T014a) see the entropy.
    
    if not input_file.exists():
        logging.info(f"Input file {input_file} not found. Skipping T005.")
        return

    try:
        df = process_trajectories(input_file)
        # Ensure directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        logging.info(f"Successfully calculated entropy and saved to {output_file}")
    except Exception as e:
        logging.error(f"Error processing trajectories: {e}")
        raise

if __name__ == "__main__":
    main()