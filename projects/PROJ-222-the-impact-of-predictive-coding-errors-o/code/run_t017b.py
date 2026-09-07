"""
T017b: Removed - Logic merged into T016a.

This task was marked for removal in the task list because its functionality
(computing the transition matrix and saving Markov artifacts) was consolidated
into T016a (code/preprocess.py -> compute_transition_matrix).

This script exists solely to satisfy the task execution pipeline by importing
the logic from T016a and ensuring the artifacts are available, or by acting
as a no-op if the artifacts were already produced by T016a.

Since T016a writes `data/processed/markov_state.json`, this script verifies
its existence and exits successfully.
"""
import sys
import os
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    T017b Implementation: Verify Markov artifacts exist (produced by T016a).
    
    Since the logic was merged into T016a, this task simply verifies that
    the output file `data/processed/markov_state.json` exists.
    """
    # Define the expected path relative to project root
    # Assuming the script runs from project root or we use absolute paths from config
    project_root = Path(__file__).parent.parent
    markov_artifact_path = project_root / "data" / "processed" / "markov_state.json"

    logger.info(f"Checking for Markov artifacts at: {markov_artifact_path}")

    if not markov_artifact_path.exists():
        logger.error(f"CRITICAL: Required artifact {markov_artifact_path} not found.")
        logger.error("T016a (compute_transition_matrix) must be run successfully before T017b.")
        sys.exit(1)

    try:
        with open(markov_artifact_path, 'r') as f:
            data = json.load(f)
        
        # Basic validation that it looks like a Markov state
        assert 'transition_matrix' in data, "Missing 'transition_matrix' key"
        assert 'alphabet' in data, "Missing 'alphabet' key"
        assert 'order' in data, "Missing 'order' key"
        
        logger.info(f"Successfully verified Markov artifacts.")
        logger.info(f"  - Order: {data['order']}")
        logger.info(f"  - Alphabet size: {len(data['alphabet'])}")
        logger.info(f"  - Matrix keys count: {len(data['transition_matrix'])}")
        
        logger.info("T017b completed successfully (Logic merged into T016a).")
        sys.exit(0)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Markov artifacts: {e}")
        sys.exit(1)
    except AssertionError as e:
        logger.error(f"Invalid Markov artifacts structure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()