"""
Utility to update state/manifest.yaml with final artifact checksums.
This script scans the data/ directory for all generated artifacts,
calculates their SHA-256 checksums, and updates the manifest.
"""
import hashlib
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import existing utilities from the project
from utils.data_manifest import calculate_file_checksum, load_manifest, save_manifest
from utils.logging_config import get_logger

# Configure logging
logger = get_logger(__name__)

def scan_artifacts(base_dir: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Recursively scan a directory for files with specified extensions.
    
    Args:
        base_dir: Root directory to scan
        extensions: List of file extensions to include (e.g., ['.json', '.csv'])
                   If None, includes all files
    
    Returns:
        List of Path objects for matching files
    """
    artifacts = []
    for root, dirs, files in os.walk(base_dir):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            file_path = Path(root) / file
            if extensions:
                if any(file_path.suffix == ext for ext in extensions):
                    artifacts.append(file_path)
            else:
                artifacts.append(file_path)
    
    return sorted(artifacts)

def update_manifest_with_checksums(manifest_path: Path, data_dir: Path) -> Dict[str, Any]:
    """
    Scan data directory, calculate checksums for all artifacts, and update manifest.
    
    Args:
        manifest_path: Path to the manifest.yaml file
        data_dir: Path to the data directory to scan
    
    Returns:
        Updated manifest dictionary
    """
    # Load existing manifest
    manifest = load_manifest(manifest_path)
    
    # Scan for artifacts
    logger.info(f"Scanning {data_dir} for artifacts...")
    artifacts = scan_artifacts(data_dir)
    
    logger.info(f"Found {len(artifacts)} artifacts to checksum")
    
    updated_files = 0
    for artifact_path in artifacts:
        # Calculate relative path from data directory
        rel_path = artifact_path.relative_to(data_dir)
        
        # Calculate checksum
        checksum = calculate_file_checksum(artifact_path)
        
        # Update manifest entry
        if 'files' not in manifest:
            manifest['files'] = {}
        
        manifest['files'][str(rel_path)] = {
            'checksum': checksum,
            'size_bytes': artifact_path.stat().st_size,
            'updated_at': artifact_path.stat().st_mtime
        }
        updated_files += 1
        logger.debug(f"Checksummed: {rel_path} -> {checksum[:16]}...")
    
    # Update manifest metadata
    manifest['metadata'] = manifest.get('metadata', {})
    manifest['metadata']['last_updated'] = str(Path(artifact_path).stat().st_mtime if artifacts else 0)
    manifest['metadata']['total_files'] = updated_files
    manifest['metadata']['scan_directory'] = str(data_dir)
    
    # Save updated manifest
    save_manifest(manifest_path, manifest)
    
    logger.info(f"Updated manifest with {updated_files} artifact checksums")
    return manifest

def main():
    """
    Main entry point for updating the manifest with checksums.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    manifest_path = project_root / "state" / "manifest.yaml"
    data_dir = project_root / "data"
    
    # Verify paths exist
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        logger.error("Please ensure state/manifest.yaml exists before running this script.")
        return 1
    
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        logger.error("Please ensure data/ directory exists before running this script.")
        return 1
    
    try:
        manifest = update_manifest_with_checksums(manifest_path, data_dir)
        
        # Print summary
        print("\n=== Manifest Update Summary ===")
        print(f"Manifest: {manifest_path}")
        print(f"Scanned directory: {data_dir}")
        print(f"Total artifacts checksummed: {manifest['metadata'].get('total_files', 0)}")
        print(f"Last updated: {manifest['metadata'].get('last_updated', 'N/A')}")
        print("================================\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to update manifest: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit(main())
