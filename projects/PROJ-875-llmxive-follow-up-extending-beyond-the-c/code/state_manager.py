"""
State manager for llmXive project.

Handles saving and loading state manifests including checksums.
Integrates with utils/checksum.py for data integrity.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Import checksum utilities
import sys
sys.path.append(str(Path(__file__).parent.parent / "utils"))
from checksum import generate_checksum_manifest, save_manifest, load_manifest, verify_checksums

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
CHECKSUM_MANIFEST_PATH = STATE_DIR / "checksums.yaml"

def ensure_state_dir():
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def update_checksum_manifest() -> Path:
    """
    Generate and save a new checksum manifest for data/processed/.
    
    Returns:
        Path to the saved manifest file
    """
    ensure_state_dir()
    return save_manifest(generate_checksum_manifest())

def get_checksum_manifest() -> Optional[Dict[str, Any]]:
    """
    Load the current checksum manifest.
    
    Returns:
        Manifest dictionary or None if not found
    """
    return load_manifest(CHECKSUM_MANIFEST_PATH)

def verify_data_integrity() -> Dict[str, Any]:
    """
    Verify data integrity against stored checksums.
    
    Returns:
        Verification results dictionary
    """
    return verify_checksums(CHECKSUM_MANIFEST_PATH)

def create_state_snapshot(
    snapshot_name: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Create a state snapshot file with checksums and metadata.
    
    Args:
        snapshot_name: Name for the snapshot (will be saved as state/<name>.yaml)
        metadata: Additional metadata to include in the snapshot
        
    Returns:
        Path to the created snapshot file
    """
    ensure_state_dir()
    
    checksum_manifest = get_checksum_manifest()
    if checksum_manifest is None:
        # Generate fresh checksums if none exist
        checksum_manifest = generate_checksum_manifest()
        save_manifest(checksum_manifest, CHECKSUM_MANIFEST_PATH)
    
    snapshot = {
        "snapshot_name": snapshot_name,
        "created_at": datetime.now().isoformat(),
        "checksum_manifest": checksum_manifest,
        "metadata": metadata or {}
    }
    
    snapshot_path = STATE_DIR / f"{snapshot_name}.yaml"
    with open(snapshot_path, "w", encoding="utf-8") as f:
        yaml.dump(snapshot, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    return snapshot_path

def load_state_snapshot(snapshot_name: str) -> Optional[Dict[str, Any]]:
    """
    Load a state snapshot by name.
    
    Args:
        snapshot_name: Name of the snapshot to load
        
    Returns:
        Snapshot dictionary or None if not found
    """
    snapshot_path = STATE_DIR / f"{snapshot_name}.yaml"
    if not snapshot_path.exists():
        return None
    
    with open(snapshot_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    """
    CLI entry point for state management operations.
    
    Usage:
        python code/state_manager.py --update-checksums
        python code/state_manager.py --verify
        python code/state_manager.py --snapshot <name>
    """
    import sys
    
    if "--update-checksums" in sys.argv:
        print("Updating checksum manifest...")
        path = update_checksum_manifest()
        print(f"Checksum manifest updated: {path}")
        return 0
    
    elif "--verify" in sys.argv:
        print("Verifying data integrity...")
        results = verify_data_integrity()
        print(f"Status: {results['status']}")
        print(f"Verified: {results['verified']}")
        print(f"Failed: {results['failed']}")
        print(f"Missing: {results['missing']}")
        return 0 if results["status"] == "success" else 1
    
    elif "--snapshot" in sys.argv:
        try:
            name_index = sys.argv.index("--snapshot") + 1
            snapshot_name = sys.argv[name_index]
        except (IndexError, ValueError):
            print("Error: --snapshot requires a name argument")
            return 1
        
        print(f"Creating state snapshot: {snapshot_name}")
        path = create_state_snapshot(snapshot_name)
        print(f"Snapshot created: {path}")
        return 0
    
    else:
        print("Usage: python code/state_manager.py [--update-checksums|--verify|--snapshot <name>]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
