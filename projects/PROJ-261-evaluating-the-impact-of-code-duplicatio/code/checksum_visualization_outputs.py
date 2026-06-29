"""
Checksum Computation for Visualization Outputs

This module computes and records checksums for all visualization outputs
(figures, plots) to ensure reproducibility and data integrity.

Task T044: Add checksum computation for visualization outputs and record
in artifact_hashes state manifest.

SC-006: Checksum tracking for all artifacts
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from checksum_manifest import (
    compute_file_checksum,
    load_manifest,
    save_manifest,
    record_artifact_checksums,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_ALGORITHM
)

# Setup module-level logger
logger = logging.getLogger(__name__)

# Visualization output directory
VISUALIZATION_DIR = Path("data/analysis/figures")

# Supported visualization file extensions
VISUALIZATION_EXTENSIONS = ['.png', '.pdf', '.svg', '.jpg', '.jpeg']

def find_visualization_outputs(
    base_dir: Path = VISUALIZATION_DIR,
    extensions: List[str] = None
) -> List[Path]:
    """
    Find all visualization output files in the specified directory.
    
    Args:
        base_dir: Base directory to search
        extensions: List of file extensions to include
    
    Returns:
        List of paths to visualization files
    """
    if extensions is None:
        extensions = VISUALIZATION_EXTENSIONS
    
    if not base_dir.exists():
        logger.warning(f"Visualization directory not found: {base_dir}")
        return []
    
    visualization_files = []
    
    for ext in extensions:
        files = list(base_dir.glob(f"*{ext}"))
        visualization_files.extend(files)
        
        # Also search in subdirectories
        files = list(base_dir.glob(f"**/*{ext}"))
        visualization_files.extend(files)
    
    # Remove duplicates and sort
    visualization_files = sorted(set(visualization_files))
    
    logger.info(f"Found {len(visualization_files)} visualization files")
    return visualization_files

def compute_visualization_checksums(
    visualization_paths: List[Path],
    algorithm: str = DEFAULT_ALGORITHM
) -> Dict[str, str]:
    """
    Compute checksums for all visualization files.
    
    Args:
        visualization_paths: List of visualization file paths
        algorithm: Hash algorithm to use
    
    Returns:
        Dict mapping file paths to checksums
    """
    checksums = {}
    
    for path in visualization_paths:
        try:
            checksum = compute_file_checksum(path, algorithm)
            checksums[str(path)] = checksum
            logger.info(f"Computed checksum for {path}: {checksum[:16]}...")
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Failed to compute checksum for {path}: {e}")
    
    return checksums

def record_visualization_checksums(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    visualization_dir: Path = VISUALIZATION_DIR,
    algorithm: str = DEFAULT_ALGORITHM
) -> Dict[str, Any]:
    """
    Find all visualization outputs, compute checksums, and record in manifest.
    
    This is the main entry point for T044.
    
    Args:
        manifest_path: Path to the checksum manifest
        visualization_dir: Directory containing visualization outputs
        algorithm: Hash algorithm to use
    
    Returns:
        Updated manifest dictionary
    """
    # Find all visualization outputs
    visualization_files = find_visualization_outputs(visualization_dir)
    
    if not visualization_files:
        logger.warning("No visualization files found to checksum")
        # Still update manifest to record that we checked
        manifest = load_manifest(manifest_path)
        if 'metadata' not in manifest:
            manifest['metadata'] = {}
        manifest['metadata']['last_visualization_check'] = datetime.utcnow().isoformat()
        manifest['metadata']['visualization_files_checked'] = 0
        save_manifest(manifest, manifest_path)
        return manifest
    
    # Compute checksums
    checksums = compute_visualization_checksums(visualization_files, algorithm)
    
    # Record in manifest
    manifest = load_manifest(manifest_path)
    
    if 'artifact_hashes' not in manifest:
        manifest['artifact_hashes'] = {}
    
    # Add visualization-specific entries with prefix
    for path, checksum in checksums.items():
        manifest['artifact_hashes'][path] = checksum
    
    # Add metadata about visualization checksums
    if 'metadata' not in manifest:
        manifest['metadata'] = {}
    manifest['metadata']['last_visualization_check'] = datetime.utcnow().isoformat()
    manifest['metadata']['visualization_files_checked'] = len(checksums)
    manifest['metadata']['visualization_algorithm'] = algorithm
    
    # Save updated manifest
    save_manifest(manifest, manifest_path)
    
    logger.info(f"Recorded checksums for {len(checksums)} visualization files")
    return manifest

def generate_visualization_checksum_report(
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    output_path: Optional[Path] = None
) -> str:
    """
    Generate a human-readable report of visualization checksums.
    
    Args:
        manifest_path: Path to the checksum manifest
        output_path: Optional path to write report (if None, returns string)
    
    Returns:
        Report as string
    """
    manifest = load_manifest(manifest_path)
    
    report_lines = [
        "=" * 70,
        "VISUALIZATION OUTPUT CHECKSUM REPORT",
        "=" * 70,
        f"Generated: {datetime.utcnow().isoformat()}",
        f"Manifest: {manifest_path}",
        "",
        "VISUALIZATION FILES:",
        "-" * 70,
    ]
    
    artifact_hashes = manifest.get('artifact_hashes', {})
    visualization_files = [
        (path, checksum) for path, checksum in artifact_hashes.items()
        if any(path.endswith(ext) for ext in VISUALIZATION_EXTENSIONS)
    ]
    
    if visualization_files:
        for path, checksum in sorted(visualization_files):
            report_lines.append(f"  {path}")
            report_lines.append(f"    Checksum ({manifest.get('metadata', {}).get('visualization_algorithm', DEFAULT_ALGORITHM)}): {checksum}")
            report_lines.append("")
    else:
        report_lines.append("  No visualization files found in manifest")
    
    # Add metadata section
    metadata = manifest.get('metadata', {})
    report_lines.extend([
        "",
        "METADATA:",
        "-" * 70,
        f"  Last visualization check: {metadata.get('last_visualization_check', 'N/A')}",
        f"  Files checked: {metadata.get('visualization_files_checked', 0)}",
        f"  Algorithm: {metadata.get('visualization_algorithm', DEFAULT_ALGORITHM)}",
        "",
        "=" * 70,
    ])
    
    report = "\n".join(report_lines)
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)
        logger.info(f"Wrote checksum report to {output_path}")
    
    return report

def main():
    """Command-line interface for visualization checksum operations."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Compute and record checksums for visualization outputs'
    )
    parser.add_argument(
        '--manifest',
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        help='Path to checksum manifest'
    )
    parser.add_argument(
        '--visualizations',
        type=Path,
        default=VISUALIZATION_DIR,
        help='Directory containing visualization outputs'
    )
    parser.add_argument(
        '--algorithm',
        type=str,
        default=DEFAULT_ALGORITHM,
        choices=['sha256', 'md5', 'sha1'],
        help='Hash algorithm to use'
    )
    parser.add_argument(
        '--report',
        type=Path,
        help='Generate checksum report to this file'
    )
    
    args = parser.parse_args()
    
    # Record visualization checksums
    manifest = record_visualization_checksums(
        manifest_path=args.manifest,
        visualization_dir=args.visualizations,
        algorithm=args.algorithm
    )
    
    print(f"Recorded checksums for visualization outputs")
    print(f"Manifest updated: {args.manifest}")
    
    # Generate report if requested
    if args.report:
        report = generate_visualization_checksum_report(args.manifest, args.report)
        print(f"Report generated: {args.report}")
    
    # Print summary
    artifact_hashes = manifest.get('artifact_hashes', {})
    visualization_count = sum(
        1 for path in artifact_hashes.keys()
        if any(path.endswith(ext) for ext in VISUALIZATION_EXTENSIONS)
    )
    print(f"Visualization files checksummed: {visualization_count}")

if __name__ == '__main__':
    main()
