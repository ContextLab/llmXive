"""
Final verification script for T041.
Verifies that all data artifacts in data/derived/ are present and match
the hashes recorded in state/manifest.json.
"""
import json
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the manifest JSON file."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

def verify_artifacts(
    derived_dir: Path, 
    manifest: Dict[str, Any]
) -> Tuple[List[str], List[str], List[str]]:
    """
    Verify all artifacts in derived_dir against manifest.
    
    Returns:
        Tuple of (missing_files, hash_mismatches, verified_files)
    """
    missing_files = []
    hash_mismatches = []
    verified_files = []
    
    # Build a map of expected files from manifest
    manifest_files = {}
    for entry in manifest.get("files", []):
        path_str = entry.get("path", "")
        # Filter for data/derived/ files
        if path_str.startswith("data/derived/"):
            manifest_files[path_str] = entry.get("sha256")
    
    if not manifest_files:
        print("WARNING: No data/derived/ files found in manifest.")
        return [], [], []

    # Check each file in the manifest
    for rel_path, expected_hash in manifest_files.items():
        full_path = derived_dir.parent / rel_path  # derived_dir is inside data/
        
        if not full_path.exists():
            missing_files.append(rel_path)
            continue
        
        actual_hash = calculate_sha256(full_path)
        
        if actual_hash is None:
            missing_files.append(rel_path)
            continue
        
        if actual_hash != expected_hash:
            hash_mismatches.append({
                "path": rel_path,
                "expected": expected_hash,
                "actual": actual_hash
            })
        else:
            verified_files.append(rel_path)
    
    # Also check if there are files in derived_dir not in manifest
    if derived_dir.exists():
        for file_path in derived_dir.iterdir():
            if file_path.is_file():
                rel_path = f"data/derived/{file_path.name}"
                if rel_path not in manifest_files:
                    # File exists but not in manifest - this might be expected 
                    # for new files, but we flag it
                    print(f"WARNING: File in data/derived/ not in manifest: {rel_path}")
    
    return missing_files, hash_mismatches, verified_files

def main():
    """Main entry point for verification."""
    project_root = Path(__file__).parent.parent
    derived_dir = project_root / "data" / "derived"
    manifest_path = project_root / "state" / "manifest.json"
    
    print(f"Project root: {project_root}")
    print(f"Derived directory: {derived_dir}")
    print(f"Manifest path: {manifest_path}")
    
    if not manifest_path.exists():
        print("ERROR: state/manifest.json does not exist.")
        print("Run the manifest generation task (T010) first.")
        sys.exit(1)
    
    if not derived_dir.exists():
        print("ERROR: data/derived/ directory does not exist.")
        sys.exit(1)
    
    try:
        manifest = load_manifest(manifest_path)
    except Exception as e:
        print(f"ERROR: Failed to load manifest: {e}")
        sys.exit(1)
    
    missing_files, hash_mismatches, verified_files = verify_artifacts(
        derived_dir, manifest
    )
    
    print("\n" + "="*60)
    print("VERIFICATION RESULTS")
    print("="*60)
    
    if verified_files:
        print(f"\n✓ VERIFIED ({len(verified_files)} files):")
        for f in verified_files:
            print(f"  - {f}")
    
    if missing_files:
        print(f"\n✗ MISSING ({len(missing_files)} files):")
        for f in missing_files:
            print(f"  - {f}")
    
    if hash_mismatches:
        print(f"\n⚠ HASH MISMATCHES ({len(hash_mismatches)} files):")
        for mismatch in hash_mismatches:
            print(f"  - {mismatch['path']}")
            print(f"    Expected: {mismatch['expected']}")
            print(f"    Actual:   {mismatch['actual']}")
    
    print("\n" + "="*60)
    
    if missing_files or hash_mismatches:
        print("RESULT: VERIFICATION FAILED")
        sys.exit(1)
    else:
        print("RESULT: VERIFICATION PASSED")
        print("All data artifacts in data/derived/ match state/manifest.json")
        sys.exit(0)

if __name__ == "__main__":
    main()
