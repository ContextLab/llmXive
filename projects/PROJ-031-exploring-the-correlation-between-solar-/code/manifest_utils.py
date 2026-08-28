import os
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def load_manifest(manifest_path: str = "data/source_manifest.yaml") -> Dict[str, Any]:
    """Load the source manifest YAML file."""
    if not os.path.exists(manifest_path):
        logger.warning(f"Manifest file not found at {manifest_path}. Initializing empty.")
        return {"sources": {}, "last_updated": None}
    
    with open(manifest_path, 'r') as f:
        return yaml.safe_load(f)

def save_manifest(manifest: Dict[str, Any], manifest_path: str = "data/source_manifest.yaml") -> None:
    """Save the manifest dictionary to YAML."""
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

def ensure_sources_initialized(manifest: Dict[str, Any], required_sources: Dict[str, str]) -> Dict[str, Any]:
    """Ensure all required sources exist in the manifest with default values."""
    if "sources" not in manifest:
        manifest["sources"] = {}
    
    for source_id, url in required_sources.items():
        if source_id not in manifest["sources"]:
            manifest["sources"][source_id] = {
                "url": url,
                "status": "pending",
                "verified": False,
                "last_verified_at": None
            }
        else:
            # Ensure URL is updated if it changed
            manifest["sources"][source_id]["url"] = url
    
    return manifest

def update_source_status(
    manifest: Dict[str, Any], 
    source_id: str, 
    status: str, 
    verified: bool
) -> Dict[str, Any]:
    """Update the status and verification flag for a specific source."""
    if source_id not in manifest["sources"]:
        logger.warning(f"Source {source_id} not found in manifest. Cannot update status.")
        return manifest
    
    manifest["sources"][source_id]["status"] = status
    manifest["sources"][source_id]["verified"] = verified
    manifest["sources"][source_id]["last_verified_at"] = datetime.utcnow().isoformat()
    
    return manifest

def write_manifest_after_ingestion(manifest: Dict[str, Any], manifest_path: str = "data/source_manifest.yaml") -> None:
    """Update the last_updated timestamp and save the manifest."""
    manifest["last_updated"] = datetime.utcnow().isoformat()
    save_manifest(manifest, manifest_path)

def validate_manifest_integrity(manifest: Dict[str, Any]) -> bool:
    """Basic validation that manifest structure is intact."""
    if "sources" not in manifest:
        return False
    
    for source_id, data in manifest["sources"].items():
        if "url" not in data or "status" not in data:
            logger.error(f"Missing required fields in source {source_id}")
            return False
    
    return True

def main():
    """CLI entry point for manifest utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage source manifest")
    parser.add_argument("--verify", action="store_true", help="Verify manifest integrity")
    parser.add_argument("--init", action="store_true", help="Initialize with required sources")
    parser.add_argument("--url", type=str, help="URL to update (with --source-id)")
    parser.add_argument("--source-id", type=str, help="Source ID to update")
    parser.add_argument("--status", type=str, help="Status to set")
    parser.add_argument("--verified", type=str, choices=["true", "false"], help="Verification flag")
    
    args = parser.parse_args()
    
    manifest = load_manifest()
    
    if args.verify:
        if validate_manifest_integrity(manifest):
            print("Manifest integrity check passed.")
        else:
            print("Manifest integrity check FAILED.")
        return 0
    
    if args.init:
        # Define standard sources for this project
        required = {
            "CDAWeb_LASCO": "https://cdaweb.gsfc.nasa.gov/index.html/",
            "GOES_XRAY": "https://services.swpc.noaa.gov/products/goes-x-ray-flare-list.txt",
            "NOAA_SWPC_DST": "https://services.swpc.noaa.gov/products/noaa-dst.txt",
            "NOAA_SWPC_KP": "https://services.swpc.noaa.gov/products/noaa-kp-index.txt"
        }
        manifest = ensure_sources_initialized(manifest, required)
        write_manifest_after_ingestion(manifest)
        print("Manifest initialized/updated with standard sources.")
        return 0
    
    if args.source_id:
        if args.status:
            manifest = update_source_status(manifest, args.source_id, args.status, False)
        if args.verified:
            is_verified = args.verified == "true"
            # If status not set, default to verified based on flag
            status = "verified" if is_verified else "pending"
            manifest = update_source_status(manifest, args.source_id, status, is_verified)
        if args.url:
            manifest["sources"][args.source_id]["url"] = args.url
        write_manifest_after_ingestion(manifest)
        print(f"Updated source {args.source_id}.")
        return 0
    
    print("Usage: python manifest_utils.py [--verify|--init|--source-id <id> [--status <s>] [--verified <t/f>] [--url <u>]]")
    return 0

if __name__ == "__main__":
    exit(main())
