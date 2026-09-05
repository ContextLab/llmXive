"""
Manifest Generator for llmXive Pipeline (T017)

This script aggregates all processed data artifacts (aligned pairs, patches, 
degraded scenes) and generates a unified manifest with checksums.

Outputs:
    data/manifest.json: Unified manifest containing file paths, types, and SHA256 checksums.
"""
import os
import sys
import json
import hashlib
import logging
import csv
from pathlib import Path
from datetime import datetime

# Add project root to path to allow relative imports if needed, 
# though this script is standalone for T017.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate checksum for {file_path}: {e}")
        raise

def get_file_info(file_path: Path) -> dict:
    """Get basic file information."""
    stat = file_path.stat()
    return {
        "name": file_path.name,
        "size_bytes": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "extension": file_path.suffix
    }

def scan_directory(directory: Path, file_patterns: list = None) -> list:
    """
    Scan a directory for files matching patterns.
    
    Args:
        directory: Path to scan.
        file_patterns: List of extensions to look for (e.g., ['.csv', '.json', '.png']).
                       If None, scans all files.
                       
    Returns:
        List of Path objects.
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []
    
    files = []
    for item in directory.rglob("*"):
        if item.is_file():
            if file_patterns is None or item.suffix in file_patterns:
                files.append(item)
    return files

def load_existing_manifests(manifest_paths: list) -> dict:
    """
    Load existing manifest files and merge them.
    
    Args:
        manifest_paths: List of paths to existing manifest JSON files.
        
    Returns:
        Merged dictionary of manifest entries.
    """
    merged = {}
    for m_path in manifest_paths:
        if m_path.exists():
            try:
                with open(m_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        merged.update({item.get('path', ''): item for item in data})
                    elif isinstance(data, dict):
                        merged.update(data)
            except Exception as e:
                logger.warning(f"Could not load manifest {m_path}: {e}")
    return merged

def generate_manifest() -> dict:
    """
    Generate the unified manifest for T017.
    
    Scans the following directories based on previous tasks:
    - data/processed/aligned_pairs.csv (from T012)
    - data/processed/patch_manifest.csv (from T013)
    - data/processed/patches_100m2/ (from T013)
    - data/processed/degraded_manifest.json (from T014b)
    - data/processed/nnf_varied_scenes/ (from T014b)
    - data/processed/aligned_pairs/ (implied folder for T012)
    
    Returns:
        Dictionary representing the full manifest.
    """
    manifest_entries = []
    
    # Define specific files and directories to include based on task descriptions
    targets = [
        # T012 outputs
        ("data/processed/raw_manifest.csv", "aligned_raw"),
        ("data/processed/aligned_pairs.csv", "aligned_pairs"),
        ("data/processed/alignment_report.csv", "alignment_report"),
        
        # T013 outputs
        ("data/processed/patch_manifest.csv", "patch_manifest"),
        
        # T014b outputs
        ("data/processed/degraded_manifest.json", "degraded_manifest"),
        ("data/processed/nnf_varied_scenes", "nnf_varied_scenes"),
        
        # T012 implied folder (if files exist)
        ("data/processed/aligned_pairs", "aligned_pairs_folder"),
        
        # T013 implied folder
        ("data/processed/patches_100m2", "patches_100m2"),
        
        # T015/T016 outputs (if they exist)
        ("data/raw/real_cloud_masks_subset", "real_cloud_masks"),
        ("data/results/mask_similarity_score.json", "mask_similarity_score"),
        
        # T021/T023 outputs (if they exist from future/parallel tasks)
        ("data/processed/reconstructed/baseline", "reconstructed_baseline"),
        ("data/processed/reconstructed/inpainted", "reconstructed_inpainted"),
        ("data/results/performance_log.csv", "performance_log"),
    ]
    
    for target_rel, category in targets:
        target_path = PROCESSED_DIR.parent / target_rel
        
        if target_path.is_file():
            # Handle single file
            checksum = calculate_sha256(target_path)
            info = get_file_info(target_path)
            entry = {
                "path": str(target_path.relative_to(PROJECT_ROOT)),
                "type": "file",
                "category": category,
                "checksum_sha256": checksum,
                **info
            }
            manifest_entries.append(entry)
            
        elif target_path.is_dir():
            # Handle directory contents
            files = list(target_path.rglob("*"))
            if not files:
                logger.info(f"Skipping empty directory: {target_path}")
                continue
                
            for file_path in files:
                if file_path.is_file():
                    try:
                        checksum = calculate_sha256(file_path)
                        info = get_file_info(file_path)
                        entry = {
                            "path": str(file_path.relative_to(PROJECT_ROOT)),
                            "type": "file",
                            "category": category,
                            "checksum_sha256": checksum,
                            **info
                        }
                        manifest_entries.append(entry)
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
        else:
            logger.info(f"Target not found, skipping: {target_path}")
    
    return {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "project": "PROJ-988-llmxive-follow-up-extending-abot-earth-0",
        "task_id": "T017",
        "description": "Unified manifest of aligned pairs, patches, and degraded scenes with checksums",
        "entries": manifest_entries,
        "total_files": len(manifest_entries)
    }

def save_manifest(manifest: dict, output_path: Path):
    """Save the manifest to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest saved to {output_path}")

def main():
    """Main entry point for T017."""
    logger.info("Starting Manifest Generation (T017)...")
    
    output_path = DATA_DIR / "manifest.json"
    
    try:
        manifest_data = generate_manifest()
        save_manifest(manifest_data, output_path)
        
        logger.info(f"Successfully generated manifest with {manifest_data['total_files']} entries.")
        return 0
    except Exception as e:
        logger.error(f"Manifest generation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
