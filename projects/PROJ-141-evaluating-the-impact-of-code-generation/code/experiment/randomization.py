"""
Randomization module for experiment condition assignment.

Implements reproducible randomization per Constitution Principle I.
Handles participant ID generation, condition assignment, seed pinning,
and logging of randomization parameters.
"""

import os
import sys
import json
import logging
import random
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, List, Optional

# Import existing logging infrastructure
from logs.experiment import log_experiment_event, log_condition_assignment, get_logger
# Import existing config
from config.settings import get_config

# Set up module logger
logger = get_logger(__name__)

# Constants for condition assignment
CONDITIONS = ["llm_assisted", "baseline"]

class RandomizationError(Exception):
    """Custom exception for randomization failures."""
    pass


def generate_participant_id() -> str:
    """
    Generate a unique, anonymous participant ID.
    
    Uses UUID4 for uniqueness and ensures no PII is embedded.
    
    Returns:
        str: A unique participant identifier (UUID format).
    """
    return str(uuid.uuid4())


def pin_random_seed(seed: int) -> None:
    """
    Pin all random number generator seeds for reproducibility.
    
    Per Constitution Principle I, this ensures that randomization
    is reproducible across runs given the same seed.
    
    Args:
        seed (int): The seed value to use for all RNGs.
    """
    # Seed Python's random module
    random.seed(seed)
    
    # Log the seed pinning for audit trail
    logger.info(f"Random seed pinned: {seed}")
    log_experiment_event(
        event_type="seed_pinned",
        data={"seed": seed, "timestamp": datetime.now(timezone.utc).isoformat()}
    )


def assign_condition(participant_id: str, seed: int) -> Tuple[str, int]:
    """
    Assign a condition to a participant using seeded randomization.
    
    Uses a seeded random choice to ensure reproducibility while
    maintaining random assignment.
    
    Args:
        participant_id (str): The unique participant identifier.
        seed (int): The random seed for reproducibility.
    
    Returns:
        Tuple[str, int]: A tuple of (assigned_condition, condition_order_index)
        - assigned_condition: Either "llm_assisted" or "baseline"
        - condition_order_index: 0 for first condition, 1 for second (for counterbalancing)
    """
    # Ensure seed is pinned for this assignment
    random.seed(seed)
    
    # Randomly select condition
    assigned_condition = random.choice(CONDITIONS)
    
    # Determine order index (0 or 1) - used for counterbalancing
    condition_order_index = random.randint(0, 1)
    
    # Log the assignment
    log_condition_assignment(
        participant_id=participant_id,
        condition=assigned_condition,
        seed=seed,
        order_index=condition_order_index
    )
    
    logger.info(
        f"Participant {participant_id} assigned to {assigned_condition} "
        f"(order: {condition_order_index}, seed: {seed})"
    )
    
    return assigned_condition, condition_order_index


def create_randomization_record(
    participant_id: str, 
    condition: str, 
    seed: int, 
    order_index: int
) -> Dict[str, Any]:
    """
    Create a complete randomization record for logging and audit.
    
    Args:
        participant_id (str): The participant identifier.
        condition (str): The assigned condition.
        seed (int): The random seed used.
        order_index (int): The condition order index.
    
    Returns:
        Dict[str, Any]: A dictionary containing the full randomization record.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Create deterministic hash for traceability
    record_string = f"{participant_id}:{condition}:{seed}:{order_index}:{timestamp}"
    record_hash = hashlib.sha256(record_string.encode()).hexdigest()[:16]
    
    return {
        "participant_id": participant_id,
        "condition": condition,
        "seed": seed,
        "order_index": order_index,
        "timestamp": timestamp,
        "record_hash": record_hash,
        "version": "1.0"
    }


def initialize_participant_session(
    participant_id: Optional[str] = None,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Initialize a new participant session with randomization.
    
    This is the main entry point for starting a new participant's experiment.
    It generates a participant ID if not provided, pins a seed, assigns a condition,
    and creates a complete randomization record.
    
    Args:
        participant_id (Optional[str]): Existing participant ID, or None to generate.
        seed (Optional[int]): Existing seed, or None to generate.
    
    Returns:
        Dict[str, Any]: A complete session initialization record including
        participant_id, assigned_condition, seed, order_index, and randomization_record.
    """
    # Generate participant ID if not provided
    if participant_id is None:
        participant_id = generate_participant_id()
        logger.info(f"Generated new participant ID: {participant_id}")
    
    # Generate or use provided seed
    if seed is None:
        # Use a high-entropy seed from system randomness
        seed = random.getrandbits(32)
        logger.info(f"Generated random seed: {seed}")
    
    # Pin the seed for reproducibility
    pin_random_seed(seed)
    
    # Assign condition
    condition, order_index = assign_condition(participant_id, seed)
    
    # Create the full record
    randomization_record = create_randomization_record(
        participant_id, condition, seed, order_index
    )
    
    session_data = {
        "participant_id": participant_id,
        "assigned_condition": condition,
        "seed": seed,
        "order_index": order_index,
        "randomization_record": randomization_record,
        "initialized_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Log the full initialization
    log_experiment_event(
        event_type="session_initialized",
        data=session_data
    )
    
    logger.info(f"Session initialized for {participant_id}: {condition} (seed: {seed})")
    
    return session_data


def verify_reproducibility(
    participant_id: str, 
    expected_seed: int, 
    expected_condition: str
) -> bool:
    """
    Verify that a given seed produces the expected condition assignment.
    
    This is a verification utility to ensure reproducibility.
    
    Args:
        participant_id (str): The participant identifier.
        expected_seed (int): The seed that was originally used.
        expected_condition (str): The condition that should be assigned.
    
    Returns:
        bool: True if the seed produces the expected condition, False otherwise.
    """
    # Pin the seed
    pin_random_seed(expected_seed)
    
    # Re-assign condition
    assigned_condition, _ = assign_condition(participant_id, expected_seed)
    
    is_match = assigned_condition == expected_condition
    
    if not is_match:
        logger.error(
            f"Reproducibility check FAILED for {participant_id}: "
            f"expected {expected_condition}, got {assigned_condition}"
        )
    else:
        logger.info(f"Reproducibility check PASSED for {participant_id}")
    
    return is_match


def main():
    """
    Command-line interface for randomization testing and demonstration.
    
    Usage:
        python code/experiment/randomization.py
    """
    print("=" * 60)
    print("Randomization Module Test")
    print("=" * 60)
    
    # Test 1: Generate participant ID
    print("\n1. Generating participant ID...")
    pid = generate_participant_id()
    print(f"   Generated: {pid}")
    assert len(pid) == 36, "Invalid UUID format"
    assert pid != "", "Empty participant ID"
    
    # Test 2: Pin seed and verify
    print("\n2. Pinning seed and verifying...")
    test_seed = 42
    pin_random_seed(test_seed)
    print(f"   Seed pinned: {test_seed}")
    
    # Test 3: Assign condition with known seed (reproducibility test)
    print("\n3. Testing reproducibility with seed 42...")
    condition1, order1 = assign_condition(pid, test_seed)
    print(f"   First assignment: {condition1} (order: {order1})")
    
    # Reset and re-assign with same seed
    pin_random_seed(test_seed)
    condition2, order2 = assign_condition(pid, test_seed)
    print(f"   Second assignment: {condition2} (order: {order2})")
    
    assert condition1 == condition2, "Reproducibility failed: conditions differ"
    assert order1 == order2, "Reproducibility failed: order differs"
    print("   ✓ Reproducibility verified!")
    
    # Test 4: Initialize full session
    print("\n4. Initializing full session...")
    session = initialize_participant_session()
    print(f"   Participant ID: {session['participant_id']}")
    print(f"   Condition: {session['assigned_condition']}")
    print(f"   Seed: {session['seed']}")
    print(f"   Order Index: {session['order_index']}")
    print(f"   Record Hash: {session['randomization_record']['record_hash']}")
    
    # Test 5: Verify reproducibility function
    print("\n5. Testing verify_reproducibility...")
    result = verify_reproducibility(
        session['participant_id'],
        session['seed'],
        session['assigned_condition']
    )
    assert result, "Reproducibility verification failed"
    print("   ✓ Verification passed!")
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
