"""
Seed Manager for llmXive Project PROJ-194.

Implements Constitution Principle VI: Reproducibility.
Logs transform_seed and SHA256 hash of identifier mapping dictionaries
for every variant generation.
"""
import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Ensure the data directory exists
DATA_DIR = "data"
SEED_LOG_PATH = os.path.join(DATA_DIR, "transform_seeds.jsonl")


def _ensure_data_dir() -> None:
    """Create the data directory if it does not exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def compute_mapping_hash(identifier_mapping: Dict[str, str]) -> str:
    """
    Compute the SHA256 hash of an identifier mapping dictionary.
    
    Args:
        identifier_mapping: Dictionary mapping original identifiers to new ones.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    # Sort keys to ensure deterministic serialization
    serialized = json.dumps(identifier_mapping, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def log_transform_seed(
    transform_seed: int,
    variant_type: str,
    identifier_mapping: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Log a transform seed and associated metadata to the seed log file.
    
    This function ensures reproducibility by recording:
    1. The random seed used for the transformation.
    2. The SHA256 hash of the identifier mapping (if provided).
    3. Timestamp and variant type.
    
    Args:
        transform_seed: The integer seed used for random operations.
        variant_type: String describing the type of transformation (e.g., "black_format", "generic_naming").
        identifier_mapping: Optional dictionary of identifier renamings. If provided, its hash is computed.
        metadata: Optional additional context (e.g., function_id, source_file).
        
    Returns:
        A dictionary representing the logged entry.
        
    Raises:
        ValueError: If transform_seed is not an integer.
    """
    if not isinstance(transform_seed, int):
        raise ValueError(f"transform_seed must be an integer, got {type(transform_seed)}")
    
    _ensure_data_dir()
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "transform_seed": transform_seed,
        "variant_type": variant_type,
        "identifier_mapping_hash": None,
        "metadata": metadata or {}
    }
    
    if identifier_mapping is not None:
        entry["identifier_mapping_hash"] = compute_mapping_hash(identifier_mapping)
        # Optionally store a truncated version of the mapping for debugging (first 5 items)
        if len(identifier_mapping) > 0:
            sample_keys = list(identifier_mapping.keys())[:5]
            entry["metadata"]["mapping_sample"] = {k: identifier_mapping[k] for k in sample_keys}
    
    # Append to JSONL file
    with open(SEED_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
        
    return entry


def get_seed_entry(
    transform_seed: int,
    variant_type: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve a logged seed entry by seed value and optionally variant type.
    
    Args:
        transform_seed: The seed integer to search for.
        variant_type: Optional filter for variant type.
        
    Returns:
        The first matching log entry, or None if not found.
    """
    if not os.path.exists(SEED_LOG_PATH):
        return None
        
    with open(SEED_LOG_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry["transform_seed"] == transform_seed:
                    if variant_type is None or entry["variant_type"] == variant_type:
                        return entry
            except json.JSONDecodeError:
                continue
    return None


def verify_reproducibility(
    expected_seed: int,
    expected_mapping: Dict[str, str],
    variant_type: str
) -> bool:
    """
    Verify that a specific transformation seed and mapping hash exist in the log.
    
    Args:
        expected_seed: The seed to verify.
        expected_mapping: The mapping dictionary to hash and compare.
        variant_type: The variant type to match.
        
    Returns:
        True if a matching entry is found, False otherwise.
    """
    entry = get_seed_entry(expected_seed, variant_type)
    if entry is None:
        return False
        
    expected_hash = compute_mapping_hash(expected_mapping)
    return entry.get("identifier_mapping_hash") == expected_hash


def main() -> None:
    """
    CLI entry point for testing the seed manager.
    Demonstrates logging and verification.
    """
    print("Testing Seed Manager (T006)...")
    
    # Simulate a transformation
    test_seed = 42
    test_mapping = {
        "calculate_total": "calc_total",
        "user_input": "u_in",
        "final_result": "res"
    }
    test_type = "generic_naming_test"
    
    # Log it
    result = log_transform_seed(
        transform_seed=test_seed,
        variant_type=test_type,
        identifier_mapping=test_mapping,
        metadata={"source": "test_script"}
    )
    print(f"Logged entry: {result}")
    
    # Verify it
    is_valid = verify_reproducibility(test_seed, test_mapping, test_type)
    print(f"Reproducibility verification: {'PASSED' if is_valid else 'FAILED'}")
    
    # Retrieve it
    retrieved = get_seed_entry(test_seed, test_type)
    print(f"Retrieved entry hash: {retrieved.get('identifier_mapping_hash')}")

if __name__ == "__main__":
    main()
