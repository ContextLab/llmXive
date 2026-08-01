import os
import sys
import json
import shutil
import argparse
import hashlib
import tarfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import config for paths
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import ensure_directories
from utils.logging import get_logger, log_info, log_warning, log_error, log_debug

logger = get_logger(__name__)

def find_all_artifacts(base_dir: Path) -> List[Path]:
    """
    Recursively find all generated artifacts in the data/artifacts directory.
    Excludes temporary files and the manifest itself.
    """
    artifacts = []
    if not base_dir.exists():
        log_warning(f"Artifacts directory {base_dir} does not exist.")
        return artifacts

    for root, dirs, files in os.walk(base_dir):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.startswith('.') or file == 'manifest.json':
                continue
            file_path = Path(root) / file
            artifacts.append(file_path)
    
    log_info(f"Found {len(artifacts)} artifacts in {base_dir}")
    return artifacts

def extract_run_id(filename: str) -> Optional[str]:
    """
    Extract run_id from filename. Assumes format: ..._{run_id}.ext or ..._{run_id}_...
    """
    # Simple heuristic: look for 8+ char hex string or timestamp-like strings
    # Common patterns in this project: embeddings_{run_id}.parquet, metrics_conditioned_{run_id}.json
    parts = filename.replace('.json', '').replace('.parquet', '').replace('.csv', '').replace('.md', '').split('_')
    
    # Look for potential run_id candidates (usually the last meaningful part before extension)
    # In this project, run_ids are often timestamps or hashes.
    # We'll look for a segment that looks like a timestamp (YYYYMMDD_HHMMSS) or a hash.
    for part in reversed(parts):
        if len(part) >= 8 and (part.replace('_', '').replace('-', '').isdigit() or 
                               all(c in '0123456789abcdef' for c in part.lower())):
            return part
    return None

def normalize_filename(path: Path, run_id: str) -> str:
    """
    Normalize filename to ensure consistent naming with run_id.
    If run_id is missing in filename, prepend it.
    """
    original_name = path.name
    if run_id in original_name:
        return original_name
    
    # Prepend run_id
    stem = path.stem
    suffix = path.suffix
    return f"{stem}_{run_id}{suffix}"

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def create_archive_manifest(artifacts: List[Dict[str, Any]], output_path: Path) -> Dict[str, Any]:
    """
    Create a manifest JSON file documenting all archived artifacts.
    """
    manifest = {
        "archive_timestamp": datetime.utcnow().isoformat(),
        "project": "PROJ-823-llmxive-follow-up-extending-multabench-b",
        "task": "T051",
        "description": "Archived artifacts with run_id naming convention",
        "total_files": len(artifacts),
        "artifacts": artifacts
    }
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    log_info(f"Created manifest at {output_path}")
    return manifest

def archive_artifacts(source_dir: Path, archive_name: Optional[str] = None) -> Path:
    """
    Main function to archive artifacts with run_id naming convention.
    
    1. Scans data/artifacts for all files.
    2. Extracts run_id from each file.
    3. Renames files to ensure clear run_id naming.
    4. Creates a manifest.json.
    5. Packages everything into a tar.gz archive.
    """
    log_info(f"Starting artifact archiving process for {source_dir}")
    
    # Ensure artifacts directory exists
    ensure_directories()
    
    # Find all artifacts
    raw_artifacts = find_all_artifacts(source_dir)
    
    if not raw_artifacts:
        log_warning("No artifacts found to archive.")
        return source_dir / "archive_empty.tar.gz"
    
    # Determine run_id (use the most frequent one or the first found)
    run_ids = [extract_run_id(f.name) for f in raw_artifacts]
    run_ids = [r for r in run_ids if r]
    
    if not run_ids:
        # If no run_id found, generate a timestamp-based one
        run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        log_warning(f"No run_id found in filenames, using generated: {run_id}")
    else:
        # Use the most common run_id
        run_id = max(set(run_ids), key=run_ids.count)
        log_info(f"Detected primary run_id: {run_id}")
    
    # Prepare staging directory
    staging_dir = source_dir / "_staging"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True)
    
    processed_artifacts = []
    
    # Process each artifact
    for original_path in raw_artifacts:
        normalized_name = normalize_filename(original_path, run_id)
        target_path = staging_dir / normalized_name
        
        # Copy file
        shutil.copy2(original_path, target_path)
        
        # Compute hash
        file_hash = compute_file_hash(target_path)
        
        processed_artifacts.append({
            "original_filename": original_path.name,
            "archived_filename": normalized_name,
            "run_id": run_id,
            "size_bytes": target_path.stat().st_size,
            "sha256": file_hash,
            "relative_path": str(target_path.relative_to(source_dir))
        })
        
        log_debug(f"Processed: {original_path.name} -> {normalized_name}")
    
    # Create manifest
    manifest_path = staging_dir / "manifest.json"
    create_archive_manifest(processed_artifacts, manifest_path)
    
    # Create archive
    if not archive_name:
        archive_name = f"artifacts_{run_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.tar.gz"
    
    archive_path = source_dir.parent / archive_name
    
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(staging_dir, arcname="artifacts")
    
    # Cleanup staging
    shutil.rmtree(staging_dir)
    
    log_info(f"Successfully archived {len(processed_artifacts)} files to {archive_path}")
    return archive_path

def main():
    parser = argparse.ArgumentParser(description="Archive generated artifacts with run_id naming")
    parser.add_argument(
        "--source-dir", 
        type=Path, 
        default=Path("data/artifacts"),
        help="Directory containing artifacts to archive"
    )
    parser.add_argument(
        "--output-name",
        type=str,
        default=None,
        help="Custom name for the output archive (optional)"
    )
    
    args = parser.parse_args()
    
    try:
        archive_path = archive_artifacts(args.source_dir, args.output_name)
        print(f"Archive created: {archive_path}")
        
        # Verify archive exists
        if archive_path.exists():
            print(f"Success: {archive_path.stat().st_size} bytes archived.")
            sys.exit(0)
        else:
            log_error("Archive creation failed silently.")
            sys.exit(1)
            
    except Exception as e:
        log_error(f"Archiving process failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
