"""
State Coverage Instrumentation for MobileGym.

This module handles the detection of state transitions, aggregation of
coverage vectors from parallel rollouts, and writing of aggregated data.
"""
import json
import os
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from code.utils.constants import is_valid_coverage_vector, calculate_coverage_ratio
from code.utils.logging import get_logger, configure_logging

# Configure logging
configure_logging()
logger = get_logger(__name__)


def initialize_coverage_vector(num_variables: int) -> List[int]:
    """
    Initialize a binary coverage vector with all zeros.
    
    Args:
        num_variables: The number of state variables to track
    
    Returns:
        A list of 0s with length num_variables
    """
    return [0] * num_variables


def detect_state_transitions(rollout: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract state transitions from a rollout JSON.
    
    Args:
        rollout: A dictionary representing a single rollout with 'transitions' key
    
    Returns:
        A list of transition dictionaries
    """
    if not isinstance(rollout, dict):
        logger.warning(f"Invalid rollout format: {type(rollout)}")
        return []
    
    transitions = rollout.get("transitions", [])
    if not isinstance(transitions, list):
        logger.warning(f"Invalid transitions format in rollout: {rollout.get('rollout_id', 'unknown')}")
        return []
    
    return transitions


def aggregate_coverage_vectors(vectors: List[List[int]]) -> List[int]:
    """
    Aggregate multiple coverage vectors into a single vector using bitwise OR.
    
    Args:
        vectors: A list of binary coverage vectors
    
    Returns:
        A single aggregated coverage vector
    """
    if not vectors:
        return []
    
    num_variables = len(vectors[0])
    if num_variables == 0:
        return []
    
    # Verify all vectors have the same length
    for i, vec in enumerate(vectors):
        if len(vec) != num_variables:
            logger.error(f"Vector length mismatch at index {i}: expected {num_variables}, got {len(vec)}")
            raise ValueError(f"Vector length mismatch at index {i}")
    
    # Aggregate using bitwise OR
    aggregated = [0] * num_variables
    for vec in vectors:
        for i in range(num_variables):
            aggregated[i] = aggregated[i] | vec[i]
    
    return aggregated


def merge_coverage_vectors_threadsafe(shared_vector: List[int], local_vector: List[int]) -> None:
    """
    Thread-safe merge of a local vector into a shared vector.
    
    This function assumes the caller holds the appropriate lock.
    
    Args:
        shared_vector: The shared coverage vector to update (modified in place)
        local_vector: The local vector to merge
    """
    if len(shared_vector) != len(local_vector):
        raise ValueError(f"Vector length mismatch: {len(shared_vector)} vs {len(local_vector)}")
    
    for i in range(len(shared_vector)):
        shared_vector[i] = shared_vector[i] | local_vector[i]


def process_rollout_batch(rollouts: List[Dict[str, Any]], num_variables: int) -> List[int]:
    """
    Process a batch of rollouts and aggregate their coverage vectors.
    
    Args:
        rollouts: A list of rollout dictionaries
        num_variables: The number of state variables to track
    
    Returns:
        An aggregated coverage vector
    """
    vectors = []
    for rollout in rollouts:
        try:
            transitions = detect_state_transitions(rollout)
            vector = _transitions_to_vector(transitions, num_variables)
            vectors.append(vector)
        except Exception as e:
            logger.error(f"Error processing rollout {rollout.get('rollout_id', 'unknown')}: {e}")
            continue
    
    if not vectors:
        return initialize_coverage_vector(num_variables)
    
    return aggregate_coverage_vectors(vectors)


def _transitions_to_vector(transitions: List[Dict[str, Any]], num_variables: int) -> List[int]:
    """
    Convert a list of transitions to a binary coverage vector.
    
    Args:
        transitions: List of transition dictionaries
        num_variables: Total number of state variables
    
    Returns:
        A binary coverage vector
    """
    vector = initialize_coverage_vector(num_variables)
    
    for transition in transitions:
        var_name = transition.get("state_var", "")
        try:
            # Extract index from variable name (e.g., "state_var_5" -> 5)
            idx = int(var_name.split("_")[-1])
            if 0 <= idx < num_variables:
                vector[idx] = 1
        except (ValueError, IndexError, KeyError):
            logger.warning(f"Invalid transition format: {transition}")
            continue
    
    return vector


def process_rollouts_parallel(
    rollouts: List[Dict[str, Any]],
    num_variables: int,
    max_workers: int = 8
) -> List[int]:
    """
    Process rollouts in parallel and aggregate coverage vectors.
    
    This function distributes rollouts across multiple threads to improve
    throughput for large batches, then aggregates the results.
    
    Args:
        rollouts: A list of rollout dictionaries
        num_variables: The number of state variables to track
        max_workers: Maximum number of worker threads
    
    Returns:
        An aggregated coverage vector
    """
    if not rollouts:
        return initialize_coverage_vector(num_variables)
    
    shared_vector = initialize_coverage_vector(num_variables)
    lock = threading.Lock()
    
    def process_chunk(chunk_rollouts: List[Dict[str, Any]]) -> List[int]:
        """Process a chunk of rollouts and return a local vector."""
        local_vector = initialize_coverage_vector(num_variables)
        
        for rollout in chunk_rollouts:
            try:
                transitions = detect_state_transitions(rollout)
                vector = _transitions_to_vector(transitions, num_variables)
                
                # Merge into local vector
                for i in range(num_variables):
                    local_vector[i] = local_vector[i] | vector[i]
            except Exception as e:
                logger.error(f"Error processing rollout in chunk: {e}")
                continue
        
        return local_vector
    
    # Split rollouts into chunks
    chunk_size = max(1, len(rollouts) // max_workers)
    chunks = [rollouts[i:i + chunk_size] for i in range(0, len(rollouts), chunk_size)]
    
    # Process chunks in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
        
        for future in as_completed(futures):
            try:
                local_vector = future.result()
                
                # Thread-safe merge into shared vector
                with lock:
                    merge_coverage_vectors_threadsafe(shared_vector, local_vector)
            except Exception as e:
                logger.error(f"Error in parallel processing: {e}")
                continue
    
    return shared_vector


def main():
    """
    Main entry point for testing the state coverage instrumentation.
    
    This function generates mock rollouts, processes them in parallel,
    and outputs the aggregated coverage vector.
    """
    logger.info("Starting state coverage instrumentation test")
    
    # Generate mock rollouts
    num_rollouts = 100
    num_variables = 50
    rollouts = []
    
    for i in range(num_rollouts):
        rollout = {
            "rollout_id": f"rollout_{i}",
            "transitions": [
                {
                    "state_var": f"state_var_{(i * 3 + j) % num_variables}",
                    "new_value": 1,
                    "timestamp": time.time()
                }
                for j in range(4)
            ]
        }
        rollouts.append(rollout)
    
    # Process in parallel
    start_time = time.time()
    aggregated_vector = process_rollouts_parallel(rollouts, num_variables, max_workers=8)
    end_time = time.time()
    
    # Calculate coverage ratio
    coverage_ratio = calculate_coverage_ratio(aggregated_vector)
    
    logger.info(f"Processed {num_rollouts} rollouts in {end_time - start_time:.2f} seconds")
    logger.info(f"Final coverage vector: {aggregated_vector}")
    logger.info(f"Coverage ratio: {coverage_ratio:.2%}")
    
    # Write results to file
    output_path = Path("data/processed/coverage_vectors.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "num_rollouts": num_rollouts,
        "num_variables": num_variables,
        "coverage_vector": aggregated_vector,
        "coverage_ratio": coverage_ratio,
        "processing_time_seconds": end_time - start_time
    }
    
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results written to {output_path}")


if __name__ == "__main__":
    import time
    from datetime import datetime, timezone
    main()
