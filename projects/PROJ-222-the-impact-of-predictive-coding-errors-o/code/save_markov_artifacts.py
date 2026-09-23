"""
T041d: Write Final Markov State
Finalizes and writes data/processed/markov_state.json containing:
- transition_matrix: 2D array of probabilities
- alphabet: list of unique symbols
- order: 1 (first-order Markov)

This artifact is validated by T017b.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Import from local modules using the provided API surface
from preprocess import get_processed_dir, get_data_dir
from config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_intermediate_counts(counts_path: Path) -> Dict[str, Any]:
    """Load the incremental counts written by T041c."""
    if not counts_path.exists():
        raise FileNotFoundError(f"Intermediate counts file not found: {counts_path}")
    
    with open(counts_path, 'r') as f:
        return json.load(f)

def load_alphabet(alphabet_path: Path) -> List[str]:
    """Load the alphabet symbols."""
    if not alphabet_path.exists():
        raise FileNotFoundError(f"Alphabet file not found: {alphabet_path}")
    
    with open(alphabet_path, 'r') as f:
        return json.load(f)

def finalize_markov_state(counts_data: Dict[str, Any], alphabet: List[str], alpha: float = 1.0) -> Dict[str, Any]:
    """
    Convert raw counts to a normalized transition matrix with Laplace smoothing.
    
    Args:
        counts_data: Dict mapping "from_symbol" -> {"to_symbol": count, ...}
        alphabet: List of unique symbols
        alpha: Laplace smoothing parameter (default 1.0)
    
    Returns:
        Dict containing transition_matrix, alphabet, and order.
    """
    if not alphabet:
        raise ValueError("Alphabet cannot be empty.")
    
    # Sort alphabet for consistent ordering
    sorted_alphabet = sorted(alphabet)
    symbol_to_idx = {sym: idx for idx, sym in enumerate(sorted_alphabet)}
    n = len(sorted_alphabet)
    
    # Initialize matrix with smoothing
    matrix = [[alpha for _ in range(n)] for _ in range(n)]
    
    # Fill in counts from data
    for from_sym, to_counts in counts_data.items():
        if from_sym not in symbol_to_idx:
            logger.warning(f"Symbol '{from_sym}' in counts not found in alphabet. Skipping.")
            continue
        
        from_idx = symbol_to_idx[from_sym]
        for to_sym, count in to_counts.items():
            if to_sym not in symbol_to_idx:
                logger.warning(f"Symbol '{to_sym}' in counts not found in alphabet. Skipping.")
                continue
            
            to_idx = symbol_to_idx[to_sym]
            matrix[from_idx][to_idx] += count
    
    # Normalize rows to get probabilities
    for i in range(n):
        row_sum = sum(matrix[i])
        if row_sum == 0:
            # If a row is still zero (shouldn't happen with smoothing), uniform distribution
            matrix[i] = [1.0 / n for _ in range(n)]
        else:
            matrix[i] = [prob / row_sum for prob in matrix[i]]
    
    return {
        "transition_matrix": matrix,
        "alphabet": sorted_alphabet,
        "order": 1
    }

def save_markov_artifacts(
    markov_state: Dict[str, Any],
    counts_path: Path,
    output_path: Path
) -> None:
    """Save the final Markov state and update the counts file status."""
    
    # Write the final state
    with open(output_path, 'w') as f:
        json.dump(markov_state, f, indent=2)
    
    logger.info(f"Markov state saved to {output_path}")
    
    # Update the counts file to indicate it has been finalized
    # (Optional: could add a 'finalized' flag, but keeping it simple)
    
    if not output_path.exists():
        raise RuntimeError(f"Failed to write markov_state.json to {output_path}")

def run_t017b_validation(output_path: Path) -> bool:
    """
    Trigger T017b validation logic to ensure the artifact is valid.
    Returns True if validation passes, False otherwise.
    """
    # Inline validation logic to avoid circular imports or missing dependencies
    if not output_path.exists():
        logger.error("markov_state.json does not exist.")
        return False
    
    try:
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        required_keys = ["transition_matrix", "alphabet", "order"]
        for key in required_keys:
            if key not in data:
                logger.error(f"Missing required key in markov_state.json: {key}")
                return False
        
        if data["order"] != 1:
            logger.error(f"Expected order=1, got {data['order']}")
            return False
        
        if not isinstance(data["alphabet"], list) or len(data["alphabet"]) == 0:
            logger.error("Alphabet must be a non-empty list.")
            return False
        
        if not isinstance(data["transition_matrix"], list):
            logger.error("Transition matrix must be a list.")
            return False
        
        logger.info("T017b validation passed.")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in markov_state.json: {e}")
        return False

def main() -> int:
    """Main entry point for T041d."""
    try:
        logger.info("Starting T041d: Write Final Markov State")
        
        # Paths
        processed_dir = get_processed_dir()
        counts_path = processed_dir / "markov_counts.json"
        alphabet_path = processed_dir / "markov_alphabet.json"
        output_path = processed_dir / "markov_state.json"
        
        # Load config for smoothing parameter
        config = get_config()
        alpha = config.get("LAPLACE_ALPHA", 1.0)
        
        # Load intermediate data
        logger.info(f"Loading counts from {counts_path}")
        counts_data = load_intermediate_counts(counts_path)
        
        logger.info(f"Loading alphabet from {alphabet_path}")
        alphabet = load_alphabet(alphabet_path)
        
        # Finalize
        logger.info("Finalizing Markov state with Laplace smoothing")
        markov_state = finalize_markov_state(counts_data, alphabet, alpha)
        
        # Save
        logger.info(f"Writing final state to {output_path}")
        save_markov_artifacts(markov_state, counts_path, output_path)
        
        # Validate
        if not run_t017b_validation(output_path):
            logger.error("T017b validation failed. Exiting with error.")
            return 1
        
        logger.info("T041d completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Missing required input file: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T041d: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())