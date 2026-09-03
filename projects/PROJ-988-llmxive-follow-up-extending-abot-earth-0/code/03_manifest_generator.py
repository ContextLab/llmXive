import os
import sys
import json
import hashlib
import logging
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ensure code directory is in path for imports if run as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from lib.logging_config import setup_logging, get_logger

logger = get_logger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise

def get_file_info(file_path: Path) -> Dict[str, Any]:
    """Get file metadata."""
    stats = file_path.stat()
    return {
        "filename": file_path.name,
        "size_bytes": stats.st_size,
        "modified_timestamp": stats.st_mtime,
        "extension": file_path.suffix
    }

def scan_directory(directory: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """Recursively scan directory for files, optionally filtering by extension."""
    files = []
    if not directory.exists():
        logger.warning(f"Directory does not exist, skipping: {directory}")
        return files
    
    for item in directory.rglob("*"):
        if item.is_file():
            if extensions is None or item.suffix in extensions:
                files.append(item)
    return files

def load_existing_manifests(manifest_paths: List[Path]) -> Dict[str, Any]:
    """Load and merge existing manifest files."""
    merged = {}
    for manifest_path in manifest_paths:
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        merged.update(data)
                    elif isinstance(data, list):
                        # Handle list of entries if necessary, though spec implies dict structure
                        for entry in data:
                            if 'path' in entry:
                                merged[entry['path']] = entry
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse existing manifest {manifest_path}: {e}")
        else:
            logger.debug(f"Existing manifest not found (expected): {manifest_path}")
    return merged

def generate_manifest(
    data_dirs: List[Path],
    output_path: Path,
    existing_manifests: Optional[List[Path]] = None
) -> Dict[str, Any]:
    """
    Scan data directories, calculate checksums, and generate a comprehensive manifest.
    
    Args:
        data_dirs: List of directories to scan (e.g., aligned_pairs, patches, degraded scenes)
        output_path: Path where the final manifest.json will be saved
        existing_manifests: Optional list of other manifest files to merge into this one
    
    Returns:
        The generated manifest dictionary
    """
    logger.info(f"Starting manifest generation for directories: {[str(d) for d in data_dirs]}")
    
    # Define extensions to include (common data formats)
    target_extensions = ['.csv', '.json', '.png', '.tif', '.tiff', '.jpg', '.jpeg', '.ply', '.npy', '.parquet']
    
    manifest = {
        "version": "1.0",
        "generated_at": "", # Will be filled by caller or timestamp logic if needed
        "source_directories": [str(d) for d in data_dirs],
        "files": {}
    }
    
    # Load existing manifests if provided
    if existing_manifests:
        existing_data = load_existing_manifests(existing_manifests)
        # We might want to merge existing data into the new structure or just start fresh
        # For this task, we generate a fresh manifest of current state, 
        # but we could merge if the logic requires cumulative tracking.
        # Per task description: "Save ... with checksums in data/manifest.json"
        # This implies a snapshot of the current state.
        logger.info(f"Loaded {len(existing_data)} entries from existing manifests to consider.")

    total_files = 0
    total_size = 0
    errors = []

    for data_dir in data_dirs:
        if not data_dir.exists():
            logger.warning(f"Skipping non-existent directory: {data_dir}")
            continue
        
        files = scan_directory(data_dir, extensions=target_extensions)
        
        for file_path in files:
            try:
                checksum = calculate_sha256(file_path)
                file_info = get_file_info(file_path)
                
                # Relative path from project root for portability
                try:
                    rel_path = file_path.relative_to(Path.cwd())
                except ValueError:
                    # Fallback if not relative to cwd
                    rel_path = file_path
                
                entry = {
                    "path": str(rel_path),
                    "checksum_sha256": checksum,
                    "size_bytes": file_info["size_bytes"],
                    "extension": file_info["extension"],
                    "source_dir": str(data_dir)
                }
                
                manifest["files"][str(rel_path)] = entry
                total_files += 1
                total_size += file_info["size_bytes"]
                
            except Exception as e:
                error_msg = f"Error processing {file_path}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
    
    manifest["summary"] = {
        "total_files": total_files,
        "total_size_bytes": total_size,
        "errors_count": len(errors),
        "errors": errors
    }
    
    # Save manifest
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest saved to {output_path}")
    logger.info(f"Total files indexed: {total_files}, Total size: {total_size / (1024*1024):.2f} MB")
    
    return manifest

def save_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """Helper to save manifest to disk."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest saved to {output_path}")

def main():
    """
    Main entry point for T017: Save aligned pairs, patches, and degraded scenes to data/processed/
    with checksums in data/manifest.json.
    """
    setup_logging()
    
    # Define project root relative to script location
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent # Assuming code/ is one level up from project root? 
    # Wait, tasks.md says: "All artifact paths are relative to the project root ... under code/, data/..."
    # The script is at code/03_manifest_generator.py.
    # So project_root should be the parent of 'code'.
    project_root = script_dir.parent
    
    data_processed_dir = project_root / "data" / "processed"
    manifest_output_path = project_root / "data" / "manifest.json"
    
    # Define the specific subdirectories to scan as per T017
    # T012: aligned_pairs.csv (in data/processed/), but we scan the source dirs for files
    # T013: patches_100m2/
    # T014b: nnf_varied_scenes/ (and degraded_base)
    
    # We scan the directories where the actual data files reside.
    # Based on T012-T014 descriptions:
    dirs_to_scan = [
        data_processed_dir, # Root processed dir to catch manifests like raw_manifest.csv, alignment_report.csv
        data_processed_dir / "patches_100m2",
        data_processed_dir / "degraded_base",
        data_processed_dir / "nnf_varied_scenes"
    ]
    
    # Filter out non-existent directories to avoid errors
    valid_dirs = [d for d in dirs_to_scan if d.exists()]
    
    if not valid_dirs:
        logger.warning("No data directories found to scan. Ensure T012, T013, T014 have run.")
        # Still generate an empty manifest to indicate the step ran, but with 0 files
        valid_dirs = [data_processed_dir] # Fallback to root to at least try
    
    existing_manifests = [
        data_processed_dir / "raw_manifest.csv", # These are CSVs, not JSON manifests, so maybe ignore
        data_processed_dir / "patch_manifest.csv",
        data_processed_dir / "degraded_manifest.json" # This one might be JSON
    ]
    
    # Only pass existing JSON manifests if we want to merge. 
    # The task says "Save ... with checksums in data/manifest.json". 
    # This implies creating a NEW master manifest.
    
    manifest = generate_manifest(
        data_dirs=valid_dirs,
        output_path=manifest_output_path,
        existing_manifests=[] # Start fresh for the master manifest
    )
    
    print(f"Task T017 Complete. Manifest generated at: {manifest_output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())