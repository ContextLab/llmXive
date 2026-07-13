import json
import os
from typing import Any, Dict, List, Optional

from utils.constants import (
    get_coverage_vector_dimensions,
    get_semantic_proxies,
    get_coverage_schema,
)
from utils.logging import get_task_logger, log_error

logger = get_task_logger(__name__)

def initialize_coverage_vector() -> Dict[str, Any]:
    """
    Initialize a binary state coverage vector based on the schema.
    Returns a dictionary with 'vector' (list of 0s) and 'metadata'.
    """
    dims = get_coverage_vector_dimensions()
    proxies = get_semantic_proxies()
    
    vector = [0] * dims
    
    return {
        "vector": vector,
        "metadata": {
            "dimensions": dims,
            "semantic_proxies": proxies,
            "initialized_at": None,
            "source": "initialization"
        }
    }

def detect_transitions(
    rollout_data: Dict[str, Any], current_vector: List[int]
) -> List[int]:
    """
    Analyze rollout data to detect state transitions and update the vector.
    
    Args:
        rollout_data: Dictionary containing state observations from a rollout.
        current_vector: The current binary coverage vector.
        
    Returns:
        Updated binary coverage vector.
        
    Raises:
        ValueError: If rollout_data structure is invalid.
    """
    if not isinstance(rollout_data, dict):
        raise ValueError("Rollout data must be a dictionary.")
        
    new_vector = current_vector.copy()
    dims = get_coverage_vector_dimensions()
    proxies = get_semantic_proxies()
    
    # Ensure the rollout data has the expected state structure
    if "states" not in rollout_data:
        logger.warning("Rollout data missing 'states' key; no transitions detected.")
        return new_vector
        
    states = rollout_data["states"]
    if not isinstance(states, list):
        logger.warning("'states' in rollout data is not a list; skipping transition detection.")
        return new_vector
        
    # Iterate through states to detect changes in semantic proxies
    for step_idx, state in enumerate(states):
        if not isinstance(state, dict):
            continue
            
        for proxy_name in proxies:
            # Check if the proxy exists in the state
            if proxy_name in state:
                # If the state indicates the proxy is active (e.g., True, 1, or non-None),
                # set the corresponding bit in the vector to 1.
                # We map the proxy name to an index. Assuming order matches get_semantic_proxies()
                try:
                    proxy_index = proxies.index(proxy_name)
                    if proxy_index < dims:
                        # Mark as covered if the proxy is present and active
                        if state[proxy_name]:
                            new_vector[proxy_index] = 1
                except ValueError:
                    # Proxy name not in list, skip
                    continue
                    
    return new_vector

def aggregate_vectors(
    vectors: List[List[int]]
) -> List[int]:
    """
    Aggregate multiple coverage vectors into a single representative vector.
    Uses logical OR (bitwise) aggregation: if any vector has a bit set, the result is set.
    
    Args:
        vectors: List of binary coverage vectors.
        
    Returns:
        Aggregated binary coverage vector.
    """
    if not vectors:
        return []
        
    dims = len(vectors[0])
    if dims == 0:
        return []
        
    # Initialize result with zeros
    result = [0] * dims
    
    for vec in vectors:
        if len(vec) != dims:
            logger.warning(f"Vector length mismatch: expected {dims}, got {len(vec)}. Skipping.")
            continue
        for i in range(dims):
            if vec[i] == 1:
                result[i] = 1
                
    return result

def save_coverage_vector(
    vector_data: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save the coverage vector data to a JSON file.
    
    Args:
        vector_data: Dictionary containing 'vector' and 'metadata'.
        output_path: Path to save the JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(vector_data, f, indent=2)
    logger.info(f"Coverage vector saved to {output_path}")

def main():
    """
    Main entry point for state coverage module.
    Demonstrates initialization, transition detection, and aggregation.
    """
    logger.info("Starting state coverage module main.")
    
    # Initialize
    coverage_data = initialize_coverage_vector()
    logger.info(f"Initialized coverage vector: {coverage_data}")
    
    # Simulate some rollout data (in real usage, this comes from training/rollouts)
    # This is just a demo of the logic; in production, data is loaded from real sources.
    mock_rollout = {
        "states": [
            {"dark_mode": False, "unread_count": 0},
            {"dark_mode": True, "unread_count": 5},  # Transition detected
            {"dark_mode": True, "unread_count": 2}
        ]
    }
    
    try:
        updated_vector = detect_transitions(mock_rollout, coverage_data["vector"])
        logger.info(f"Updated vector after transitions: {updated_vector}")
        
        # Aggregate with another mock vector
        mock_vector_2 = [0, 1, 0, 0] # Assuming 4 dims for demo
        aggregated = aggregate_vectors([updated_vector, mock_vector_2])
        logger.info(f"Aggregated vector: {aggregated}")
        
    except Exception as e:
        log_error(logger, "Error during state coverage processing", e)
        raise

if __name__ == "__main__":
    main()
