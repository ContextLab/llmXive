"""
Archive Pipeline for T005d: Archive Raw Data & Upload to CI.

This module implements the logic to copy raw data files from the
eBird and Daymet download directories into a central archive directory,
compute checksums for provenance, and prepare the artifacts for CI upload.
"""

import logging
import sys
import shutil
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List

# Configure logging
logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def archive_data(
    source_dirs: List[Path],
    archive_dir: Path,
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Copy files from source directories to the archive directory.

    Args:
        source_dirs: List of source directories containing raw data.
        archive_dir: Destination directory for the archive.
        overwrite: If True, overwrite existing files in archive.

    Returns:
        Dictionary containing archive statistics and file manifest.
    """
    if not archive_dir.exists():
        archive_dir.mkdir(parents=True)
        logger.info(f"Created archive directory: {archive_dir}")

    manifest = {
        "source_dirs": [str(p) for p in source_dirs],
        "archive_dir": str(archive_dir),
        "files": [],
        "total_files": 0,
        "total_size_bytes": 0
    }

    for source_dir in source_dirs:
        if not source_dir.exists():
            logger.warning(f"Source directory does not exist: {source_dir}")
            continue

        # Create corresponding subdirectory in archive
        subdir_name = source_dir.name
        target_subdir = archive_dir / subdir_name
        target_subdir.mkdir(parents=True, exist_ok=True)

        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(source_dir)
                target_path = target_subdir / relative_path

                # Ensure parent directories exist
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # Check if file exists and overwrite policy
                if target_path.exists() and not overwrite:
                    logger.info(f"Skipping existing file: {target_path}")
                    continue

                try:
                    shutil.copy2(file_path, target_path)
                    file_size = file_path.stat().st_size
                    checksum = compute_sha256(file_path)

                    manifest["files"].append({
                        "source": str(file_path),
                        "archive": str(target_path),
                        "size_bytes": file_size,
                        "sha256": checksum
                    })
                    manifest["total_files"] += 1
                    manifest["total_size_bytes"] += file_size

                    logger.info(f"Archived: {file_path} -> {target_path}")
                except Exception as e:
                    logger.error(f"Failed to archive {file_path}: {e}")
                    raise

    return manifest

def verify_archive_integrity(
    archive_dir: Path,
    manifest_path: Path
) -> bool:
    """
    Verify the integrity of the archived files against the manifest.

    Args:
        archive_dir: The archive directory to verify.
        manifest_path: Path to the JSON manifest file.

    Returns:
        True if all files match their checksums, False otherwise.
    """
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        return False

    try:
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest: {e}")
        return False

    all_valid = True
    for file_info in manifest.get("files", []):
        archive_path = Path(file_info["archive"])
        expected_checksum = file_info["sha256"]

        if not archive_path.exists():
            logger.error(f"Missing archived file: {archive_path}")
            all_valid = False
            continue

        actual_checksum = compute_sha256(archive_path)
        if actual_checksum != expected_checksum:
            logger.error(
                f"Checksum mismatch for {archive_path}: "
                f"expected {expected_checksum}, got {actual_checksum}"
            )
            all_valid = False
        else:
            logger.debug(f"Verified: {archive_path}")

    return all_valid

def generate_checksum_manifest(
    manifest: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write the archive manifest to a JSON file.

    Args:
        manifest: The archive manifest dictionary.
        output_path: Path to write the manifest JSON.
    """
    with open(output_path, "w") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest written to: {output_path}")

def run_archive_pipeline(
    ebird_source: Path,
    daymet_source: Path,
    archive_dir: Path,
    manifest_output: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Run the full archive pipeline for T005d.

    Args:
        ebird_source: Path to eBird raw data directory.
        daymet_source: Path to Daymet raw data directory.
        archive_dir: Path to the archive destination.
        manifest_output: Optional path for the manifest file.

    Returns:
        The archive manifest dictionary.
    """
    source_dirs = [ebird_source, daymet_source]
    
    logger.info(f"Starting archive pipeline. Sources: {source_dirs}")
    logger.info(f"Archive destination: {archive_dir}")

    # Archive the data
    manifest = archive_data(source_dirs, archive_dir, overwrite=False)

    # Generate manifest if output path provided
    if manifest_output:
        generate_checksum_manifest(manifest, manifest_output)

    logger.info(
        f"Archive pipeline complete. "
        f"Total files: {manifest['total_files']}, "
        f"Total size: {manifest['total_size_bytes']} bytes"
    )

    return manifest

def main():
    """Main entry point for the archive pipeline."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Define paths based on project structure
    project_root = Path(__file__).resolve().parent.parent.parent
    ebird_source = project_root / "data" / "raw" / "ebird_sample"
    daymet_source = project_root / "data" / "raw" / "daymet"
    archive_dir = project_root / "data" / "raw" / "archive"
    manifest_output = archive_dir / "archive_manifest.json"

    # Verify source directories exist
    if not ebird_source.exists():
        logger.error(f"eBird source directory not found: {ebird_source}")
        logger.error("Please ensure T005b has completed successfully.")
        sys.exit(1)

    if not daymet_source.exists():
        logger.error(f"Daymet source directory not found: {daymet_source}")
        logger.error("Please ensure T005c1 has completed successfully.")
        sys.exit(1)

    try:
        manifest = run_archive_pipeline(
            ebird_source=ebird_source,
            daymet_source=daymet_source,
            archive_dir=archive_dir,
            manifest_output=manifest_output
        )
        logger.info("Archive pipeline executed successfully.")
        logger.info(f"Manifest saved to: {manifest_output}")
        
        # In a real CI environment, the next step would be to upload
        # the archive_dir to CI artifacts. This is typically handled
        # by CI configuration (e.g., GitHub Actions, GitLab CI).
        logger.info(
            "To upload to CI artifacts, configure your CI pipeline "
            "to upload the contents of: " + str(archive_dir)
        )

    except Exception as e:
        logger.error(f"Archive pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
