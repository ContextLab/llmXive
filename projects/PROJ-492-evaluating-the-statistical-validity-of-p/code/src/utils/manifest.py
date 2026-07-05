"""
Manifest generation utility for FR-024.
Generates a manifest.json file containing SHA256 hashes for all specified artifacts.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from code.src.utils.logger import get_default_logger, AuditLogger

logger = get_default_logger(__name__)


def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def generate_manifest(
    artifact_paths: List[Path],
    output_path: Path,
    base_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generates a manifest.json file with SHA256 hashes for the given artifact paths.
    
    Args:
        artifact_paths: List of Path objects pointing to files to include in the manifest.
        output_path: Path where the manifest.json file will be written.
        base_dir: Optional base directory to compute relative paths from. 
                  If None, absolute paths are used.
                  
    Returns:
        The manifest dictionary that was written.
        
    Raises:
        FileNotFoundError: If any artifact in artifact_paths does not exist.
        IOError: If the manifest cannot be written.
    """
    if base_dir is None:
        base_dir = Path.cwd()
        
    manifest = {
        "version": "1.0",
        "generated_at": None, # Will be set by caller if needed, or left for metadata
        "artifacts": {}
    }
    
    missing_files = []
    
    for path in artifact_paths:
        if not path.exists():
            missing_files.append(str(path))
            continue
        
        # Determine relative path
        try:
            rel_path = str(path.relative_to(base_dir))
        except ValueError:
            # If path is not relative to base_dir, use absolute path string
            rel_path = str(path.absolute())
            
        try:
            file_hash = compute_sha256(path)
            manifest["artifacts"][rel_path] = {
                "sha256": file_hash,
                "size_bytes": path.stat().st_size
            }
            logger.debug(f"Added to manifest: {rel_path} (hash: {file_hash[:16]}...)")
        except Exception as e:
            logger.error(f"Failed to compute hash for {path}: {e}")
            raise
            
    if missing_files:
        logger.error(f"Missing files for manifest: {missing_files}")
        raise FileNotFoundError(f"Missing files: {missing_files}")
        
    # Write manifest
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest written to {output_path} with {len(manifest['artifacts'])} artifacts.")
    except IOError as e:
        raise IOError(f"Failed to write manifest to {output_path}: {e}")
        
    return manifest


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Loads a manifest.json file.
    
    Args:
        manifest_path: Path to the manifest file.
        
    Returns:
        The manifest dictionary.
        
    Raises:
        FileNotFoundError: If the manifest file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_manifest(
    manifest_path: Path,
    base_dir: Optional[Path] = None
) -> bool:
    """
    Verifies that the files listed in the manifest exist and their hashes match.
    
    Args:
        manifest_path: Path to the manifest file.
        base_dir: Base directory for relative path resolution. Defaults to manifest's parent.
                 
    Returns:
        True if all files match, False otherwise.
    """
    if base_dir is None:
        base_dir = manifest_path.parent
        
    manifest = load_manifest(manifest_path)
    all_valid = True
    
    for rel_path, info in manifest.get("artifacts", {}).items():
        expected_hash = info.get("sha256")
        file_path = base_dir / rel_path
        
        if not file_path.exists():
            logger.error(f"Verification failed: File not found {file_path}")
            all_valid = False
            continue
            
        actual_hash = compute_sha256(file_path)
        
        if actual_hash != expected_hash:
            logger.error(
                f"Verification failed: Hash mismatch for {file_path}. "
                f"Expected: {expected_hash}, Actual: {actual_hash}"
            )
            all_valid = False
        else:
            logger.debug(f"Verification passed: {file_path}")
            
    return all_valid


def main():
    """
    CLI entry point for generating a manifest.
    Usage: python -m code.src.utils.manifest --output output/manifest.json --files data/... output/...
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate manifest.json with SHA256 hashes")
    parser.add_argument("--output", type=str, required=True, help="Path to output manifest.json")
    parser.add_argument("--files", nargs="+", type=str, required=True, help="List of file paths to include")
    parser.add_argument("--base-dir", type=str, default=None, help="Base directory for relative paths")
    
    args = parser.parse_args()
    
    artifact_paths = [Path(p) for p in args.files]
    output_path = Path(args.output)
    base_dir = Path(args.base_dir) if args.base_dir else None
    
    try:
        manifest = generate_manifest(artifact_paths, output_path, base_dir)
        print(f"Manifest generated successfully at {output_path}")
        print(f"Total artifacts: {len(manifest['artifacts'])}")
    except Exception as e:
        logger.error(f"Failed to generate manifest: {e}")
        raise


if __name__ == "__main__":
    main()
