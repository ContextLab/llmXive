"""
Task T017b: Verify preprocessing outputs.

Pre-requisite: T017a must complete.
Logic: Verify file existence, non-empty content, and record SHA256 checksums 
in state/artifact_hashes.yaml. If files are missing or empty, raise an error and halt.
"""
import os
import sys
import json
import hashlib
import yaml
from pathlib import Path
from typing import List, Dict, Any

# Constants based on project structure
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STATE_DIR = PROJECT_ROOT / "state"
ARTIFACT_HASHES_FILE = STATE_DIR / "artifact_hashes.yaml"

# Expected outputs from T017a (preprocess.py)
EXPECTED_FILES = [
    "batch_corrected_matrix.csv",
    "labels.csv",
    "preprocess_log.json"
]

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Failed to compute hash for {file_path}: {e}")

def check_file_non_empty(file_path: Path) -> bool:
    """Check if a file exists and has non-zero size."""
    if not file_path.exists():
        return False
    return file_path.stat().st_size > 0

def load_artifact_manifest() -> Dict[str, Any]:
    """Load existing artifact manifest or return empty dict."""
    if ARTIFACT_HASHES_FILE.exists():
        try:
            with open(ARTIFACT_HASHES_FILE, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}
    return {}

def save_artifact_manifest(manifest: Dict[str, Any]) -> None:
    """Save artifact manifest to YAML file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(ARTIFACT_HASHES_FILE, "w") as f:
        yaml.safe_dump(manifest, f, default_flow_style=False, sort_keys=False)

def verify_preprocessing_outputs() -> bool:
    """
    Main verification logic for T017b.
    
    Returns True if all checks pass, raises exception otherwise.
    """
    errors = []
    manifest = load_artifact_manifest()
    
    print(f"Verifying preprocessing outputs in {DATA_PROCESSED_DIR}...")
    
    for filename in EXPECTED_FILES:
        file_path = DATA_PROCESSED_DIR / filename
        
        # Check existence
        if not file_path.exists():
            errors.append(f"MISSING: {filename} does not exist")
            continue
        
        # Check non-empty
        if not check_file_non_empty(file_path):
            errors.append(f"EMPTY: {filename} exists but is empty")
            continue
        
        # Compute checksum
        try:
            checksum = compute_sha256(file_path)
            print(f"  ✓ {filename}: {checksum[:16]}... ({file_path.stat().st_size} bytes)")
            
            # Update manifest
            manifest[filename] = {
                "checksum": checksum,
                "path": str(file_path.relative_to(PROJECT_ROOT)),
                "verified": True
            }
        except Exception as e:
            errors.append(f"ERROR: Failed to process {filename}: {str(e)}")
    
    # Validate specific content for preprocess_log.json
    log_path = DATA_PROCESSED_DIR / "preprocess_log.json"
    if log_path.exists() and check_file_non_empty(log_path):
        try:
            with open(log_path, "r") as f:
                log_data = json.load(f)
            
            # Check for essential keys
            required_keys = ["batch_correction", "features_retained", "samples_retained"]
            missing_keys = [k for k in required_keys if k not in log_data]
            if missing_keys:
                errors.append(f"INCOMPLETE LOG: preprocess_log.json missing keys: {missing_keys}")
            else:
                print(f"  ✓ preprocess_log.json contains required metadata")
        except json.JSONDecodeError:
            errors.append("INVALID: preprocess_log.json is not valid JSON")
        except Exception as e:
            errors.append(f"ERROR: Failed to validate preprocess_log.json: {str(e)}")
    
    # Save updated manifest
    save_artifact_manifest(manifest)
    print(f"\nArtifact manifest updated: {ARTIFACT_HASHES_FILE}")
    
    if errors:
        error_msg = "Preprocessing verification FAILED:\n" + "\n".join(f"  - {e}" for e in errors)
        raise RuntimeError(error_msg)
    
    print("\n✓ All preprocessing outputs verified successfully!")
    return True

def main():
    """Entry point for T017b."""
    try:
        success = verify_preprocessing_outputs()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
