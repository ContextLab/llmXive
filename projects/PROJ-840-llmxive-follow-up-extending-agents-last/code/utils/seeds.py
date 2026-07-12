import os
import random
import hashlib
import json
import pickle
from typing import Optional, Dict, Any, Tuple, List
import logging

# Configure logger for the module
logger = logging.getLogger(__name__)

def set_seed(seed: int) -> None:
    """Set global random seeds for reproducibility."""
    random.seed(seed)
    # Note: numpy is imported elsewhere, so we don't set it here to avoid circular deps
    # unless explicitly needed in this file.

def get_seed_state() -> Dict[str, Any]:
    """Capture the current state of the random number generator."""
    return {
        "random": random.getstate()
    }

def restore_seed_state(state: Dict[str, Any]) -> None:
    """Restore the random number generator to a previously captured state."""
    if "random" in state:
        random.setstate(state["random"])

def verify_seed(seed: int) -> bool:
    """Verify that a seed is a valid integer and within safe bounds."""
    if not isinstance(seed, int):
        logger.error(f"Seed must be an integer, got {type(seed)}")
        return False
    # Python handles large ints, but we check for reasonable bounds for reproducibility
    if seed < 0 or seed > 2**32 - 1:
        logger.warning(f"Seed {seed} is outside standard 32-bit range, may affect cross-platform reproducibility")
    return True

def generate_task_seed(base_seed: int, task_id: str) -> int:
    """Generate a deterministic task-specific seed from a base seed and task ID."""
    if not verify_seed(base_seed):
        raise ValueError(f"Invalid base seed: {base_seed}")
    
    combined_str = f"{base_seed}:{task_id}"
    hash_obj = hashlib.sha256(combined_str.encode('utf-8'))
    # Take the first 8 bytes and convert to int
    return int.from_bytes(hash_obj.digest()[:8], byteorder='big')

def save_seed_state(state: Dict[str, Any], filepath: str) -> None:
    """Save the seed state to a file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(state, f)
    logger.info(f"Seed state saved to {filepath}")

def load_seed_state(filepath: str) -> Dict[str, Any]:
    """Load the seed state from a file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Seed state file not found: {filepath}")
    with open(filepath, 'rb') as f:
        return pickle.load(f)

def verify_pairing(task_instance: Dict[str, Any], seed: int) -> str:
    """
    Generate a deterministic checksum for a task instance and seed to ensure strict pairing.
    
    This function MUST be called by T015 before data generation.
    It creates a hash of the sorted JSON representation of the task instance 
    combined with the seed.
    
    Args:
        task_instance (Dict[str, Any]): The task data dictionary.
        seed (int): The seed used for generation.
        
    Returns:
        str: A hex string checksum (SHA-256) representing the pairing.
        
    Raises:
        ValueError: If the seed is invalid or task_instance is not a dict.
    """
    if not isinstance(task_instance, dict):
        raise ValueError("task_instance must be a dictionary")
    if not verify_seed(seed):
        raise ValueError(f"Invalid seed for pairing verification: {seed}")
    
    # Create a canonical representation of the task instance
    # Sort keys to ensure deterministic serialization regardless of insertion order
    try:
        canonical_str = json.dumps(task_instance, sort_keys=True, separators=(',', ':'))
    except TypeError as e:
        raise ValueError(f"Task instance contains non-serializable data: {e}")
    
    # Combine with seed
    pairing_str = f"seed:{seed}|data:{canonical_str}"
    
    # Generate SHA-256 checksum
    checksum = hashlib.sha256(pairing_str.encode('utf-8')).hexdigest()
    
    logger.debug(f"Pairing verification generated checksum: {checksum[:16]}...")
    return checksum