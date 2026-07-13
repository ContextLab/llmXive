"""
Task T029: Generate the 'held-out test set' containing state variables NOT present
in the training-time State Coverage Vector to satisfy FR-005 transfer evaluation requirements.

This script reads the semantic proxies defined in the coverage schema (the full universe
of potential state variables). It then loads the aggregated coverage vectors from
data/processed/coverage_vectors.json. It identifies which variables were actually
observed (non-zero count) in the training data.

The output is a JSON file listing the 'held-out' variables (those in the schema but
not observed in the training vectors), which serves as the test set for transfer evaluation.
"""
import json
import os
import sys
from typing import List, Dict, Any, Set

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.constants import get_semantic_proxies
from utils.logging import get_task_logger

logger = get_task_logger(__name__)

COVERAGE_FILE = "data/processed/coverage_vectors.json"
OUTPUT_FILE = "data/processed/transfer_test_set.json"

def load_aggregated_vectors(filepath: str) -> List[Dict[str, Any]]:
    """Load the aggregated coverage vectors produced by T028."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Coverage vector file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different possible structures (list of vectors or dict with 'vectors' key)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'vectors' in data:
        return data['vectors']
    else:
        raise ValueError(f"Unexpected structure in {filepath}")

def get_observed_variables(vectors: List[Dict[str, Any]]) -> Set[str]:
    """
    Extract the set of state variables that were observed (active) in the training data.
    A variable is considered 'observed' if its count in any vector is > 0.
    """
    observed: Set[str] = set()
    
    for vec in vectors:
        # The vector might be a dict mapping var_name -> count, or a list of counts.
        # Based on typical coverage vector implementations, we expect a dict or a structured object.
        if isinstance(vec, dict):
            for key, value in vec.items():
                if key in ['metadata', 'vector_id', 'timestamp']:
                    continue
                # If value is a count > 0, mark as observed
                if isinstance(value, (int, float)) and value > 0:
                    observed.add(key)
                elif isinstance(value, dict) and value.get('count', 0) > 0:
                    observed.add(key)
        elif isinstance(vec, list):
            # Fallback if vector is a list, though we need the names to compare against schema
            # This case is less likely if we have the schema names, but handled for robustness
            logger.warning("Vector is a list; cannot map indices to variable names without schema mapping.")
    
    return observed

def generate_held_out_test_set() -> Dict[str, Any]:
    """
    Main logic to generate the held-out test set.
    """
    logger.info("Starting T029: Generating held-out test set for transfer evaluation.")
    
    # 1. Get the full universe of semantic proxies (the schema definition)
    all_proxies = get_semantic_proxies()
    logger.info(f"Loaded {len(all_proxies)} semantic proxies from schema.")
    
    if not all_proxies:
        logger.error("No semantic proxies found in schema. Cannot generate test set.")
        return {}

    # 2. Load training data to see what was actually covered
    try:
        vectors = load_aggregated_vectors(COVERAGE_FILE)
        logger.info(f"Loaded {len(vectors)} coverage vectors from {COVERAGE_FILE}.")
    except FileNotFoundError as e:
        logger.error(f"Training data not found. T028 must be completed first. Error: {e}")
        raise
    
    # 3. Identify observed variables
    observed_vars = get_observed_variables(vectors)
    logger.info(f"Identified {len(observed_vars)} unique state variables observed in training data.")
    
    # 4. Compute the difference (Held-out = All - Observed)
    # Note: We only consider variables that are in the schema.
    schema_vars = set(all_proxies)
    held_out_vars = schema_vars - observed_vars
    
    logger.info(f"Calculated {len(held_out_vars)} held-out variables for transfer evaluation.")
    
    # 5. Construct the output artifact
    result = {
        "description": "Held-out test set for transfer evaluation (FR-005).",
        "criteria": "State variables defined in schema but not observed (count > 0) in training coverage vectors.",
        "total_schema_variables": len(schema_vars),
        "observed_in_training": len(observed_vars),
        "held_out_count": len(held_out_vars),
        "held_out_variables": sorted(list(held_out_vars)),
        "observed_variables": sorted(list(observed_vars)),
        "generated_at": "T029 Execution"
    }
    
    return result

def main():
    """Entry point for the script."""
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(OUTPUT_FILE)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        result = generate_held_out_test_set()
        
        # Write to disk
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Successfully wrote held-out test set to {OUTPUT_FILE}")
        logger.info(f"Held-out variables: {result['held_out_variables']}")
        
    except Exception as e:
        logger.error(f"Failed to generate held-out test set: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
