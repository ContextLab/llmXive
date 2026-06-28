"""
Checksum computation for visualization outputs.

This script computes SHA-256 checksums for all visualization files
generated in data/analysis/figures/ and records them in the artifact_hashes
state manifest.

Implements SC-006 (checksum tracking) for visualization outputs.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from checksum_manifest import (
    compute_file_checksum,
    record_artifact_checksums,
    save_manifest,
    load_manifest,
    setup_logging,
)
from config import get_checksum_algorithm, get_figure_format


def find_visualization_outputs(figures_dir: Path) -> List[Path]:
    """
    Find all visualization output files in the figures directory.

    Args:
        figures_dir: Path to the figures directory

    Returns:
        List of paths to visualization files (PNG and PDF)
    """
    if not figures_dir.exists():
        logging.warning(f"Figures directory does not exist: {figures_dir}")
        return []

    # Get figure formats from config
    formats = get_figure_format()
    if isinstance(formats, str):
        formats = [formats]

    # Build file extensions list
    extensions = []
    for fmt in formats:
        ext = fmt.lower()
        if ext in ["png", "pdf"]:
            extensions.append(f".{ext}")
        elif ext.startswith("."):
            extensions.append(ext)
        else:
            extensions.append(f".{ext}")

    # Find all matching files
    visualization_files = []
    for ext in extensions:
      visualization_files.extend(figures_dir.glob(f"*{ext}"))

    # Also check for common visualization naming patterns
    common_patterns = [
        "scatter_plot.png",
        "scatter_plot.pdf",
        "clone_density_perplexity.png",
        "clone_density_perplexity.pdf",
        "clone_density_accuracy.png",
        "clone_density_accuracy.pdf",
        "sensitivity_analysis.png",
        "sensitivity_analysis.pdf",
        "correlation_scatter.png",
        "correlation_scatter.pdf",
    ]

    for pattern in common_patterns:
        file_path = figures_dir / pattern
        if file_path.exists() and file_path not in visualization_files:
            visualization_files.append(file_path)

    return sorted(set(visualization_files))


def compute_visualization_checksums(
    figures_dir: Path,
    checksum_algorithm: str = "sha256",
) -> List[Tuple[str, str]]:
    """
    Compute checksums for all visualization files.

    Args:
        figures_dir: Path to the figures directory
        checksum_algorithm: Algorithm to use (default: sha256)

    Returns:
        List of tuples (relative_path, checksum)
    """
    visualization_files = find_visualization_outputs(figures_dir)

    if not visualization_files:
        logging.warning(f"No visualization files found in {figures_dir}")
        return []

    checksums = []
    for file_path in visualization_files:
        try:
            checksum = compute_file_checksum(file_path, algorithm=checksum_algorithm)
            relative_path = str(file_path.relative_to(figures_dir.parent.parent))
            checksums.append((relative_path, checksum))
            logging.info(f"Computed checksum for {relative_path}: {checksum[:16]}...")
        except Exception as e:
            logging.error(f"Failed to compute checksum for {file_path}: {e}")

    return checksums


def record_visualization_checksums(
    figures_dir: Path,
    manifest_path: Path,
    checksum_algorithm: str = "sha256",
) -> bool:
    """
    Compute and record visualization checksums in the manifest.

    Args:
        figures_dir: Path to the figures directory
        manifest_path: Path to the manifest file
        checksum_algorithm: Algorithm to use

    Returns:
        True if successful, False otherwise
    """
    # Compute checksums
    checksums = compute_visualization_checksums(figures_dir, checksum_algorithm)

    if not checksums:
        logging.warning("No visualization checksums to record")
        return False

    # Load existing manifest
    manifest = load_manifest(manifest_path)

    # Record checksums with metadata
    record_data = {
        "artifact_type": "visualization",
        "source_directory": str(figures_dir),
        "checksum_algorithm": checksum_algorithm,
        "computed_at": datetime.utcnow().isoformat() + "Z",
        "artifacts": {
            rel_path: {
                "checksum": checksum,
                "algorithm": checksum_algorithm,
                "recorded_at": datetime.utcnow().isoformat() + "Z",
            }
            for rel_path, checksum in checksums
        },
    }

    # Record in manifest
    record_artifact_checksums(manifest, "visualizations", record_data)

    # Save updated manifest
    save_manifest(manifest, manifest_path)

    logging.info(
        f"Recorded {len(checksums)} visualization checksums in manifest"
    )
    return True


def main() -> int:
    """
    Main entry point for visualization checksum computation.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting visualization checksum computation")

    # Get paths from config
    project_root = Path(__file__).parent.parent
    figures_dir = project_root / "data" / "analysis" / "figures"
    manifest_path = project_root / "data" / "artifact_hashes.json"
    checksum_algorithm = get_checksum_algorithm()

    logger.info(f"Figures directory: {figures_dir}")
    logger.info(f"Manifest path: {manifest_path}")
    logger.info(f"Checksum algorithm: {checksum_algorithm}")

    # Check if figures directory exists
    if not figures_dir.exists():
        logger.error(f"Figures directory does not exist: {figures_dir}")
        logger.error("Run T041/T042 first to generate visualization outputs")
        return 1

    # Check if manifest exists
    if not manifest_path.exists():
        logger.warning(f"Manifest does not exist: {manifest_path}")
        logger.warning("Creating new manifest")
        # Initialize empty manifest
        manifest = {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "artifact_hashes": {},
        }
        save_manifest(manifest, manifest_path)

    # Compute and record checksums
    success = record_visualization_checksums(
        figures_dir,
        manifest_path,
        checksum_algorithm,
    )

    if success:
        logger.info("Visualization checksum computation completed successfully")
        return 0
    else:
        logger.error("Visualization checksum computation failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())