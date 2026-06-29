"""
Quickstart validation script for PROJ-261.

This script validates the project setup and ensures all required
components are in place before running the analysis pipeline.
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict
from config import (
    get_clone_thresholds,
    get_random_seed,
    get_memory_limit_mb,
    get_max_runtime_seconds,
)
from checksum_manifest import (
    load_manifest,
    verify_artifact_checksums,
)

def setup_logging(name: str) -> logging.Logger:
    """Setup logging configuration for validation script."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(Path("data/quickstart_validation.log"))
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def validate_directory_structure(logger: logging.Logger) -> bool:
    """
    Validate that all required directories exist.

    Args:
        logger: Logger instance

    Returns:
        True if all directories exist, False otherwise
    """
    required_dirs = [
        Path("data/raw"),
        Path("data/processed"),
        Path("data/analysis"),
        Path("data/analysis/figures"),
        Path("code"),
        Path("tests"),
        Path("specs/001-evaluating-the-impact-of-code-duplication"),
        Path("specs/001-evaluating-the-impact-of-code-duplication/contracts"),
    ]

    all_valid = True
    for dir_path in required_dirs:
        if not dir_path.exists():
            logger.error(f"Missing directory: {dir_path}")
            all_valid = False
        else:
            logger.info(f"Directory exists: {dir_path}")

    return all_valid

def validate_config_documentation(logger: logging.Logger) -> bool:
    """
    Validate that configuration is properly documented.

    Args:
        logger: Logger instance

    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        thresholds = get_clone_thresholds()
        seed = get_random_seed()
        memory_limit = get_memory_limit_mb()
        max_runtime = get_max_runtime_seconds()

        logger.info(f"Configuration loaded:")
        logger.info(f"  Clone thresholds: {thresholds}")
        logger.info(f"  Random seed: {seed}")
        logger.info(f"  Memory limit: {memory_limit} MB")
        logger.info(f"  Max runtime: {max_runtime} seconds")

        return True
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False

def validate_checksum_manifest(logger: logging.Logger) -> bool:
    """
    Validate checksum manifest exists and is valid.

    Args:
        logger: Logger instance

    Returns:
        True if manifest is valid, False otherwise
    """
    manifest_path = Path("data/checksum_manifest.json")

    if not manifest_path.exists():
        logger.warning(f"Checksum manifest not found: {manifest_path}")
        logger.info("This is expected before first pipeline run")
        return True

    try:
        manifest = load_manifest(manifest_path)
        valid, errors = verify_artifact_checksums(manifest, logger)

        if valid:
            logger.info("Checksum manifest validation passed")
            return True
        else:
            logger.error(f"Checksum validation failed: {errors}")
            return False
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        return False

def validate_quickstart_documentation(logger: logging.Logger) -> bool:
    """
    Validate that quickstart.md exists and contains required sections.

    Args:
        logger: Logger instance

    Returns:
        True if documentation is valid, False otherwise
    """
    quickstart_path = Path("specs/001-evaluating-the-impact-of-code-duplication/quickstart.md")

    if not quickstart_path.exists():
        logger.error(f"Quickstart documentation not found: {quickstart_path}")
        return False

    try:
        content = quickstart_path.read_text()

        required_sections = [
            "## Setup",
            "## Data Download",
            "## Running the Pipeline",
            "## Expected Outputs",
        ]

        for section in required_sections:
            if section not in content:
                logger.error(f"Missing section in quickstart.md: {section}")
                return False

        logger.info("Quickstart documentation validation passed")
        return True
    except Exception as e:
        logger.error(f"Failed to read quickstart.md: {e}")
        return False

def validate_output_files(logger: logging.Logger) -> bool:
    """
    Validate that required output files exist.

    Args:
        logger: Logger instance

    Returns:
        True if all output files exist, False otherwise
    """
    required_files = [
        Path("data/processed/clone_metrics.csv"),
        Path("data/processed/perplexity_scores.csv"),
    ]

    all_valid = True
    for file_path in required_files:
        if not file_path.exists():
            logger.warning(f"Missing output file: {file_path}")
            all_valid = False
        else:
            logger.info(f"Output file exists: {file_path}")

    return all_valid

def validate_quickstart_steps(logger: logging.Logger) -> bool:
    """
    Validate that quickstart steps are executable.

    Args:
        logger: Logger instance

    Returns:
        True if steps are valid, False otherwise
    """
    quickstart_path = Path("specs/001-evaluating-the-impact-of-code-duplication/quickstart.md")

    if not quickstart_path.exists():
        logger.error(f"Quickstart documentation not found: {quickstart_path}")
        return False

    try:
        content = quickstart_path.read_text()

        # Check for required commands
        required_commands = [
            "python code/data_loader.py",
            "python code/main.py",
        ]

        for cmd in required_commands:
            if cmd not in content:
                logger.warning(f"Missing command in quickstart.md: {cmd}")

        logger.info("Quickstart steps validation passed")
        return True
    except Exception as e:
        logger.error(f"Failed to validate quickstart steps: {e}")
        return False

def main():
    """Main entry point for validation script."""
    logger = setup_logging("quickstart_validation")

    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation")
    logger.info("=" * 60)

    results = {}

    # Run all validations
    results["directory_structure"] = validate_directory_structure(logger)
    results["config_documentation"] = validate_config_documentation(logger)
    results["checksum_manifest"] = validate_checksum_manifest(logger)
    results["quickstart_documentation"] = validate_quickstart_documentation(logger)
    results["output_files"] = validate_output_files(logger)
    results["quickstart_steps"] = validate_quickstart_steps(logger)

    # Summary
    logger.info("=" * 60)
    logger.info("Validation Summary")
    logger.info("=" * 60)

    all_passed = all(results.values())

    for check, passed in results.items():
        status = "PASS" if passed else "FAIL"
        logger.info(f"  {check}: {status}")

    if all_passed:
        logger.info("All validations passed!")
        sys.exit(0)
    else:
        logger.error("Some validations failed")
        sys.exit(1)

if __name__ == "__main__":
    main()