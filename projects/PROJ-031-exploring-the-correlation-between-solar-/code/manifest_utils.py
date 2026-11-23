import os
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_manifest(path: Path) -> Dict[str, Any]:
    """Load a YAML manifest file."""
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    if not isinstance(data, dict):
        raise ValueError("Manifest must be a YAML dictionary")
    
    return data

def save_manifest(manifest: Dict[str, Any], path: Path) -> None:
    """Save a manifest dictionary to a YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

def ensure_sources_initialized(manifest: Dict[str, Any], source_ids: list) -> None:
    """Ensure required source keys exist in the manifest."""
    if "sources" not in manifest:
        manifest["sources"] = {}
    
    for sid in source_ids:
        if sid not in manifest["sources"]:
            manifest["sources"][sid] = {
                "url": "",
                "status": "pending",
                "verified": False,
                "last_verified_at": None
            }

def update_source_status(manifest: Dict[str, Any], source_id: str, status: str, timestamp: Optional[str] = None) -> None:
    """Update the status and verification timestamp for a source."""
    if source_id not in manifest.get("sources", {}):
        raise KeyError(f"Source {source_id} not found in manifest")
    
    manifest["sources"][source_id]["status"] = status
    manifest["sources"][source_id]["verified"] = (status == "verified")
    if timestamp:
        manifest["sources"][source_id]["last_verified_at"] = timestamp
    else:
        manifest["sources"][source_id]["last_verified_at"] = datetime.utcnow().isoformat() + "Z"

def write_manifest_after_ingestion(manifest: Dict[str, Any], path: Path) -> None:
    """Finalize manifest after ingestion (checksums, etc.)."""
    # Placeholder for future checksum logic if needed
    manifest["last_updated"] = datetime.utcnow().isoformat() + "Z"
    save_manifest(manifest, path)

def validate_manifest_integrity(manifest: Dict[str, Any]) -> bool:
    """Basic validation that manifest structure is intact."""
    if "sources" not in manifest:
        return False
    for key, val in manifest["sources"].items():
        if not isinstance(val, dict):
            return False
        if "url" not in val or "status" not in val:
            return False
    return True

def main():
    """CLI entry point for manifest utilities (mostly for testing)."""
    logger.info("Manifest utilities module loaded.")

if __name__ == "__main__":
    main()