"""
Checksum Computation for Visualization Outputs

This script computes and records checksums for all visualization outputs
(figures) in the project's analysis directory to ensure data integrity
and reproducibility per Constitution Principle V (Versioning Discipline).

This task (T044) specifically addresses checksum tracking for US3
visualization outputs as required by SC-006.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Import from local modules
from checksum_manifest import (
    compute_file_checksum,
    compute_all_artifact_checksums,
    load_manifest,
    save_manifest,
    record_artifact_checksums,
    get_artifact_hashes,
    setup_logging,
    DEFAULT_MANIFEST_PATH
)

# Configure module logging
logger = logging.getLogger(__name__)

# Visualization output directories
VISUALIZATION_OUTPUT_DIRS = [
    Path("data/analysis/figures"),
    Path("data/analysis"),
]

# Supported figure formats
SUPPORTED_FORMATS = [".png", ".pdf", ".svg", ".jpg", ".jpeg"]


def find_visualization_outputs(
    base_dirs: Optional[List[Path]] = None
) -> List[Path]:
    """
    Find all visualization output files in specified directories.

    Args:
        base_dirs: List of directories to search (defaults to VISUALIZATION_OUTPUT_DIRS)

    Returns:
        List of Path objects for all figure files found
    """
    if base_dirs is None:
        base_dirs = VISUALIZATION_OUTPUT_DIRS

    figure_files = []
    for base_dir in base_dirs:
        if not base_dir.exists():
            logger.warning(f"Visualization directory does not exist: {base_dir}")
            continue

        for ext in SUPPORTED_FORMATS:
            # Use rglob for recursive search
            for figure_file in base_dir.rglob(f"*{ext}"):
                if figure_file.is_file():
                    figure_files.append(figure_file)

        # Also check for common figure naming patterns
        for pattern in ["*.png", "*.pdf"]:
            for figure_file in base_dir.glob(pattern):
                if figure_file not in figure_files:
                    figure_files.append(figure_file)

    # Remove duplicates and sort
    figure_files = sorted(set(figure_files))
    logger.info(f"Found {len(figure_files)} visualization output(s)")
    return figure_files


def compute_visualization_checksums(
    figure_files: List[Path],
    algorithm: str = "sha256"
) -> Dict[str, str]:
    """
    Compute checksums for all visualization outputs.

    Args:
        figure_files: List of figure file paths
        algorithm: Hash algorithm to use

    Returns:
        Dictionary mapping file paths to checksums
    """
    checksums = {}
    for figure_file in figure_files:
        checksum = compute_file_checksum(figure_file, algorithm)
        if checksum:
            checksums[str(figure_file)] = checksum
            logger.debug(f"Computed checksum for {figure_file}: {checksum[:16]}...")
        else:
            logger.warning(f"Failed to compute checksum for {figure_file}")

    return checksums


def record_visualization_checksums(
    manifest_path: Path,
    checksums: Dict[str, str],
    category: str = "visualizations"
) -> bool:
    """
    Record visualization checksums in the manifest.

    Args:
        manifest_path: Path to manifest file
        checksums: Dictionary of file paths to checksums
        category: Category label for visualization artifacts

    Returns:
        True if successful, False otherwise
    """
    if not checksums:
        logger.warning("No checksums to record")
        return False

    try:
        manifest = record_artifact_checksums(
            manifest_path,
            checksums,
            category
        )
        logger.info(f"Recorded {len(checksums)} visualization checksum(s) in manifest")
        return True
    except Exception as e:
        logger.error(f"Failed to record visualization checksums: {e}")
        return False


def generate_visualization_checksum_report(
    checksums: Dict[str, str],
    output_path: Optional[Path] = None
) -> str:
    """
    Generate a human-readable checksum report for visualization outputs.

    Args:
        checksums: Dictionary of file paths to checksums
        output_path: Optional path to save report

    Returns:
        Report string
    """
    lines = [
        "=" * 60,
        "VISUALIZATION OUTPUT CHECKSUM REPORT",
        f"Generated: {datetime.now().isoformat()}",
        f"Total outputs: {len(checksums)}",
        "=" * 60,
        ""
    ]

    for path, checksum in sorted(checksums.items()):
        lines.append(f"File: {path}")
        lines.append(f"  SHA256: {checksum}")
        lines.append("")

    report = "\n".join(lines)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)
        logger.info(f"Saved checksum report to {output_path}")

    return report


def main():
    """Main entry point for visualization checksum computation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute and record checksums for visualization outputs"
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help="Path to checksum manifest file"
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        default="sha256",
        choices=["sha256", "md5", "sha1"],
        help="Hash algorithm to use"
    )
    parser.add_argument(
        "--category",
        type=str,
        default="visualizations",
        help="Category label for visualization artifacts"
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("data/analysis/visualization_checksum_report.txt"),
        help="Path to save checksum report"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute checksums without recording to manifest"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    logger.info("Starting visualization output checksum computation")
    logger.info(f"Manifest path: {args.manifest_path}")
    logger.info(f"Algorithm: {args.algorithm}")

    # Find all visualization outputs
    figure_files = find_visualization_outputs()

    if not figure_files:
        logger.warning("No visualization outputs found to checksum")
        # Still create/update manifest to record that we checked
        manifest = load_manifest(args.manifest_path)
        if "artifact_hashes" not in manifest:
            manifest["artifact_hashes"] = {}
        manifest["artifact_hashes"][args.category] = {
            "_metadata": {
                "checked_at": datetime.now().isoformat(),
                "status": "no_outputs_found",
                "message": "No visualization outputs exist yet"
            }
        }
        save_manifest(args.manifest_path, manifest)
        return 0

    # Compute checksums
    checksums = compute_visualization_checksums(figure_files, args.algorithm)

    if not checksums:
        logger.error("Failed to compute any checksums")
        return 1

    # Generate report
    report = generate_visualization_checksum_report(checksums, args.report_path)
    print(report)

    # Record in manifest (unless dry-run)
    if not args.dry_run:
        success = record_visualization_checksums(
            args.manifest_path,
            checksums,
            args.category
        )
        if not success:
            logger.error("Failed to record checksums in manifest")
            return 1

    logger.info("Visualization checksum computation completed successfully")
    return 0


if __name__ == "__main__":
    exit(main())