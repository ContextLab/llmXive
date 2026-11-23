"""
Utility to update data_manifest.json with placeholder entries for missing sources.
This supports spec-amendment T018a.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

from code.config import DATA_MANIFEST_PATH, DATA_RAW_PATH
from code.errors import ManifestError

def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    if not file_path.exists():
        return "N/A"
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest() -> dict:
    """Load the current data manifest."""
    if not DATA_MANIFEST_PATH.exists():
        return {"entries": []}
    with open(DATA_MANIFEST_PATH, "r") as f:
        return json.load(f)

def save_manifest(manifest: dict) -> None:
    """Save the updated manifest."""
    with open(DATA_MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

def update_manifest_with_placeholder(
    source_type: str,
    system_name: str,
    reason: str,
    verification_ref: str
) -> None:
    """
    Add a placeholder entry to the manifest for a missing source.
    Implements T018a requirements.
    """
    manifest = load_manifest()
    
    entry_id = f"{source_type}_{system_name}_placeholder"
    
    # Determine file path for the placeholder
    placeholder_filename = f"{source_type}_{system_name}_no_data.json"
    placeholder_path = DATA_RAW_PATH / placeholder_filename
    
    # Create the placeholder file if it doesn't exist
    if not placeholder_path.exists():
        placeholder_data = {
            "status": "no_data",
            "reason": reason,
            "system": system_name,
            "source_type": source_type,
            "verification_ref": verification_ref,
            "timestamp": datetime.utcnow().isoformat()
        }
        with open(placeholder_path, "w") as f:
            json.dump(placeholder_data, f, indent=2)
    
    # Calculate checksum of the placeholder file
    checksum = calculate_file_checksum(placeholder_path)
    
    new_entry = {
        "source_id": entry_id,
        "source_type": "placeholder",
        "system": system_name,
        "doi": "N/A",
        "url": "N/A",
        "checksum": checksum,
        "status": "no_data",
        "reason": reason,
        "verification_ref": verification_ref,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Check for duplicate
    existing_ids = [e.get("source_id") for e in manifest.get("entries", [])]
    if entry_id not in existing_ids:
        manifest["entries"].append(new_entry)
        save_manifest(manifest)
        print(f"Updated manifest with placeholder for {source_type} {system_name}")
    else:
        print(f"Entry {entry_id} already exists in manifest.")

def main():
    """
    Example usage:
    python -m code.data.update_manifest_with_placeholder \
        --source_type calphad --system Fe-Cr-Mo --reason no_source_found \
        --verification_ref "research/data_sources.md#T045e-Verify"
    """
    import argparse
    parser = argparse.ArgumentParser(description="Update manifest with placeholder for missing data")
    parser.add_argument("--source_type", required=True, help="Type of source (calphad, dft)")
    parser.add_argument("--system", required=True, help="System name (e.g., Fe-Cr-Mo)")
    parser.add_argument("--reason", required=True, help="Reason for missing data (no_source_found, fetch_failed)")
    parser.add_argument("--verification_ref", required=True, help="Reference to verification log")
    
    args = parser.parse_args()
    
    try:
        update_manifest_with_placeholder(
            source_type=args.source_type,
            system_name=args.system,
            reason=args.reason,
            verification_ref=args.verification_ref
        )
    except Exception as e:
        print(f"Error updating manifest: {e}")
        raise ManifestError(f"Failed to update manifest: {e}")

if __name__ == "__main__":
    main()
