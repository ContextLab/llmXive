"""
Script to generate provenance sidecars for all preprocessed fMRI files.

This script scans the processed-fmri directory, identifies all preprocessed BOLD images,
and generates YAML provenance sidecars for each file, recording pipeline version,
parameters, and execution context.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from utils.provenance import (
    generate_provenance_sidecar,
    generate_provenance_manifest,
    get_software_versions,
)
from utils.config_loader import load_config


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def find_preprocessed_files(
    processed_dir: str,
    file_pattern: str = "*space-MNI_bold.nii.gz",
) -> list:
    """
    Find all preprocessed BOLD files in the specified directory.

    Args:
        processed_dir: Directory containing preprocessed files
        file_pattern: Glob pattern for matching files

    Returns:
        List of paths to preprocessed files
    """
    processed_path = Path(processed_dir)
    if not processed_path.exists():
        logger.warning(f"Processed directory does not exist: {processed_dir}")
        return []

    files = list(processed_path.rglob(file_pattern))
    logger.info(f"Found {len(files)} preprocessed files matching pattern")
    return files


def get_processing_parameters() -> dict:
    """
    Get processing parameters from configuration or defaults.

    Returns:
        Dictionary of processing parameters
    """
    try:
        config = load_config()
        params = {
            "smoothing_fwhm_mm": config.get("preprocessing", {}).get(
                "smoothing_fwhm_mm", 6
            ),
            "realign": True,
            "normalize": True,
            "slice_timing": True,
            "motion_correction": True,
            "coregistration": True,
        }
    except Exception as e:
        logger.warning(f"Could not load config, using defaults: {e}")
        params = {
            "smoothing_fwhm_mm": 6,
            "realign": True,
            "normalize": True,
            "slice_timing": True,
            "motion_correction": True,
            "coregistration": True,
        }

    return params


def generate_sidecars_for_files(
    files: list,
    base_input_dir: str = "data/raw-fmri",
    dry_run: bool = False,
) -> tuple:
    """
    Generate provenance sidecars for a list of preprocessed files.

    Args:
        files: List of paths to preprocessed files
        base_input_dir: Base directory for input files (for reference)
        dry_run: If True, only log what would be done without writing

    Returns:
        Tuple of (successful_count, failed_count)
    """
    success_count = 0
    failed_count = 0
    software_versions = get_software_versions()
    parameters = get_processing_parameters()

    for output_file in files:
        # Derive input file path (simplified mapping)
        relative_path = output_file.relative_to(Path("data/processed-fmri"))
        input_file = Path(base_input_dir) / relative_path

        # Check if input file exists (for reference)
        if not input_file.exists():
            logger.warning(f"Input file not found: {input_file}, using placeholder")
            input_file = Path("data/raw-fmri/placeholder.nii.gz")

        try:
            if not dry_run:
                  sidecar_path = generate_provenance_sidecar(
                      input_file=str(input_file),
                      output_file=str(output_file),
                      parameters=parameters,
                      software_versions=software_versions,
                  )
                  logger.info(f"Generated sidecar: {sidecar_path}")
                  success_count += 1
            else:
                  logger.info(f"[DRY RUN] Would generate sidecar for: {output_file}")
                  success_count += 1
        except Exception as e:
            logger.error(f"Failed to generate sidecar for {output_file}: {e}")
            failed_count += 1

    return success_count, failed_count


def main():
    """Main entry point for provenance sidecar generation."""
    parser = argparse.ArgumentParser(
        description="Generate provenance sidecars for preprocessed fMRI files"
    )
    parser.add_argument(
        "--processed-dir",
        default="data/processed-fmri",
        help="Directory containing preprocessed files (default: data/processed-fmri)",
    )
    parser.add_argument(
        "--input-dir",
        default="data/raw-fmri",
        help="Base directory for input files (default: data/raw-fmri)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only log what would be done without writing files",
    )
    parser.add_argument(
        "--generate-manifest",
        action="store_true",
        help="Generate manifest file after creating sidecars",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Starting provenance sidecar generation")
    logger.info(f"Processed directory: {args.processed_dir}")
    logger.info(f"Input directory: {args.input_dir}")

    # Find preprocessed files
    files = find_preprocessed_files(args.processed_dir)

    if not files:
        logger.warning("No preprocessed files found. Exiting.")
        sys.exit(0)

    # Generate sidecars
    success_count, failed_count = generate_sidecars_for_files(
        files, base_input_dir=args.input_dir, dry_run=args.dry_run
    )

    logger.info(
        f"Sidecar generation complete: {success_count} successful, {failed_count} failed"
    )

    # Generate manifest if requested
    if args.generate_manifest and not args.dry_run:
        logger.info("Generating provenance manifest...")
        try:
            manifest_path = generate_provenance_manifest(
                output_dir=args.processed_dir
            )
            logger.info(f"Manifest generated: {manifest_path}")
        except Exception as e:
            logger.error(f"Failed to generate manifest: {e}")

    # Exit with error if any failures
    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()