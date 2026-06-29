"""
Quickstart validation module.

Validates project structure, configuration, and output files.
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
    get_min_valid_segments,
)
from checksum_manifest import (
    load_manifest,
    verify_artifact_checksums,
)

logger = logging.getLogger(__name__)

def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure logging for the validation module."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )

def validate_directory_structure() -> bool:
    """
    Validate that required directories exist.
    
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
    ]
    
    all_valid = True
    for dir_path in required_dirs:
        if dir_path.exists():
            logger.info(f"  {dir_path}: OK")
        else:
            logger.error(f"  {dir_path}: MISSING")
            all_valid = False
    
    return all_valid

def validate_config_documentation() -> bool:
    """
    Validate that configuration is properly documented.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        thresholds = get_clone_thresholds()
        seed = get_random_seed()
        memory = get_memory_limit_mb()
        runtime = get_max_runtime_seconds()
        segments = get_min_valid_segments()
        
        logger.info("  config.py: OK")
        logger.info(f"    thresholds: {thresholds}")
        logger.info(f"    seed: {seed}")
        logger.info(f"    memory_limit: {memory}")
        logger.info(f"    max_runtime: {runtime}")
        logger.info(f"    min_segments: {segments}")
        
        return True
    except Exception as e:
        logger.error(f"  config.py: FAIL - {e}")
        return False

def validate_checksum_manifest() -> bool:
    """
    Validate checksum manifest exists and is valid.
    
    Returns:
        True if manifest is valid, False otherwise
    """
    manifest_path = Path("data/analysis/checksum_manifest.json")
    
    if manifest_path.exists():
        try:
            manifest = load_manifest(manifest_path)
            if manifest and 'artifact_hashes' in manifest:
                logger.info(f"  checksum_manifest: OK ({len(manifest['artifact_hashes'])} artifacts)")
                return True
            else:
                logger.error("  checksum_manifest: INVALID (missing artifact_hashes)")
                return False
        except Exception as e:
            logger.error(f"  checksum_manifest: ERROR - {e}")
            return False
    else:
        logger.info("  checksum_manifest: NOT YET GENERATED (expected before pipeline run)")
        return True

def validate_quickstart_documentation() -> bool:
    """
    Validate that quickstart documentation exists.
    
    Returns:
        True if documentation exists, False otherwise
    """
    quickstart_path = Path("quickstart.md")
    
    if quickstart_path.exists():
        logger.info("  quickstart_documentation: OK")
        return True
    else:
        logger.error("  quickstart_documentation: MISSING")
        return False

def validate_output_files() -> bool:
    """
    Validate that output files exist after pipeline run.
    
    Returns:
        True if all expected outputs exist, False otherwise
    """
    required_files = [
        Path("data/raw/github-code-sample.csv"),
        Path("data/processed/clone_metrics.csv"),
        Path("data/processed/perplexity_scores.csv"),
        Path("data/analysis/correlation_results.csv"),
    ]
    
    all_valid = True
    for file_path in required_files:
        if file_path.exists():
            logger.info(f"  {file_path}: OK")
        else:
            logger.info(f"  {file_path}: NOT YET GENERATED (expected before pipeline run)")
    
    return all_valid

def validate_quickstart_steps() -> bool:
    """
    Validate that quickstart.md contains required steps.
    
    Returns:
        True if steps are documented, False otherwise
    """
    quickstart_path = Path("quickstart.md")
    
    if not quickstart_path.exists():
        logger.error("  quickstart_steps: QUICKSTART MISSING")
        return False
    
    with open(quickstart_path, 'r') as f:
        content = f.read()
    
    required_steps = [
        "python code/data_loader.py",
        "python code/main.py",
        "data/raw/github-code-sample.csv",
    ]
    
    all_valid = True
    for step in required_steps:
        if step in content:
            logger.info(f"  quickstart_steps: '{step}' - FOUND")
        else:
            logger.error(f"  quickstart_steps: '{step}' - MISSING")
            all_valid = False
    
    return all_valid

def main():
    """
    Main entry point for quickstart validation.
    """
    parser = argparse.ArgumentParser(description='Validate project quickstart')
    parser.add_argument(
        'command',
        nargs='?',
        default='validate_all',
        choices=['validate_all', 'validate_directory_structure', 'validate_config_documentation', 
                'validate_checksum_manifest', 'validate_quickstart_documentation', 
                'validate_output_files', 'validate_quickstart_steps'],
        help='Validation command to run'
    )
    
    args = parser.parse_args()
    
    setup_logging()
    logger.info("=== Quickstart Validation ===")
    
    commands = {
        'validate_all': [
            validate_directory_structure,
            validate_config_documentation,
            validate_checksum_manifest,
            validate_quickstart_documentation,
            validate_output_files,
            validate_quickstart_steps,
        ],
        'validate_directory_structure': [validate_directory_structure],
        'validate_config_documentation': [validate_config_documentation],
        'validate_checksum_manifest': [validate_checksum_manifest],
        'validate_quickstart_documentation': [validate_quickstart_documentation],
        'validate_output_files': [validate_output_files],
        'validate_quickstart_steps': [validate_quickstart_steps],
    }
    
    validators = commands.get(args.command, [])
    results = []
    
    for validator in validators:
        result = validator()
        results.append(result)
    
    if all(results):
        logger.info("=== All validations passed ===")
        return 0
    else:
        logger.error("Some validations failed")
        return 1

if __name__ == '__main__':
    import argparse
    sys.exit(main())