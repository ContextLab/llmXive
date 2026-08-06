import json
import os
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.data_synthesis.models import SyntheticVideoFrame
from src.utils.logging import get_logger
from src.utils.validation import validate_manifest_structure

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def export_raw_data(
    source_dir: Path,
    destination_dir: Path,
    chunk_ids: Optional[List[str]] = None,
    overwrite: bool = False
) -> List[Dict[str, Any]]:
    """
    Export raw video data (JSONL frames) from source directory to data/raw/.
    
    Args:
        source_dir: Directory containing generated chunk files (e.g., chunk_0001.jsonl)
        destination_dir: Target directory (e.g., data/raw/)
        chunk_ids: Optional list of specific chunk IDs to export. If None, export all.
        overwrite: If True, overwrite existing files in destination.
    
    Returns:
        List of metadata dicts for exported files.
    """
    logger = get_logger("exporter")
    source_dir = Path(source_dir)
    destination_dir = Path(destination_dir)
    
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    
    destination_dir.mkdir(parents=True, exist_ok=True)
    
    exported_files = []
    
    # Determine which files to process
    if chunk_ids:
        files_to_process = [source_dir / f"chunk_{cid}.jsonl" for cid in chunk_ids]
    else:
        files_to_process = list(source_dir.glob("chunk_*.jsonl"))
    
    if not files_to_process:
        logger.warning(f"No chunk files found in {source_dir}")
        return []
    
    for src_file in files_to_process:
        if not src_file.is_file():
            continue
        
        dst_file = destination_dir / src_file.name
        
        if dst_file.exists() and not overwrite:
            logger.info(f"Skipping existing file: {dst_file.name}")
            continue
        
        # Copy file
        shutil.copy2(str(src_file), str(dst_file))
        
        # Compute hash
        file_hash = compute_file_hash(dst_file)
        
        # Get file stats
        file_size = dst_file.stat().st_size
        
        metadata = {
            "filename": dst_file.name,
            "path": str(dst_file),
            "size_bytes": file_size,
            "sha256": file_hash,
            "exported_at": str(dst_file.stat().st_mtime)
        }
        
        exported_files.append(metadata)
        logger.info(f"Exported: {dst_file.name} ({file_size} bytes, hash: {file_hash[:16]}...)")
    
    return exported_files

def generate_manifest(
    exported_files: List[Dict[str, Any]],
    raw_data_dir: Path,
    manifest_path: Path,
    total_duration_seconds: float = 0.0
) -> Dict[str, Any]:
    """
    Generate manifest.jsonl file containing metadata for all exported data.
    
    Args:
        exported_files: List of file metadata dicts from export_raw_data
        raw_data_dir: Path to the raw data directory
        manifest_path: Path where manifest.jsonl will be written
        total_duration_seconds: Optional total duration of all video data
    
    Returns:
        The manifest dictionary written to disk.
    """
    logger = get_logger("exporter")
    raw_data_dir = Path(raw_data_dir)
    manifest_path = Path(manifest_path)
    
    # Ensure parent directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "version": "1.0",
        "created_at": str(manifest_path.stat().st_mtime) if manifest_path.exists() else None,
        "data_directory": str(raw_data_dir),
        "total_files": len(exported_files),
        "total_size_bytes": sum(f.get("size_bytes", 0) for f in exported_files),
        "total_duration_seconds": total_duration_seconds,
        "files": exported_files
    }
    
    # Validate structure
    try:
        validate_manifest_structure(manifest)
    except Exception as e:
        logger.error(f"Manifest validation failed: {e}")
        raise
    
    # Write manifest as JSONL (one line, one object)
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest written to: {manifest_path}")
    logger.info(f"  Total files: {manifest['total_files']}")
    logger.info(f"  Total size: {manifest['total_size_bytes']:,} bytes")
    logger.info(f"  Total duration: {manifest['total_duration_seconds']:,} seconds")
    
    return manifest

def main():
    """Main entry point for data export task."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Export synthetic data to data/raw/ and generate manifest")
    parser.add_argument("--source", type=str, required=True, help="Source directory with chunk files")
    parser.add_argument("--destination", type=str, default="data/raw", help="Destination directory for raw data")
    parser.add_argument("--manifest", type=str, default="data/manifest.jsonl", help="Path for manifest.jsonl")
    parser.add_argument("--duration", type=float, default=0.0, help="Total duration in seconds (optional)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    
    args = parser.parse_args()
    
    source_dir = Path(args.source)
    destination_dir = Path(args.destination)
    manifest_path = Path(args.manifest)
    
    logger = get_logger("exporter")
    logger.info(f"Starting export from {source_dir} to {destination_dir}")
    
    # Export raw data
    exported_files = export_raw_data(
        source_dir=source_dir,
        destination_dir=destination_dir,
        overwrite=args.overwrite
    )
    
    if not exported_files:
        logger.warning("No files were exported. Exiting.")
        return
    
    # Generate manifest
    manifest = generate_manifest(
        exported_files=exported_files,
        raw_data_dir=destination_dir,
        manifest_path=manifest_path,
        total_duration_seconds=args.duration
    )
    
    logger.info("Export completed successfully.")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
