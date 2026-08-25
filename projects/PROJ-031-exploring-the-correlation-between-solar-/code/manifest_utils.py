"""
Manifest Consistency Utilities for PROJ-031.

Provides atomic updates to data/source_manifest.yaml including
last_verified_at timestamps and status fields for every source.
"""
import os
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "data" / "source_manifest.yaml"
logger = logging.getLogger(__name__)

REQUIRED_SOURCES = [
    "dst_indices",
    "kp_indices",
    "goes_flares",
    "cme_catalog"
]

def load_manifest() -> Dict[str, Any]:
    """
    Load the source manifest from disk.
    
    Raises:
        FileNotFoundError: If the manifest file is missing.
        yaml.YAMLError: If the manifest is corrupted.
    """
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Manifest file missing at {MANIFEST_PATH}. "
            "Pipeline cannot proceed without a valid source manifest."
        )
    
    try:
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict) or 'sources' not in data:
                raise yaml.YAMLError("Manifest missing 'sources' key.")
            return data
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Manifest file corrupted at {MANIFEST_PATH}: {e}")

def save_manifest(data: Dict[str, Any]) -> None:
    """
    Atomically save the manifest to disk.
    
    Uses a temporary file and rename to ensure atomicity.
    """
    temp_path = MANIFEST_PATH.with_suffix('.tmp')
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        os.replace(temp_path, MANIFEST_PATH)
        logger.info(f"Manifest updated atomically at {MANIFEST_PATH}")
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise RuntimeError(f"Failed to save manifest atomically: {e}")

def ensure_sources_initialized(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure all required sources exist in the manifest with required fields.
    
    Args:
        manifest: The loaded manifest dictionary.
        
    Returns:
        The updated manifest dictionary.
    """
    if 'sources' not in manifest:
        manifest['sources'] = {}
    
    for source in REQUIRED_SOURCES:
        if source not in manifest['sources']:
            manifest['sources'][source] = {
                'status': 'Pending',
                'url': '',
                'retrieved_at': None,
                'record_count': 0
            }
        else:
            # Ensure required fields exist
            if 'status' not in manifest['sources'][source]:
                manifest['sources'][source]['status'] = 'Pending'
            if 'last_verified_at' not in manifest['sources'][source]:
                manifest['sources'][source]['last_verified_at'] = None
            
    return manifest

def update_source_status(
    source_name: str,
    status: str,
    url: Optional[str] = None,
    record_count: Optional[int] = None,
    manifest: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update a specific source's status and metadata.
    
    Args:
        source_name: The key of the source (e.g., 'dst_indices').
        status: The new status ('Verified', 'Failed', 'Pending').
        url: Optional URL to update.
        record_count: Optional record count to update.
        manifest: Optional manifest to update in memory. If None, loads from disk.
        
    Returns:
        The updated manifest dictionary.
    """
    if manifest is None:
        manifest = load_manifest()
    
    manifest = ensure_sources_initialized(manifest)
    
    if source_name not in manifest['sources']:
        raise ValueError(f"Unknown source: {source_name}")
    
    now = datetime.utcnow().isoformat()
    manifest['sources'][source_name]['status'] = status
    manifest['sources'][source_name]['last_verified_at'] = now
    
    if url is not None:
        manifest['sources'][source_name]['url'] = url
    if record_count is not None:
        manifest['sources'][source_name]['record_count'] = record_count
    
    return manifest

def write_manifest_after_ingestion(
    source_name: str,
    status: str,
    url: Optional[str] = None,
    record_count: Optional[int] = None
) -> None:
    """
    Load manifest, update source, and save atomically.
    
    This is the primary entry point for ingestion scripts to update the manifest.
    """
    manifest = load_manifest()
    updated_manifest = update_source_status(
        source_name=source_name,
        status=status,
        url=url,
        record_count=record_count,
        manifest=manifest
    )
    save_manifest(updated_manifest)
    logger.info(f"Manifest updated for {source_name}: status={status}")

def validate_manifest_integrity(manifest: Dict[str, Any]) -> bool:
    """
    Validate that all required sources have required fields.
    
    Returns:
        True if valid, False otherwise.
    """
    if 'sources' not in manifest:
        return False
        
    for source in REQUIRED_SOURCES:
        if source not in manifest['sources']:
            return False
        entry = manifest['sources'][source]
        if 'status' not in entry or 'last_verified_at' not in entry:
            return False
    return True

def main():
    """CLI entry point for manifest utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage source manifest")
    parser.add_argument("--check", action="store_true", help="Check manifest integrity")
    parser.add_argument("--update", type=str, help="Update a specific source status")
    parser.add_argument("--status", type=str, help="Status value for update")
    parser.add_argument("--url", type=str, help="URL for update")
    parser.add_argument("--count", type=int, help="Record count for update")
    
    args = parser.parse_args()
    
    if args.check:
        try:
            manifest = load_manifest()
            if validate_manifest_integrity(manifest):
                print("Manifest integrity: OK")
            else:
                print("Manifest integrity: FAILED - Missing required fields")
                return 1
        except Exception as e:
            print(f"Manifest check failed: {e}")
            return 1
    elif args.update:
        if not args.status:
            print("Error: --status required with --update")
            return 1
        try:
            write_manifest_after_ingestion(
                source_name=args.update,
                status=args.status,
                url=args.url,
                record_count=args.count
            )
            print(f"Updated {args.update} to {args.status}")
        except Exception as e:
            print(f"Update failed: {e}")
            return 1
    else:
        parser.print_help()
    
    return 0

if __name__ == "__main__":
    exit(main())
