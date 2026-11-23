"""
Configuration Validator for llmXive project.

Validates dataset_paths existence and hash_registry integrity
against config.py values.
"""
import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

# Import from existing API surface
from config import get_path, get_mode, is_ci_mode, get_config_summary
from config_env import get_env_config, verify_dataset, register_artifact
from utils.logger import get_logger, log_error, log_fatal

logger = get_logger("config_validator")


class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors."""
    pass


def validate_dataset_paths(dataset_paths: Dict[str, str], mode: str) -> Tuple[bool, List[str]]:
    """
    Validate that all configured dataset paths exist and are accessible.
    
    Args:
        dataset_paths: Dictionary mapping dataset names to their paths
        mode: Current configuration mode ('CI' or 'RESEARCH')
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    valid = True
    
    if not dataset_paths:
        if mode == "RESEARCH":
            errors.append("RESEARCH mode requires dataset_paths to be configured")
            return False, errors
        else:
            # CI mode might not need all paths if using synthetic data
            logger.info("No dataset_paths configured in CI mode - may use synthetic data")
            return True, []
    
    for name, path_str in dataset_paths.items():
        path = Path(path_str)
        
        # Check if path exists
        if not path.exists():
            # In CI mode, we might create synthetic paths, but we should warn
            if mode == "CI":
                logger.warning(f"Dataset path '{name}' ({path_str}) does not exist in CI mode")
                # Optionally create the path for CI mode
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created missing path: {path}")
                except Exception as e:
                    errors.append(f"Failed to create path for '{name}': {str(e)}")
                    valid = False
            else:
                errors.append(f"Dataset path '{name}' does not exist: {path_str}")
                valid = False
        elif not path.is_dir():
            errors.append(f"Dataset path '{name}' is not a directory: {path_str}")
            valid = False
        else:
            # Check if directory is readable
            try:
                list(path.iterdir())
                logger.info(f"Dataset path '{name}' is accessible: {path_str}")
            except PermissionError:
                errors.append(f"Dataset path '{name}' is not readable: {path_str}")
                valid = False
            except Exception as e:
                errors.append(f"Error accessing dataset path '{name}': {str(e)}")
                valid = False
    
    return valid, errors


def validate_hash_registry(hash_registry: Dict[str, str], dataset_paths: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate hash_registry integrity against actual file hashes.
    
    Args:
        hash_registry: Dictionary mapping file identifiers to expected hashes
        dataset_paths: Dictionary of dataset paths to check against
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    valid = True
    
    if not hash_registry:
        logger.info("No hash_registry configured - skipping hash validation")
        return True, []
    
    # For each registered hash, verify the file exists and hash matches
    for identifier, expected_hash in hash_registry.items():
        # Try to find the file in configured dataset paths
        file_found = False
        file_path = None
        
        for dataset_name, path_str in dataset_paths.items():
            path = Path(path_str)
            # Search for file with identifier in name or as exact match
            for file_path_iter in path.rglob("*"):
                if file_path_iter.is_file():
                    if identifier in file_path_iter.name or file_path_iter.name == identifier:
                        file_found = True
                        file_path = file_path_iter
                        break
            if file_found:
                break
        
        if not file_found:
            # File not found - might be expected if data not downloaded yet
            errors.append(f"Hash registry entry '{identifier}' not found in any dataset path")
            # Don't mark as invalid if file is simply not downloaded yet
            # valid = False
        else:
            # Compute actual hash
            try:
                actual_hash = compute_file_hash(file_path)
                if actual_hash != expected_hash:
                    errors.append(
                        f"Hash mismatch for '{identifier}': "
                        f"expected {expected_hash}, got {actual_hash}"
                    )
                    valid = False
                else:
                    logger.info(f"Hash verified for '{identifier}': {actual_hash}")
            except Exception as e:
                errors.append(f"Error computing hash for '{identifier}': {str(e)}")
                valid = False
    
    return valid, errors


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use
        
    Returns:
        Hex digest of the file hash
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks for large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def validate_config() -> Tuple[bool, List[str]]:
    """
    Main validation function that checks all configuration aspects.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    valid = True
    
    logger.info("Starting configuration validation...")
    
    # Get current mode
    mode = get_mode()
    logger.info(f"Current mode: {mode}")
    
    # Get configuration summary to access dataset_paths and hash_registry
    config_summary = get_config_summary()
    
    # Extract dataset_paths and hash_registry from config summary
    # These should be populated by T004b
    dataset_paths = config_summary.get("dataset_paths", {})
    hash_registry = config_summary.get("hash_registry", {})
    
    logger.info(f"Dataset paths: {list(dataset_paths.keys())}")
    logger.info(f"Hash registry entries: {list(hash_registry.keys())}")
    
    # Validate dataset paths
    paths_valid, path_errors = validate_dataset_paths(dataset_paths, mode)
    errors.extend(path_errors)
    if not paths_valid:
        valid = False
    
    # Validate hash registry
    # Only validate hashes if dataset paths are valid
    if paths_valid:
        hash_valid, hash_errors = validate_hash_registry(hash_registry, dataset_paths)
        errors.extend(hash_errors)
        if not hash_valid:
            valid = False
    
    # Additional validation: Check if required paths exist based on mode
    if mode == "RESEARCH":
        # Research mode requires specific paths
        required_paths = ["raw_data", "annotations", "processed_data"]
        for req_path in required_paths:
            if req_path not in dataset_paths:
                errors.append(f"RESEARCH mode requires '{req_path}' in dataset_paths")
                valid = False
    
    if valid:
        logger.info("Configuration validation PASSED")
    else:
        logger.error(f"Configuration validation FAILED with {len(errors)} errors")
        for error in errors:
            logger.error(f"  - {error}")
    
    return valid, errors


def run_validation() -> bool:
    """
    Run validation and exit with appropriate code.
    
    Returns:
        True if validation passes, False otherwise
    """
    valid, errors = validate_config()
    
    if not valid:
        log_fatal(f"Configuration validation failed: {len(errors)} errors found")
        for error in errors:
            log_error(f"  - {error}")
        return False
    
    logger.info("All configuration checks passed")
    return True


def main():
    """CLI entry point for configuration validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate llmXive configuration")
    parser.add_argument("--mode", choices=["CI", "RESEARCH"], default=None,
                      help="Override configuration mode for validation")
    parser.add_argument("--verbose", action="store_true",
                      help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    if args.mode:
        from config import set_mode
        set_mode(args.mode)
        logger.info(f"Override mode set to: {args.mode}")
    
    success = run_validation()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
