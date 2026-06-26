"""
Checksum manifest infrastructure for tracking artifact hashes.

This module provides functionality to compute and record checksums
for all output files and intermediate files/logs in the pipeline.

Per Constitution Principle V (Versioning Discipline), all artifacts
must have traceable checksums for reproducibility verification.
"""
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Default manifest path
DEFAULT_MANIFEST_PATH = Path("projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/analysis/artifact_manifest.json")

# Files that should be checksummed
ARTIFACT_FILES = [
    # Output files
    Path("projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/processed/clone_metrics.csv"),
    Path("projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/processed/perplexity_scores.csv"),
    # Intermediate files and logs
    Path("projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/parse_failures.csv"),
    Path("projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/raw/github-code-sample.csv"),
    # Analysis outputs
    Path("projects/PROJ-261-evaluating-the-impact-of-code-duplication/data/analysis/correlation_results.csv"),
]

def setup_logging() -> logging.Logger:
    """Setup logging for checksum operations."""
    logger = logging.getLogger("checksum_manifest")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> Optional[str]:
    """
    Compute checksum for a single file.
    
    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (default: sha256)
    
    Returns:
        Hex digest string or None if file doesn't exist
    """
    if not file_path.exists():
        logger = setup_logging()
        logger.warning(f"File does not exist, skipping checksum: {file_path}")
        return None
    
    try:
        hasher = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger = setup_logging()
        logger.error(f"Error computing checksum for {file_path}: {e}")
        return None

def compute_all_artifact_checksums() -> Dict[str, str]:
    """
    Compute checksums for all tracked artifact files.
    
    Returns:
        Dictionary mapping file paths (as strings) to their checksums
    """
    logger = setup_logging()
    logger.info("Computing checksums for all artifact files...")
    
    checksums = {}
    for file_path in ARTIFACT_FILES:
        checksum = compute_file_checksum(file_path)
        if checksum:
            checksums[str(file_path)] = checksum
            logger.debug(f"  {file_path}: {checksum[:16]}...")
    
    logger.info(f"Computed {len(checksums)} artifact checksums")
    return checksums

def load_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load existing manifest from disk.
    
    Args:
        manifest_path: Path to manifest file (uses default if None)
    
    Returns:
        Manifest dictionary or empty dict if not found
    """
    if manifest_path is None:
        manifest_path = DEFAULT_MANIFEST_PATH
    
    if not manifest_path.exists():
        return {"artifact_hashes": {}, "metadata": {}}
    
    try:
        with open(manifest_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger = setup_logging()
        logger.error(f"Error loading manifest: {e}")
        return {"artifact_hashes": {}, "metadata": {}}

def save_manifest(manifest: Dict[str, Any], manifest_path: Optional[Path] = None) -> None:
    """
    Save manifest to disk.
    
    Args:
        manifest: Manifest dictionary to save
        manifest_path: Path to manifest file (uses default if None)
    """
    if manifest_path is None:
        manifest_path = DEFAULT_MANIFEST_PATH
    
    # Ensure parent directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger = setup_logging()
    logger.info(f"Manifest saved to {manifest_path}")

def record_artifact_checksums(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Compute and record artifact checksums in the manifest.
    
    This function:
    1. Loads the existing manifest
    2. Computes checksums for all tracked artifact files
    3. Updates the artifact_hashes dictionary
    4. Updates metadata with timestamp
    5. Saves the updated manifest
    
    Args:
        manifest_path: Path to manifest file (uses default if None)
    
    Returns:
        Updated manifest dictionary
    """
    logger = setup_logging()
    logger.info("Recording artifact checksums in manifest...")
    
    # Load existing manifest
    manifest = load_manifest(manifest_path)
    
    # Compute fresh checksums
    checksums = compute_all_artifact_checksums()
    
    # Update artifact_hashes
    manifest["artifact_hashes"] = checksums
    
    # Update metadata
    manifest["metadata"] = {
        "last_updated": datetime.utcnow().isoformat(),
        "algorithm": "sha256",
        "artifact_count": len(checksums),
        "manifest_version": "1.0"
    }
    
    # Save updated manifest
    save_manifest(manifest, manifest_path)
    
    logger.info(f"Recorded {len(checksums)} artifact checksums")
    return manifest

def verify_artifact_checksums(manifest_path: Optional[Path] = None) -> Dict[str, bool]:
    """
    Verify current file checksums against recorded manifest values.
    
    Args:
        manifest_path: Path to manifest file (uses default if None)
    
    Returns:
        Dictionary mapping file paths to verification status (True/False)
    """
    logger = setup_logging()
    logger.info("Verifying artifact checksums...")
    
    manifest = load_manifest(manifest_path)
    recorded_hashes = manifest.get("artifact_hashes", {})
    
    verification_results = {}
    for file_path_str, recorded_hash in recorded_hashes.items():
        file_path = Path(file_path_str)
        current_hash = compute_file_checksum(file_path)
        
        if current_hash is None:
            verification_results[file_path_str] = False
            logger.warning(f"File not found for verification: {file_path_str}")
        elif current_hash == recorded_hash:
            verification_results[file_path_str] = True
            logger.debug(f"Checksum verified: {file_path_str}")
        else:
            verification_results[file_path_str] = False
            logger.warning(f"Checksum mismatch for {file_path_str}")
            logger.warning(f"  Recorded: {recorded_hash}")
            logger.warning(f"  Current:  {current_hash}")
    
    logger.info(f"Verified {len(verification_results)} artifacts")
    return verification_results

def get_artifact_hashes() -> Dict[str, str]:
    """
    Get current artifact hashes from the manifest.
    
    Returns:
        Dictionary mapping file paths to their checksums
    """
    manifest = load_manifest()
    return manifest.get("artifact_hashes", {})

def add_custom_artifact(file_path: Path, manifest_path: Optional[Path] = None) -> None:
    """
    Add a custom artifact to the tracking list and compute its checksum.
    
    Args:
        file_path: Path to the artifact file
        manifest_path: Path to manifest file (uses default if None)
    """
    global ARTIFACT_FILES
    
    if file_path not in ARTIFACT_FILES:
        ARTIFACT_FILES.append(file_path)
    
    # Record the checksum
    record_artifact_checksums(manifest_path)

def main() -> None:
    """Main entry point for checksum manifest operations."""
    logger = setup_logging()
    logger.info("Checksum Manifest Utility")
    logger.info("=" * 50)
    
    # Record all artifact checksums
    manifest = record_artifact_checksums()
    
    # Display summary
    logger.info(f"Total artifacts tracked: {manifest['metadata']['artifact_count']}")
    logger.info(f"Last updated: {manifest['metadata']['last_updated']}")
    logger.info("Artifact checksums:")
    for path, checksum in manifest["artifact_hashes"].items():
        logger.info(f"  {path}: {checksum[:16]}...")

if __name__ == "__main__":
    main()