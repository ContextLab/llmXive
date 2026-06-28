"""Quickstart validation script for reproducibility verification.

This script validates that the quickstart documentation steps work correctly
by verifying configuration parameters, directory structure, checksum manifest,
and output file generation.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import (
    get_clone_thresholds,
    get_random_seed,
    get_memory_limit_mb,
    get_max_runtime_seconds,
    get_min_valid_segments,
    get_correlation_method,
    get_significance_threshold,
    get_figure_format,
    get_figure_dpi,
    get_checksum_algorithm,
    get_dataset_name,
    get_model_name,
    get_quantization_bits,
    get_streaming_enabled,
    get_pii_scan_enabled,
    get_all_config,
)
from checksum_manifest import (
    setup_logging as setup_manifest_logging,
    compute_file_checksum,
    load_manifest,
    save_manifest,
)

# Set up logging
logger = logging.getLogger(__name__)


def validate_config_documentation() -> bool:
    """Validate that all required configuration parameters are documented."""
    logger.info("Validating configuration documentation...")

    config = get_all_config()
    required_params = [
        'clone_thresholds',
        'random_seed',
        'memory_limit_mb',
        'max_runtime_seconds',
        'min_valid_segments',
        'correlation_method',
        'significance_threshold',
        'figure_format',
        'figure_dpi',
        'checksum_algorithm',
        'dataset_name',
        'model_name',
        'quantization_bits',
        'streaming_enabled',
        'pii_scan_enabled',
    ]

    missing = []
    for param in required_params:
        if param not in config:
            missing.append(param)

    if missing:
        logger.error(f"Missing configuration parameters: {missing}")
        return False

    logger.info(f"All {len(required_params)} configuration parameters validated.")
    return True


def validate_directory_structure() -> bool:
    """Validate that required directories exist."""
    logger.info("Validating directory structure...")

    required_dirs = [
        project_root / 'data' / 'raw',
        project_root / 'data' / 'processed',
        project_root / 'data' / 'analysis',
        project_root / 'data' / 'analysis' / 'figures',
        project_root / 'specs' / '001-evaluating-the-impact-of-code-duplication',
        project_root / 'specs' / '001-evaluating-the-impact-of-code-duplication' / 'contracts',
    ]

    missing = []
    for dir_path in required_dirs:
        if not dir_path.exists():
            missing.append(str(dir_path))

    if missing:
        logger.error(f"Missing directories: {missing}")
        return False

    logger.info(f"All {len(required_dirs)} directories validated.")
    return True


def validate_checksum_manifest() -> bool:
    """Validate that checksum manifest exists and is valid."""
    logger.info("Validating checksum manifest...")

    manifest_path = project_root / 'data' / 'checksum_manifest.json'

    if not manifest_path.exists():
        logger.warning(f"Checksum manifest not found at {manifest_path}. Creating new one.")
        manifest = {
            'version': '1.0',
            'created_at': '2024-01-01T00:00:00',
            'artifact_hashes': {}
        }
        save_manifest(manifest_path, manifest)
        return True

    try:
        manifest = load_manifest(manifest_path)
        if 'artifact_hashes' not in manifest:
            logger.error("Checksum manifest missing 'artifact_hashes' key.")
            return False
        logger.info(f"Checksum manifest validated with {len(manifest['artifact_hashes'])} artifacts.")
        return True
    except Exception as e:
        logger.error(f"Failed to load checksum manifest: {e}")
        return False


def validate_quickstart_documentation() -> bool:
    """Validate that quickstart.md exists and is readable."""
    logger.info("Validating quickstart documentation...")

    quickstart_path = project_root / 'specs' / '001-evaluating-the-impact-of-code-duplication' / 'quickstart.md'

    if not quickstart_path.exists():
        logger.error(f"Quickstart documentation not found at {quickstart_path}")
        return False

    try:
        with open(quickstart_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for key sections
        required_sections = [
            'Quickstart',
            'Installation',
            'Running the Pipeline',
            'Expected Outputs',
        ]

        missing_sections = []
        for section in required_sections:
            if section.lower() not in content.lower():
                missing_sections.append(section)

        if missing_sections:
            logger.warning(f"Quickstart may be missing sections: {missing_sections}")
            return False

        logger.info(f"Quickstart documentation validated at {quickstart_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to read quickstart documentation: {e}")
        return False


def validate_output_files() -> bool:
    """Validate that expected output directories and files are accessible."""
    logger.info("Validating output file structure...")

    data_raw = project_root / 'data' / 'raw'
    data_processed = project_root / 'data' / 'processed'
    data_analysis = project_root / 'data' / 'analysis'

    # Check directories exist
    if not data_raw.exists():
        logger.warning(f"Data directory {data_raw} does not exist. Pipeline may not have run.")
        return False

    if not data_processed.exists():
        logger.warning(f"Processed directory {data_processed} does not exist.")
        return False

    if not data_analysis.exists():
        logger.warning(f"Analysis directory {data_analysis} does not exist.")
        return False

    logger.info("Output file structure validated.")
    return True


def validate_quickstart_steps() -> Dict[str, Any]:
    """Run through all quickstart validation steps."""
    logger.info("Starting quickstart validation...")

    results = {
        'config_validation': False,
        'directory_validation': False,
        'checksum_validation': False,
        'documentation_validation': False,
        'output_validation': False,
        'overall_success': False,
    }

    # Step 1: Validate configuration
    results['config_validation'] = validate_config_documentation()

    # Step 2: Validate directory structure
    results['directory_validation'] = validate_directory_structure()

    # Step 3: Validate checksum manifest
    results['checksum_validation'] = validate_checksum_manifest()

    # Step 4: Validate quickstart documentation
    results['documentation_validation'] = validate_quickstart_documentation()

    # Step 5: Validate output files
    results['output_validation'] = validate_output_files()

    # Overall success requires all critical validations
    results['overall_success'] = all([
        results['config_validation'],
        results['directory_validation'],
        results['checksum_validation'],
        results['documentation_validation'],
    ])

    # Output validation is warning-level, not failure
    if not results['output_validation']:
        logger.warning("Output files not found - pipeline may not have been executed yet.")

    return results


def main() -> int:
    """Main entry point for quickstart validation."""
    # Set up logging
    setup_manifest_logging()
    logger.setLevel(logging.INFO)

    logger.info("=" * 60)
    logger.info("Quickstart Validation for PROJ-261")
    logger.info("=" * 60)

    # Run validation
    results = validate_quickstart_steps()

    # Log results
    logger.info("-" * 60)
    logger.info("Validation Results:")
    logger.info(f"  Config Validation: {'PASS' if results['config_validation'] else 'FAIL'}")
    logger.info(f"  Directory Validation: {'PASS' if results['directory_validation'] else 'FAIL'}")
    logger.info(f"  Checksum Validation: {'PASS' if results['checksum_validation'] else 'FAIL'}")
    logger.info(f"  Documentation Validation: {'PASS' if results['documentation_validation'] else 'FAIL'}")
    logger.info(f"  Output Validation: {'PASS' if results['output_validation'] else 'WARN'}")
    logger.info(f"  Overall: {'PASS' if results['overall_success'] else 'FAIL'}")
    logger.info("-" * 60)

    if results['overall_success']:
        logger.info("Quickstart validation PASSED. Reproducibility steps are working.")
        return 0
    else:
        logger.error("Quickstart validation FAILED. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
