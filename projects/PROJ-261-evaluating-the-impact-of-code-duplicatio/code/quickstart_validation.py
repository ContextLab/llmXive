"""
Quickstart validation script for the project.

This script validates that all required components are in place:
- Directory structure
- Configuration documentation
- Checksum manifest
- Output files
- Quickstart documentation
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from config import (
    get_clone_thresholds,
    get_random_seed,
    get_memory_limit_mb,
    get_max_runtime_seconds,
    get_min_valid_segments,
    get_correlation_method,
    get_significance_threshold,
)
from checksum_manifest import (
    load_manifest,
    verify_artifact_checksums,
    get_artifact_hashes,
)


def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def validate_directory_structure(logger: Optional[logging.Logger] = None) -> bool:
    """
    Validate that all required directories exist.
    
    Args:
        logger: Logger instance
        
    Returns:
        True if all directories exist, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    project_root = Path(__file__).parent.parent

    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "analysis",
        project_root / "data" / "analysis" / "figures",
        project_root / "code",
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
        project_root / "specs" / "001-evaluating-the-impact-of-code-duplicatio" / "contracts",
    ]

    all_exist = True
    for dir_path in required_dirs:
        if not dir_path.exists():
            logger.error(f"Missing directory: {dir_path}")
            all_exist = False
        else:
            logger.info(f"Directory exists: {dir_path}")

    if all_exist:
        logger.info("All required directories exist")
    else:
        logger.error("Some required directories are missing")

    return all_exist


def validate_config_documentation(logger: Optional[logging.Logger] = None) -> bool:
    """
    Validate that configuration is properly documented.
    
    Args:
        logger: Logger instance
        
    Returns:
        True if configuration is valid, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    try:
        # Test that all config functions work
        thresholds = get_clone_thresholds()
        seed = get_random_seed()
        memory_limit = get_memory_limit_mb()
        max_runtime = get_max_runtime_seconds()
        min_segments = get_min_valid_segments()
        correlation_method = get_correlation_method()
        significance = get_significance_threshold()

        logger.info(f"Clone thresholds: {thresholds}")
        logger.info(f"Random seed: {seed}")
        logger.info(f"Memory limit: {memory_limit} MB")
        logger.info(f"Max runtime: {max_runtime} seconds")
        logger.info(f"Min valid segments: {min_segments}")
        logger.info(f"Correlation method: {correlation_method}")
        logger.info(f"Significance threshold: {significance}")

        logger.info("Configuration validation passed")
        return True

    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False


def validate_checksum_manifest(logger: Optional[logging.Logger] = None) -> bool:
    """
    Validate that checksum manifest is properly maintained.
    
    Args:
        logger: Logger instance
        
    Returns:
        True if manifest is valid, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    project_root = Path(__file__).parent.parent
    manifest_path = project_root / "data" / "artifact_checksums.json"

    if not manifest_path.exists():
        logger.warning(f"Checksum manifest not found: {manifest_path}")
        return False

    try:
        manifest = load_manifest(manifest_path)
        
        if manifest is None:
            logger.error("Failed to load checksum manifest")
            return False

        verified = verify_artifact_checksums(manifest_path, logger=logger)
        
        if verified:
            logger.info("Checksum manifest validation passed")
            return True
        else:
            logger.error("Checksum manifest verification failed")
            return False

    except Exception as e:
        logger.error(f"Checksum manifest validation failed: {e}")
        return False


def validate_quickstart_documentation(logger: Optional[logging.Logger] = None) -> bool:
    """
    Validate that quickstart documentation exists and is readable.
    
    Args:
        logger: Logger instance
        
    Returns:
        True if documentation is valid, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    project_root = Path(__file__).parent.parent
    quickstart_path = project_root / "specs" / "001-evaluating-the-impact-of-code-duplicatio" / "quickstart.md"

    if not quickstart_path.exists():
        logger.error(f"Quickstart documentation not found: {quickstart_path}")
        return False

    try:
        content = quickstart_path.read_text()
        
        if len(content) < 100:
            logger.error("Quickstart documentation appears to be too short")
            return False

        logger.info("Quickstart documentation validation passed")
        return True

    except Exception as e:
        logger.error(f"Quickstart documentation validation failed: {e}")
        return False


def validate_output_files(logger: Optional[logging.Logger] = None) -> bool:
    """
    Validate that output files exist and are non-empty.
    
    Args:
        logger: Logger instance
        
    Returns:
        True if all output files are valid, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    project_root = Path(__file__).parent.parent
    processed_dir = project_root / "data" / "processed"

    required_files = [
        processed_dir / "clone_metrics.csv",
        processed_dir / "perplexity_scores.csv",
    ]

    all_valid = True
    for file_path in required_files:
        if not file_path.exists():
            logger.warning(f"Output file not found: {file_path}")
            all_valid = False
        else:
            size = file_path.stat().st_size
            if size == 0:
                logger.error(f"Output file is empty: {file_path}")
                all_valid = False
            else:
                logger.info(f"Output file exists and has {size} bytes: {file_path}")

    if all_valid:
        logger.info("All output files are valid")
    else:
        logger.warning("Some output files are missing or empty")

    return all_valid


def validate_quickstart_steps(logger: Optional[logging.Logger] = None) -> bool:
    """
    Validate that quickstart steps can be executed.
    
    Args:
        logger: Logger instance
        
    Returns:
        True if steps are valid, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Check that key scripts exist
    project_root = Path(__file__).parent.parent
    scripts = [
        project_root / "code" / "main.py",
        project_root / "code" / "data_loader.py",
        project_root / "code" / "ast_cloner.py",
        project_root / "code" / "model_metrics.py",
    ]

    all_exist = True
    for script in scripts:
        if not script.exists():
            logger.error(f"Script not found: {script}")
            all_exist = False
        else:
            logger.info(f"Script exists: {script}")

    if all_exist:
        logger.info("All required scripts exist")
    else:
        logger.error("Some required scripts are missing")

    return all_exist


def main() -> int:
    """
    Main entry point for quickstart validation.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python quickstart_validation.py <command>")
        print("Commands: validate_directory_structure, validate_config_documentation,")
        print("          validate_checksum_manifest, validate_quickstart_documentation,")
        print("          validate_output_files, validate_quickstart_steps, main")
        return 1

    command = sys.argv[1]
    log_file = Path(__file__).parent.parent / "data" / "validation.log"
    logger = setup_logging(log_file)

    logger.info(f"Running quickstart validation: {command}")

    validators = {
        "validate_directory_structure": validate_directory_structure,
        "validate_config_documentation": validate_config_documentation,
        "validate_checksum_manifest": validate_checksum_manifest,
        "validate_quickstart_documentation": validate_quickstart_documentation,
        "validate_output_files": validate_output_files,
        "validate_quickstart_steps": validate_quickstart_steps,
        "main": lambda: main_validation(logger),
    }

    if command not in validators:
        logger.error(f"Unknown command: {command}")
        return 1

    try:
        result = validators[command](logger)
        if result:
            logger.info(f"Validation passed: {command}")
            return 0
        else:
            logger.error(f"Validation failed: {command}")
            return 1
    except Exception as e:
        logger.error(f"Validation error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


def main_validation(logger: Optional[logging.Logger] = None) -> bool:
    """
    Run all validations.
    
    Args:
        logger: Logger instance
        
    Returns:
        True if all validations pass, False otherwise
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    validations = [
        ("Directory structure", validate_directory_structure),
        ("Configuration", validate_config_documentation),
        ("Checksum manifest", validate_checksum_manifest),
        ("Quickstart docs", validate_quickstart_documentation),
        ("Output files", validate_output_files),
        ("Quickstart steps", validate_quickstart_steps),
    ]

    all_passed = True
    for name, validator in validations:
        logger.info(f"Running {name} validation...")
        if not validator(logger):
            logger.error(f"{name} validation failed")
            all_passed = False
        else:
            logger.info(f"{name} validation passed")

    if all_passed:
        logger.info("All validations passed!")
    else:
        logger.error("Some validations failed")

    return all_passed


if __name__ == "__main__":
    sys.exit(main())