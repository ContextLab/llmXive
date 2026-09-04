import json
import os
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.utils.logging import get_logger
from src.utils.validation import validate_manifest_structure, ValidationError
from src.data_synthesis.models import SyntheticVideoFrame
from src.data_synthesis.visual_labeler import FrameLabel
from src.data_synthesis.logging_integration import LabelingAuditLogger

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def export_raw_data(
    source_dir: Path,
    dest_dir: Path,
    chunk_id: str,
    overwrite: bool = False
) -> Dict[str, Any]:
    """
    Export raw video frames and labels from source to destination.
    
    Args:
        source_dir: Directory containing generated video frames and labels
        dest_dir: Destination directory for raw data export
        chunk_id: Identifier for this chunk of data
        overwrite: Whether to overwrite existing files
        
    Returns:
        Dictionary containing export metadata
    """
    logger = get_logger("data_synthesis.exporter")
    
    # Ensure destination directory exists
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Source paths
    frames_file = source_dir / f"{chunk_id}_frames.jsonl"
    labels_file = source_dir / f"{chunk_id}_labels.jsonl"
    
    # Destination paths
    dest_frames_file = dest_dir / f"{chunk_id}_frames.jsonl"
    dest_labels_file = dest_dir / f"{chunk_id}_labels.jsonl"
    
    export_stats = {
        "chunk_id": chunk_id,
        "frames_exported": 0,
        "labels_exported": 0,
        "frames_hash": None,
        "labels_hash": None,
        "export_path": str(dest_dir),
        "timestamp": None
    }
    
    # Export frames
    if frames_file.exists():
        if dest_frames_file.exists() and not overwrite:
            logger.warning(f"Frames file {dest_frames_file} already exists, skipping")
        else:
            shutil.copy2(frames_file, dest_frames_file)
            export_stats["frames_exported"] = sum(1 for _ in open(frames_file))
            export_stats["frames_hash"] = compute_file_hash(dest_frames_file)
            logger.info(f"Exported {export_stats['frames_exported']} frames to {dest_frames_file}")
    else:
        logger.warning(f"Source frames file {frames_file} not found")
    
    # Export labels
    if labels_file.exists():
        if dest_labels_file.exists() and not overwrite:
            logger.warning(f"Labels file {dest_labels_file} already exists, skipping")
        else:
            shutil.copy2(labels_file, dest_labels_file)
            export_stats["labels_exported"] = sum(1 for _ in open(labels_file))
            export_stats["labels_hash"] = compute_file_hash(dest_labels_file)
            logger.info(f"Exported {export_stats['labels_exported']} labels to {dest_labels_file}")
    else:
        logger.warning(f"Source labels file {labels_file} not found")
    
    # Record timestamp
    export_stats["timestamp"] = os.path.getmtime(dest_frames_file) if dest_frames_file.exists() else None
    
    return export_stats

def generate_manifest(
    raw_data_dir: Path,
    manifest_path: Path,
    total_duration_seconds: float,
    ci_mode: bool = False,
    target_duration: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate a manifest.jsonl file documenting the exported dataset.
    
    Args:
        raw_data_dir: Directory containing exported raw data files
        manifest_path: Path to write the manifest.jsonl file
        total_duration_seconds: Total duration of video data in seconds
        ci_mode: Whether running in CI mode (subset generation)
        target_duration: Expected target duration for validation
        
    Returns:
        Dictionary containing manifest metadata
    """
    logger = get_logger("data_synthesis.exporter")
    
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Collect chunk information
    chunks = []
    total_frames = 0
    total_labels = 0
    critical_count = 0
    silence_count = 0
    
    for jsonl_file in sorted(raw_data_dir.glob("*_frames.jsonl")):
        chunk_id = jsonl_file.stem.replace("_frames", "")
        
        # Count frames
        frame_count = sum(1 for _ in open(jsonl_file))
        total_frames += frame_count
        
        # Get corresponding labels
        labels_file = raw_data_dir / f"{chunk_id}_labels.jsonl"
        label_count = 0
        if labels_file.exists():
            label_count = sum(1 for _ in open(labels_file))
            total_labels += label_count
            
            # Count label types
            with open(labels_file, 'r') as f:
                for line in f:
                    label_data = json.loads(line)
                    if label_data.get("label") == "critical":
                        critical_count += 1
                    elif label_data.get("label") == "silence":
                        silence_count += 1
        
        # Compute hash
        file_hash = compute_file_hash(jsonl_file)
        
        chunks.append({
            "chunk_id": chunk_id,
            "frames_file": str(jsonl_file),
            "labels_file": str(labels_file) if labels_file.exists() else None,
            "frame_count": frame_count,
            "label_count": label_count,
            "file_hash": file_hash
        })
    
    # Validate manifest structure
    manifest_content = {
        "version": "1.0",
        "ci_mode": ci_mode,
        "total_duration_seconds": total_duration_seconds,
        "target_duration_seconds": target_duration if target_duration else total_duration_seconds,
        "total_frames": total_frames,
        "total_labels": total_labels,
        "label_distribution": {
            "critical": critical_count,
            "silence": silence_count
        },
        "chunks": chunks,
        "raw_data_dir": str(raw_data_dir),
        "generated_at": None
    }
    
    # Write manifest as JSONL (one line per entry for streaming compatibility)
    with open(manifest_path, 'w') as f:
        json.dump(manifest_content, f, indent=2)
    
    logger.info(f"Generated manifest at {manifest_path}")
    logger.info(f"Total frames: {total_frames}, Total labels: {total_labels}")
    logger.info(f"Label distribution - Critical: {critical_count}, Silence: {silence_count}")
    
    # Validate manifest
    try:
        validate_manifest_structure(manifest_content)
        logger.info("Manifest structure validation passed")
    except ValidationError as e:
        logger.error(f"Manifest structure validation failed: {e}")
        raise
    
    return manifest_content

def main():
    """Main entry point for data export."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Export synthetic data to raw format")
    parser.add_argument("--source-dir", type=str, required=True, help="Source directory with generated data")
    parser.add_argument("--dest-dir", type=str, required=True, help="Destination directory for raw data")
    parser.add_argument("--manifest-path", type=str, default="data/manifest.jsonl", help="Path for manifest file")
    parser.add_argument("--chunk-id", type=str, required=True, help="Chunk identifier")
    parser.add_argument("--total-duration", type=float, required=True, help="Total duration in seconds")
    parser.add_argument("--ci-mode", action="store_true", help="Run in CI mode (subset)")
    parser.add_argument("--target-duration", type=float, help="Target duration for validation")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    
    args = parser.parse_args()
    
    source_dir = Path(args.source_dir)
    dest_dir = Path(args.dest_dir)
    manifest_path = Path(args.manifest_path)
    
    # Export raw data
    logger = get_logger("data_synthesis.exporter")
    logger.info(f"Starting export from {source_dir} to {dest_dir}")
    
    export_stats = export_raw_data(
        source_dir=source_dir,
        dest_dir=dest_dir,
        chunk_id=args.chunk_id,
        overwrite=args.overwrite
    )
    
    # Generate manifest
    manifest_content = generate_manifest(
        raw_data_dir=dest_dir,
        manifest_path=manifest_path,
        total_duration_seconds=args.total_duration,
        ci_mode=args.ci_mode,
        target_duration=args.target_duration
    )
    
    logger.info("Export completed successfully")
    return export_stats, manifest_content

if __name__ == "__main__":
    main()