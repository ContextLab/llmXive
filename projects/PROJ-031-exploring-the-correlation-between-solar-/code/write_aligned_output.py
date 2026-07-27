import os
import sys
import csv
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any

# Ensure we can import from the project root if run as a module
# (though typically run as `python code/write_aligned_output.py`)

def ensure_directories():
    """Ensure output directories exist."""
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/raw", exist_ok=True)

def load_aligned_events(input_path: str = "data/processed/aligned_events.csv") -> list:
    """Load aligned events from CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    events = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(row)
    return events

def write_aligned_events(events: list, output_path: str = "data/processed/aligned_events.csv") -> None:
    """Write aligned events to CSV."""
    if not events:
        raise ValueError("No events to write")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Get fieldnames from the first event
    fieldnames = list(events[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest(manifest_path: str = "data/source_manifest.yaml") -> Dict[str, Any]:
    """Load source manifest from YAML."""
    import yaml
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_manifest(manifest: Dict[str, Any], manifest_path: str = "data/source_manifest.yaml") -> None:
    """Save source manifest to YAML."""
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

def update_manifest_with_checksum(
    manifest: Dict[str, Any],
    artifact_name: str,
    artifact_path: str,
    source_name: Optional[str] = None
) -> Dict[str, Any]:
    """Update manifest with checksum for an artifact."""
    checksum = compute_file_checksum(artifact_path)
    timestamp = datetime.now().isoformat()
    
    # If source_name is provided, update the source entry
    if source_name and source_name in manifest.get("sources", {}):
        manifest["sources"][source_name]["status"] = "Verified"
        manifest["sources"][source_name]["last_updated"] = timestamp
        manifest["sources"][source_name]["checksum"] = checksum
    
    # Ensure processed artifact entry exists
    if "processed" not in manifest:
        manifest["processed"] = {}
    
    manifest["processed"][artifact_name] = {
        "path": artifact_path,
        "checksum": checksum,
        "created": timestamp,
        "status": "Verified"
    }
    
    return manifest

def main():
    """Main entry point for writing aligned events and updating manifest."""
    ensure_directories()
    
    # Load aligned events (assumed to be produced by align.py)
    input_path = "data/processed/aligned_events.csv"
    
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found. Please run align.py first.")
        sys.exit(1)
    
    events = load_aligned_events(input_path)
    print(f"Loaded {len(events)} aligned events from {input_path}")
    
    # Write aligned events (overwrite to ensure latest)
    write_aligned_events(events, input_path)
    print(f"Successfully wrote {len(events)} events to {input_path}")
    
    # Load manifest
    manifest_path = "data/source_manifest.yaml"
    manifest = load_manifest(manifest_path)
    
    # Update manifest with checksum for aligned_events
    manifest = update_manifest_with_checksum(
        manifest,
        artifact_name="aligned_events",
        artifact_path=input_path,
        source_name=None  # This is a derived artifact, not a source
    )
    
    # Save updated manifest
    save_manifest(manifest, manifest_path)
    print(f"Updated manifest at {manifest_path} with aligned_events checksum")
    
    # Verify the update
    manifest = load_manifest(manifest_path)
    if "processed" in manifest and "aligned_events" in manifest["processed"]:
        entry = manifest["processed"]["aligned_events"]
        print(f"Verified: aligned_events checksum = {entry['checksum'][:16]}...")
        print(f"Status: {entry['status']}, Created: {entry['created']}")
    else:
        print("Warning: Could not verify aligned_events entry in manifest")

if __name__ == "__main__":
    main()
