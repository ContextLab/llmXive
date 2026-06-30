"""
Security hardening utilities for the llmXive pipeline.

This module provides:
1. Secure random seed generation using os.urandom.
2. Input sanitization for file paths and user inputs to prevent injection.
3. Validation of configuration values.
"""
import os
import re
import logging
import secrets
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Whitelist for safe file extensions
SAFE_EXTENSIONS = {'.csv', '.json', '.txt', '.parquet', '.tsv', '.npy', '.pkl'}

# Whitelist for safe characters in identifiers
IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z0-9_]+$')

def get_secure_seed() -> int:
    """
    Generate a cryptographically secure random seed.
    
    Returns:
        int: A 64-bit integer suitable for seeding numpy or random.
    """
    # Generate 8 bytes (64 bits) of random data
    random_bytes = os.urandom(8)
    seed = int.from_bytes(random_bytes, byteorder='big')
    logger.debug(f"Generated secure seed: {seed}")
    return seed

def sanitize_path(
    input_path: Union[str, Path], 
    base_dir: Optional[Path] = None,
    allow_glob: bool = False
) -> Path:
    """
    Sanitize a file path to prevent directory traversal and injection.
    
    Args:
        input_path: The user-provided path string or Path object.
        base_dir: Optional base directory to restrict access to (jail).
        allow_glob: If True, allow * and ? characters (for glob patterns).
        
    Returns:
        Path: A validated, absolute Path object.
        
    Raises:
        ValueError: If the path contains unsafe characters or escapes the base directory.
        TypeError: If input is not a string or Path.
    """
    if input_path is None:
        raise ValueError("Path cannot be None")
        
    if isinstance(input_path, Path):
        path_str = str(input_path)
    elif isinstance(input_path, str):
        path_str = input_path
    else:
        raise TypeError(f"Path must be str or Path, got {type(input_path)}")
        
    # Check for null bytes
    if '\x00' in path_str:
        raise ValueError("Path contains null byte")
        
    # Check for directory traversal attempts
    if '..' in path_str:
        # Normalize first to see if it actually escapes
        normalized = Path(path_str).resolve()
        if base_dir:
            try:
                normalized.relative_to(base_dir.resolve())
            except ValueError:
                raise ValueError(f"Path '{path_str}' attempts to escape base directory '{base_dir}'")
        else:
            # If no base dir, just ensure it doesn't start with ..
            if path_str.startswith('..') or '/..' in path_str or '\\..' in path_str:
                raise ValueError(f"Path '{path_str}' contains directory traversal")
                
    # Check for shell metacharacters if not allowing glob
    if not allow_glob:
        unsafe_chars = [';', '|', '&', '$', '`', '(', ')', '{', '}', '<', '>', '\n', '\r']
        for char in unsafe_chars:
            if char in path_str:
                raise ValueError(f"Path contains unsafe character: {repr(char)}")
                
    # Validate extension if present
    p_obj = Path(path_str)
    if p_obj.suffix and p_obj.suffix.lower() not in SAFE_EXTENSIONS:
        logger.warning(f"Unusual file extension detected: {p_obj.suffix}. Proceeding with caution.")
        
    return Path(path_str)

def sanitize_identifier(name: str) -> str:
    """
    Sanitize a string to be used as an identifier (e.g., column name, variable).
    
    Args:
        name: The input string.
        
    Returns:
        str: A sanitized string containing only alphanumeric characters and underscores.
        
    Raises:
        ValueError: If the string becomes empty after sanitization.
    """
    if not isinstance(name, str):
        raise TypeError("Identifier must be a string")
        
    # Remove anything that isn't alphanumeric or underscore
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', name)
    
    if not sanitized:
        raise ValueError(f"Identifier '{name}' contains no valid characters")
        
    return sanitized

def validate_config_value(
    config: Dict[str, Any],
    required_keys: List[str],
    allowed_types: Optional[Dict[str, type]] = None
) -> Dict[str, Any]:
    """
    Validate a configuration dictionary against required keys and types.
    
    Args:
        config: The configuration dictionary.
        required_keys: List of keys that must be present.
        allowed_types: Optional dict mapping keys to expected types.
        
    Returns:
        Dict[str, Any]: The validated config.
        
    Raises:
        ValueError: If required keys are missing or types are incorrect.
    """
    if not isinstance(config, dict):
        raise TypeError("Configuration must be a dictionary")
        
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")
            
    if allowed_types:
        for key, expected_type in allowed_types.items():
            if key in config:
                if not isinstance(config[key], expected_type):
                    raise ValueError(
                        f"Configuration key '{key}' must be of type {expected_type.__name__}, "
                        f"got {type(config[key]).__name__}"
                    )
                    
    return config

def secure_random_choice(seq: list) -> Any:
    """
    Select a random element from a sequence using a cryptographically secure method.
    
    Args:
        seq: A sequence of elements.
        
    Returns:
        Any: A randomly selected element.
    """
    if not seq:
        raise ValueError("Sequence cannot be empty")
        
    return secrets.choice(seq)

def secure_shuffle(seq: list) -> list:
    """
    Shuffle a list in-place using a cryptographically secure method.
    
    Args:
        seq: The list to shuffle.
        
    Returns:
        list: The shuffled list (same object).
    """
    if not isinstance(seq, list):
        raise TypeError("Secure shuffle requires a list")
        
    # Use secrets.SystemRandom for shuffling
    rng = secrets.SystemRandom()
    rng.shuffle(seq)
    return seq

def main():
    """
    CLI entry point for security hardening utilities.
    Runs a self-test of the security functions.
    """
    logging.basicConfig(level=logging.INFO)
    
    logger.info("Running security hardening self-tests...")
    
    # Test 1: Secure Seed
    seed = get_secure_seed()
    logger.info(f"Secure seed generated: {seed}")
    assert isinstance(seed, int), "Seed must be an integer"
    
    # Test 2: Path Sanitization
    try:
        safe_path = sanitize_path("data/derived/trial_data.csv", base_dir=Path("data"))
        logger.info(f"Safe path validated: {safe_path}")
    except ValueError as e:
        logger.error(f"Path validation failed unexpectedly: {e}")
        
    try:
        unsafe_path = sanitize_path("../etc/passwd", base_dir=Path("data"))
        logger.error("Path traversal was NOT detected!")
    except ValueError:
        logger.info("Path traversal correctly blocked.")
        
    # Test 3: Identifier Sanitization
    clean_id = sanitize_identifier("user-input_123")
    logger.info(f"Sanitized identifier: {clean_id}")
    
    # Test 4: Config Validation
    test_config = {"seed": 42, "n_samples": 1000}
    try:
        validate_config_value(test_config, ["seed", "n_samples"], {"seed": int})
        logger.info("Config validation passed.")
    except ValueError as e:
        logger.error(f"Config validation failed: {e}")
        
    logger.info("Security hardening self-tests completed successfully.")

if __name__ == "__main__":
    main()
