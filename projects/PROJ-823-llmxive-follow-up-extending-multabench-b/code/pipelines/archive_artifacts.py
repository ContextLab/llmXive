"""
Archive artifacts generated during the pipeline execution.
This script scans the data/artifacts/ directory, organizes files by run_id,
computes hashes for integrity verification, and creates a manifest file.
"""
import os
import sys
import json
import shutil
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import config to ensure directories exist
from config import ensure_directories
from utils.logging import get_logger, log_info, log_warning, log_error

logger = get_logger(__name__)

def find_all_artifacts(artifacts_dir: Path) -> List[Path]:
    """
    Recursively find all artifact files in the specified directory.
    
    Args:
        artifacts_dir: Path to the artifacts directory
        
    Returns:
        List of paths to artifact files
    """
    if not artifacts_dir.exists():
        log_warning(f"Artifacts directory does not exist: {artifacts_dir}")
        return []
    
    artifacts = []
    for root, _, files in os.walk(artifacts_dir):
        for file in files:
            # Skip temporary files and the manifest itself
            if file.startswith('.') or file == 'archive_manifest.json':
                continue
            file_path = Path(root) / file
            if file_path.is_file():
                artifacts.append(file_path)
    
    log_info(f"Found {len(artifacts)} artifact files in {artifacts_dir}")
    return artifacts

def extract_run_id(filepath: Path) -> Optional[str]:
    """
    Extract run_id from filename based on naming convention.
    Expected formats:
    - embeddings_{run_id}.parquet
    - metrics_conditioned_{run_id}.json
    - frozen_baseline_aggregated_{run_id}.json
    - correlation_report_{run_id}.json
    - etc.
    
    Args:
        filepath: Path to the artifact file
        
    Returns:
        Extracted run_id or None if not found
    """
    filename = filepath.name
    
    # Common patterns for run_id extraction
    patterns = [
        r'embeddings_(.+)\.parquet',
        r'metrics_conditioned_(.+)\.json',
        r'frozen_baseline_aggregated_(.+)\.json',
        r'correlation_report_(.+)\.json',
        r'gpu_tuned_baselines_(.+)\.csv',
        r'metadata_stats_summary_(.+)\.csv',
        r'frozen_baseline_metrics_(.+)\.json',
        r'data_integrity_report_(.+)\.json',
        r'skipped_datasets_(.+)\.json',
        r'runtime_report_(.+)\.json',
        r'final_validation_report_(.+)\.md',
    ]
    
    import re
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
    
    # Fallback: try to extract any alphanumeric sequence that looks like a run_id
    # Run IDs are typically timestamps or hashes
    fallback_patterns = [
        r'(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2})',  # ISO timestamp format
        r'([a-f0-9]{16,})',  # Hash-like strings
    ]
    
    for pattern in fallback_patterns:
        match = re.search(pattern, filename)
        if match:
            return match.group(1)
    
    log_warning(f"Could not extract run_id from filename: {filename}")
    return None

def normalize_filename(filepath: Path, run_id: Optional[str] = None) -> str:
    """
    Normalize filename to ensure consistent naming with run_id.
    
    Args:
        filepath: Original file path
        run_id: Run ID to use in normalized name
        
    Returns:
        Normalized filename
    """
    if run_id:
        # Keep original extension but ensure run_id is in the name
        stem = filepath.stem
        suffix = filepath.suffix
        # If run_id is not already in the stem, add it
        if run_id not in stem:
            return f"{stem}_{run_id}{suffix}"
        return f"{stem}{suffix}"
    
    return filepath.name

def compute_file_hash(filepath: Path, algorithm: str = 'sha256') -> str:
    """
    Compute hash of a file for integrity verification.
    
    Args:
        filepath: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hex digest of the file hash
    """
    hash_func = hashlib.new(algorithm)
    
    try:
        with open(filepath, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        log_error(f"Failed to compute hash for {filepath}: {e}")
        raise

def create_archive_manifest(
    artifacts: List[Dict[str, Any]], 
    archive_path: Path,
    run_ids: List[str]
) -> Dict[str, Any]:
    """
    Create a manifest file documenting all archived artifacts.
    
    Args:
        artifacts: List of artifact information dictionaries
        archive_path: Path to the archive
        run_ids: List of run IDs included in the archive
        
    Returns:
        Manifest dictionary
    """
    manifest = {
        'archive_version': '1.0',
        'created_at': datetime.now().isoformat(),
        'archive_path': str(archive_path),
        'total_artifacts': len(artifacts),
        'run_ids': sorted(list(set(run_ids))),
        'artifacts': artifacts,
        'checksum_algorithm': 'sha256'
    }
    
    return manifest

def archive_artifacts(
    artifacts_dir: Path,
    output_dir: Path,
    include_run_ids: Optional[List[str]] = None
) -> Path:
    """
    Archive all artifacts with run_id organization and create manifest.
    
    Args:
        artifacts_dir: Source directory containing artifacts
        output_dir: Destination directory for archived artifacts
        include_run_ids: Optional list of specific run_ids to include
        
    Returns:
        Path to the archive manifest file
    """
    # Ensure output directory exists
    ensure_directories(output_dir)
    
    # Find all artifacts
    all_artifacts = find_all_artifacts(artifacts_dir)
    
    if not all_artifacts:
        log_warning("No artifacts found to archive")
        # Create empty manifest
        manifest_path = output_dir / 'archive_manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump({'error': 'No artifacts found'}, f, indent=2)
        return manifest_path
    
    # Filter by run_id if specified
    if include_run_ids:
        filtered_artifacts = []
        for artifact in all_artifacts:
            run_id = extract_run_id(artifact)
            if run_id and run_id in include_run_ids:
                filtered_artifacts.append(artifact)
        all_artifacts = filtered_artifacts
        log_info(f"Filtered to {len(all_artifacts)} artifacts for specified run_ids")
    
    # Organize artifacts by run_id
    artifacts_by_run = {}
    run_ids_found = []
    
    for artifact_path in all_artifacts:
        run_id = extract_run_id(artifact_path)
        
        if not run_id:
            # Place in 'unknown_run_id' folder
            run_id = 'unknown_run_id'
        
        if run_id not in artifacts_by_run:
            artifacts_by_run[run_id] = []
            run_ids_found.append(run_id)
        
        artifacts_by_run[run_id].append(artifact_path)
    
    # Create archive structure and copy files
    archived_artifacts = []
    
    for run_id, artifact_paths in artifacts_by_run.items():
        run_dir = output_dir / run_id
        ensure_directories(run_dir)
        
        for artifact_path in artifact_paths:
            # Compute hash
            file_hash = compute_file_hash(artifact_path)
            
            # Normalize filename
            normalized_name = normalize_filename(artifact_path, run_id)
            dest_path = run_dir / normalized_name
            
            # Copy file
            try:
                shutil.copy2(artifact_path, dest_path)
                
                # Record in manifest
                artifact_info = {
                    'original_path': str(artifact_path),
                    'archived_path': str(dest_path),
                    'filename': normalized_name,
                    'run_id': run_id,
                    'size_bytes': dest_path.stat().st_size,
                    'hash': file_hash,
                    'created_at': datetime.fromtimestamp(dest_path.stat().st_ctime).isoformat()
                }
                archived_artifacts.append(artifact_info)
                
                log_info(f"Archived: {artifact_path.name} -> {dest_path}")
                
            except Exception as e:
                log_error(f"Failed to archive {artifact_path}: {e}")
    
    # Create manifest
    archive_manifest_path = output_dir / 'archive_manifest.json'
    manifest = create_archive_manifest(
        archived_artifacts,
        archive_manifest_path,
        run_ids_found
    )
    
    with open(archive_manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    log_info(f"Archive complete. Manifest saved to: {archive_manifest_path}")
    log_info(f"Total artifacts archived: {len(archived_artifacts)}")
    log_info(f"Run IDs included: {', '.join(sorted(run_ids_found))}")
    
    return archive_manifest_path

def main():
    """Main entry point for the archive artifacts script."""
    parser = argparse.ArgumentParser(
        description='Archive pipeline artifacts with run_id organization'
    )
    parser.add_argument(
        '--artifacts-dir',
        type=str,
        default='data/artifacts',
        help='Source directory containing artifacts (default: data/artifacts)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/archived',
        help='Destination directory for archived artifacts (default: data/archived)'
    )
    parser.add_argument(
        '--run-ids',
        type=str,
        nargs='+',
        default=None,
        help='Optional list of specific run_ids to include'
    )
    
    args = parser.parse_args()
    
    # Convert to Path objects
    artifacts_dir = Path(args.artifacts_dir)
    output_dir = Path(args.output_dir)
    
    # Validate source directory
    if not artifacts_dir.exists():
        log_error(f"Artifacts directory does not exist: {artifacts_dir}")
        sys.exit(1)
    
    try:
        manifest_path = archive_artifacts(
            artifacts_dir=artifacts_dir,
            output_dir=output_dir,
            include_run_ids=args.run_ids
        )
        
        print(f"\nArchive completed successfully!")
        print(f"Manifest: {manifest_path}")
        
        # Load and display summary
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        if 'error' not in manifest:
            print(f"Total artifacts: {manifest['total_artifacts']}")
            print(f"Run IDs: {', '.join(manifest['run_ids'])}")
            
    except Exception as e:
        log_error(f"Archive process failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
