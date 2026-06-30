"""
Checksum computation for visualization outputs.

This module computes SHA-256 checksums for all visualization files
in the data/analysis/figures/ directory and records them in the
artifact_hashes state manifest (checksum_manifest.py).

Per Constitution Principle III (Data Hygiene) and SC-006 (checksum tracking).
"""
import logging
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from checksum_manifest import (
    setup_logging as manifest_setup_logging,
    compute_file_checksum,
    load_manifest,
    save_manifest,
    record_artifact_checksums,
)
from config import (
    get_checksum_algorithm,
    get_figure_format,
)

# Configure module-level logging
logger = logging.getLogger(__name__)

def setup_logging() -> logging.Logger:
    """Setup logging for this module."""
    return manifest_setup_logging("checksum_visualization_outputs")

def find_visualization_outputs(
    figures_dir: Optional[Path] = None,
) -> List[Path]:
    """
    Find all visualization output files in the figures directory.
    
    Args:
        figures_dir: Path to figures directory. Defaults to data/analysis/figures/
    
    Returns:
        List of Path objects for visualization files (PNG and PDF)
    """
    if figures_dir is None:
        figures_dir = Path("data/analysis/figures")
    
    if not figures_dir.exists():
        logger.warning(f"Figures directory does not exist: {figures_dir}")
        return []
    
    # Find all PNG and PDF files
    figure_files = []
    for ext in ["png", "pdf"]:
        figure_files.extend(figures_dir.glob(f"*.{ext}"))
    
    logger.info(f"Found {len(figure_files)} visualization files in {figures_dir}")
    return figure_files

def compute_visualization_checksums(
    figure_files: List[Path],
    algorithm: Optional[str] = None,
) -> Dict[str, str]:
    """
    Compute checksums for all visualization files.
    
    Args:
        figure_files: List of Path objects for visualization files
        algorithm: Hash algorithm to use. Defaults to config value (sha256)
    
    Returns:
        Dictionary mapping file paths (as strings) to checksums
    """
    if algorithm is None:
        algorithm = get_checksum_algorithm()
    
    checksums = {}
    for figure_file in figure_files:
        try:
            checksum = compute_file_checksum(figure_file, algorithm)
            checksums[str(figure_file)] = checksum
            logger.debug(f"Computed checksum for {figure_file}: {checksum[:16]}...")
        except Exception as e:
            logger.error(f"Failed to compute checksum for {figure_file}: {e}")
    
    return checksums

def record_visualization_checksums(
    checksums: Dict[str, str],
    manifest_path: Optional[Path] = None,
) -> bool:
    """
    Record visualization checksums in the artifact_hashes state manifest.
    
    Args:
        checksums: Dictionary mapping file paths to checksums
        manifest_path: Path to manifest file. Defaults to code/checksum_manifest.json
    
    Returns:
        True if successfully recorded, False otherwise
    """
    if manifest_path is None:
        manifest_path = Path("code/checksum_manifest.json")
    
    try:
        # Load existing manifest
        manifest = load_manifest(manifest_path)
        
        # Add visualization checksums to artifact_hashes
        if "artifact_hashes" not in manifest:
            manifest["artifact_hashes"] = {}
        
        # Record each checksum with metadata
        for file_path, checksum in checksums.items():
            key = f"visualization:{file_path}"
            manifest["artifact_hashes"][key] = {
                "checksum": checksum,
                "algorithm": get_checksum_algorithm(),
                "recorded_at": datetime.utcnow().isoformat(),
                "type": "visualization_output",
            }
        
        # Save updated manifest
        save_manifest(manifest, manifest_path)
        logger.info(f"Recorded {len(checksums)} visualization checksums in manifest")
        return True
        
    except Exception as e:
        logger.error(f"Failed to record visualization checksums in manifest: {e}")
        return False

def generate_visualization_checksum_report(
    checksums: Dict[str, str],
    output_path: Optional[Path] = None,
) -> Path:
    """
    Generate a checksum report for visualization outputs.
    
    Args:
        checksums: Dictionary mapping file paths to checksums
        output_path: Path for report file. Defaults to data/analysis/visualization_checksums.txt
    
    Returns:
        Path to the generated report file
    """
    if output_path is None:
        output_path = Path("data/analysis/visualization_checksums.txt")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        f.write("=" * 60 + "\n")
        f.write("Visualization Output Checksum Report\n")
        f.write(f"Generated: {datetime.utcnow().isoformat()}\n")
        f.write(f"Algorithm: {get_checksum_algorithm()}\n")
        f.write("=" * 60 + "\n\n")
        
        if checksums:
            for file_path, checksum in checksums.items():
                f.write(f"{file_path}: {checksum}\n")
        else:
            f.write("No visualization files found.\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"Total files: {len(checksums)}\n")
        f.write("=" * 60 + "\n")
    
    logger.info(f"Generated checksum report at {output_path}")
    return output_path

def main() -> int:
    """
    Main entry point for checksum computation of visualization outputs.
    
    Returns:
        0 on success, 1 on failure
    """
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Visualization Output Checksum Computation")
    logger.info("=" * 60)
    
    try:
        # Find visualization outputs
        figure_files = find_visualization_outputs()
        
        if not figure_files:
            logger.warning("No visualization files found. Creating empty manifest entry.")
            # Still create a report showing no files
            generate_visualization_checksum_report({}, Path("data/analysis/visualization_checksums.txt"))
            # Record empty checksums in manifest
            record_visualization_checksums({})
            return 0
        
        # Compute checksums
        checksums = compute_visualization_checksums(figure_files)
        
        if not checksums:
            logger.error("Failed to compute checksums for any visualization files.")
            return 1
        
        # Generate report
        generate_visualization_checksum_report(checksums)
        
        # Record in manifest
        if not record_visualization_checksums(checksums):
            logger.error("Failed to record checksums in manifest.")
            return 1
        
        logger.info("Visualization checksum computation completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error during checksum computation: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
