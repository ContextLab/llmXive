import numpy as np
import pandas as pd
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import os
import sys

# Configure logging to write to the specific edge case log file
LOG_FILE = Path("data/processed/edge_case_warnings.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def setup_logging():
    """Configure logging to write warnings/errors to the specific edge case log."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE, mode='a')
        ]
    )

def calculate_shannon_entropy(probabilities: Union[np.ndarray, List[float]]) -> float:
    """
    Calculate Shannon entropy of a probability distribution.
    
    Args:
        probabilities: Array of probabilities (must sum to 1.0).
        
    Returns:
        Shannon entropy value in bits. Returns 0.0 if distribution is degenerate (all mass on one outcome).
        
    Raises:
        ValueError: If probabilities are invalid (negative, sum != 1).
    """
    probs = np.array(probabilities, dtype=float)
    
    # Validate input
    if np.any(probs < 0):
        raise ValueError("Probabilities cannot be negative.")
    
    total = np.sum(probs)
    if total == 0:
        # Degenerate case: no valid moves
        return 0.0
        
    # Normalize to ensure sum is exactly 1.0 to avoid floating point issues
    probs = probs / total
    
    # Filter out zero probabilities (log(0) is undefined)
    valid_probs = probs[probs > 0]
    
    if len(valid_probs) == 0:
        return 0.0
        
    # Calculate entropy: -sum(p * log2(p))
    entropy = -np.sum(valid_probs * np.log2(valid_probs))
    
    return float(entropy)

def extract_move_distribution(row: pd.Series) -> Dict[str, float]:
    """
    Extract the legal moves distribution from a dataframe row.
    
    The 'legal_moves' column is expected to be a string representation of a JSON object
    or a dict-like string, e.g., "{'move_a': 0.5, 'move_b': 0.5}" or a JSON string.
    Alternatively, it might be a list of moves if counts are uniform.
    
    Args:
        row: A row from the metrics dataframe.
        
    Returns:
        Dictionary mapping move identifiers to their probability/count.
    """
    raw_moves = row.get('legal_moves', '{}')
    
    if pd.isna(raw_moves) or raw_moves == '':
        return {}
        
    if isinstance(raw_moves, dict):
        return raw_moves
        
    if isinstance(raw_moves, str):
        # Try parsing as JSON first
        try:
            import json
            parsed = json.loads(raw_moves)
            if isinstance(parsed, dict):
                return parsed
            if isinstance(parsed, list):
                # If it's a list of moves, assume uniform distribution
                counts = {str(move): 1.0 for move in parsed}
                return counts
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Try parsing as Python literal (e.g., {'a': 1, 'b': 2})
        try:
            # Safe eval is risky, but for controlled data formats we can try a simple split
            # This is a fallback for malformed JSON that looks like a dict
            clean = raw_moves.strip().replace("'", '"')
            parsed = json.loads(clean)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
            
    # If we can't parse, return empty
    return {}

def calculate_entropy_for_trajectory(row: pd.Series) -> Tuple[float, str]:
    """
    Calculate entropy for a single trajectory turn.
    
    Args:
        row: A row from the metrics dataframe.
        
    Returns:
        Tuple of (entropy_value, status_string).
        If entropy is NaN or Inf, status is 'SENTINEL'.
        Otherwise, status is 'OK'.
    """
    distribution = extract_move_distribution(row)
    
    if not distribution:
        # No moves available -> entropy 0
        return 0.0, 'OK'
        
    probs = list(distribution.values())
    
    try:
        entropy = calculate_shannon_entropy(probs)
        
        if np.isnan(entropy) or np.isinf(entropy):
            return entropy, 'SENTINEL'
            
        return entropy, 'OK'
        
    except ValueError as e:
        # Log the error and return sentinel
        logging.warning(f"Invalid distribution in row {row.get('trajectory_id', 'unknown')}: {e}")
        return float('nan'), 'SENTINEL'

def process_trajectories(input_path: str, output_path: str) -> None:
    """
    Main processing function to calculate entropy for all trajectories.
    
    Args:
        input_path: Path to the input CSV (metrics_with_moves.csv).
        output_path: Path to the output CSV (entropy_metrics.csv).
    """
    setup_logging()
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        logging.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Real data missing; pipeline cannot proceed. Expected: {input_file}")
        
    logging.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file)
    
    if df.empty:
        logging.warning(f"Input file {input_file} is empty (header only). No data to process.")
        # Create output with same columns but no rows
        output_df = pd.DataFrame(columns=['trajectory_id', 'turn', 'entropy', 'status'])
        output_df.to_csv(output_file, index=False)
        return
        
    logging.info(f"Processing {len(df)} rows...")
    
    results = []
    sentinel_count = 0
    
    for idx, row in df.iterrows():
        trajectory_id = row.get('trajectory_id', 'unknown')
        turn = row.get('turn', 0)
        
        entropy, status = calculate_entropy_for_trajectory(row)
        
        if status == 'SENTINEL':
            sentinel_count += 1
            logging.warning(
                f"NaN/Inf entropy detected for trajectory {trajectory_id}, turn {turn}. "
                f"Value: {entropy}. Triggering all-layers fallback in downstream tasks."
            )
            
        results.append({
            'trajectory_id': trajectory_id,
            'turn': turn,
            'entropy': entropy,
            'status': status
        })
        
    output_df = pd.DataFrame(results)
    
    logging.info(f"Entropy calculation complete. Processed {len(output_df)} rows. "
                 f"Sentinel (NaN/Inf) count: {sentinel_count}")
                 
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    output_df.to_csv(output_file, index=False)
    logging.info(f"Results written to {output_file}")

def main():
    """Entry point for the entropy calculation task."""
    # Define paths relative to project root
    input_file = "data/processed/metrics_with_moves.csv"
    output_file = "data/processed/entropy_metrics.csv"
    
    try:
        process_trajectories(input_file, output_file)
        logging.info("T006b: Entropy calculation completed successfully.")
    except FileNotFoundError as e:
        logging.critical(f"T006b: Pipeline blocked due to missing data. {e}")
        raise
    except Exception as e:
        logging.error(f"T006b: Unexpected error during entropy calculation: {e}")
        raise

if __name__ == "__main__":
    main()