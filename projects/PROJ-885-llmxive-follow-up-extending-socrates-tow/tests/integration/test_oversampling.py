"""
Integration test for oversampling distribution (US1).

Verifies that the generated conflict trajectories meet the requirement
of having >= 40% of samples in the "high emotional reactivity" or
"diverse cultural identity" categories.
"""

import json
import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories, setup_logging

# Configure logging for the test
logger = setup_logging("test_oversampling", level=logging.INFO)

TRAJECTORIES_FILE = project_root / "data" / "processed" / "trajectories.json"
EXPECTED_THRESHOLD = 0.40  # 40%

def test_oversampling_distribution():
    """
    Integration test:
    1. Load the generated trajectories from data/processed/trajectories.json
    2. Calculate the percentage of samples with:
       - Emotional Reactivity = "high"
       - Cultural Identity = "diverse"
    3. Assert that the combined percentage is >= 40%.

    This test depends on T012/T013/T014 having run successfully to produce
    the input file.
    """
    if not TRAJECTORIES_FILE.exists():
        logger.error(
            f"Trajectories file not found: {TRAJECTORIES_FILE}. "
            "Ensure T014 (output writer) has been executed first."
        )
        raise FileNotFoundError(
            f"Required input file missing: {TRAJECTORIES_FILE}. "
            "Run the data generation pipeline (T012-T014) before running this test."
        )

    logger.info(f"Loading trajectories from {TRAJECTORIES_FILE}")
    with open(TRAJECTORIES_FILE, "r", encoding="utf-8") as f:
        trajectories = json.load(f)

    if not isinstance(trajectories, list) or len(trajectories) == 0:
        raise ValueError("Trajectories file is empty or malformed.")

    logger.info(f"Loaded {len(trajectories)} trajectories.")

    high_reactivity_count = 0
    diverse_identity_count = 0

    for traj in trajectories:
        metadata = traj.get("metadata", {})
        emotional_reactivity = metadata.get("emotional_reactivity")
        cultural_identity = metadata.get("cultural_identity")

        if emotional_reactivity == "high":
            high_reactivity_count += 1
        
        if cultural_identity == "diverse":
            diverse_identity_count += 1

    # Calculate percentages
    total = len(trajectories)
    pct_high_reactivity = high_reactivity_count / total
    pct_diverse_identity = diverse_identity_count / total

    # The requirement is >= 40% in EITHER category (union) or combined?
    # The spec says "oversampling scenarios with 'high emotional reactivity' 
    # and 'diverse cultural identity' attributes". Usually, this implies 
    # the union of these sets should be >= 40%, or the specific target 
    # categories combined. 
    # Given T013 description: "ensure ≥40% of trajectories fall into 
    # 'high emotional reactivity' or 'diverse cultural identity' categories".
    # We calculate the union (samples that are EITHER high reactivity OR diverse identity).
    
    # Recalculate union
    union_count = 0
    for traj in trajectories:
        metadata = traj.get("metadata", {})
        emotional_reactivity = metadata.get("emotional_reactivity")
        cultural_identity = metadata.get("cultural_identity")
        
        if emotional_reactivity == "high" or cultural_identity == "diverse":
            union_count += 1

    union_percentage = union_count / total

    logger.info(f"High Emotional Reactivity count: {high_reactivity_count} ({pct_high_reactivity:.2%})")
    logger.info(f"Diverse Cultural Identity count: {diverse_identity_count} ({pct_diverse_identity:.2%})")
    logger.info(f"Union (High Reactivity OR Diverse Identity) count: {union_count} ({union_percentage:.2%})")

    assert union_percentage >= EXPECTED_THRESHOLD, (
        f"Oversampling threshold not met. "
        f"Expected >= {EXPECTED_THRESHOLD:.0%} samples with 'high emotional reactivity' OR 'diverse cultural identity', "
        f"but got {union_percentage:.2%} ({union_count}/{total})."
    )

    logger.info("SUCCESS: Oversampling distribution meets the >= 40% threshold.")

if __name__ == "__main__":
    test_oversampling_distribution()
    print("Test passed.")