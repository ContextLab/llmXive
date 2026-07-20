import os
import hashlib
import sys
import yaml
from pathlib import Path

from code.config import DATA_RAW_DIR, DATA_CHECKSUMS_FILE, STATE_FILE

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error computing hash for {file_path}: {e}")

def ensure_raw_directory() -> None:
    """Ensure the data/raw/ directory exists."""
    Path(DATA_RAW_DIR).mkdir(parents=True, exist_ok=True)

def load_checksums() -> dict:
    """Load existing checksums from the state file."""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            state = yaml.safe_load(f)
            return state.get("artifact_hashes", {})
    except Exception:
        return {}

def save_checksums(checksums: dict) -> None:
    """Save checksums to the state file under artifact_hashes."""
    # Ensure state directory exists
    state_dir = os.path.dirname(STATE_FILE)
    if state_dir:
        Path(state_dir).mkdir(parents=True, exist_ok=True)

    # Load existing state or create new
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {}

    # Update artifact_hashes
    state["artifact_hashes"] = checksums

    # Write back
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False)

def verify_file(file_path: str, expected_hash: str) -> bool:
    """Verify a file's hash against an expected value."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found for verification: {file_path}")
    
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def compute_and_store_checksum(file_path: str) -> str:
    """Compute hash of a file and store it in state."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Cannot compute checksum: file not found {file_path}")
    
    file_name = os.path.basename(file_path)
    hash_value = compute_sha256(file_path)
    
    # Load existing checksums
    checksums = load_checksums()
    checksums[file_name] = hash_value
    
    # Save updated checksums
    save_checksums(checksums)
    
    print(f"Computed and stored checksum for {file_name}: {hash_value}")
    return hash_value

def verify_all() -> bool:
    """Verify all files in data/raw/ against stored checksums."""
    checksums = load_checksums()
    if not checksums:
        print("No checksums found in state file.")
        return True
    
    all_verified = True
    for file_name, expected_hash in checksums.items():
        file_path = os.path.join(DATA_RAW_DIR, file_name)
        if not os.path.exists(file_path):
            print(f"MISSING: {file_path}")
            all_verified = False
            continue
        
        try:
            actual_hash = compute_sha256(file_path)
            if actual_hash == expected_hash:
                print(f"VERIFIED: {file_name}")
            else:
                print(f"MISMATCH: {file_name} (expected {expected_hash}, got {actual_hash})")
                all_verified = False
        except Exception as e:
            print(f"ERROR verifying {file_name}: {e}")
            all_verified = False
    
    return all_verified

def store_all() -> None:
    """Compute and store checksums for all files in data/raw/."""
    if not os.path.exists(DATA_RAW_DIR):
        print(f"Directory not found: {DATA_RAW_DIR}")
        return
    
    files = [f for f in os.listdir(DATA_RAW_DIR) if os.path.isfile(os.path.join(DATA_RAW_DIR, f))]
    if not files:
        print("No files found in data/raw/ to checksum.")
        return
    
    checksums = load_checksums()
    for file_name in files:
        file_path = os.path.join(DATA_RAW_DIR, file_name)
        try:
            hash_value = compute_sha256(file_path)
            checksums[file_name] = hash_value
            print(f"Stored checksum for {file_name}: {hash_value}")
        except Exception as e:
            print(f"Error computing checksum for {file_name}: {e}")
    
    save_checksums(checksums)

def main():
    """Main entry point for checksum verification."""
    # Ensure directory exists
    ensure_raw_directory()
    
    # If argument is 'verify', verify existing
    # If argument is 'store', compute and store new
    # If no argument, do both (verify first, then store if missing)
    if len(sys.argv) > 1:
        action = sys.argv[1].lower()
    else:
        action = "auto"
    
    if action == "verify":
        if verify_all():
            print("All checksums verified.")
            sys.exit(0)
        else:
            print("Checksum verification failed.")
            sys.exit(1)
    elif action == "store":
        store_all()
        sys.exit(0)
    elif action == "auto":
        # Try to verify first
        if os.path.exists(DATA_CHECKSUMS_FILE) or os.path.exists(STATE_FILE):
            if verify_all():
                print("All checksums verified.")
                sys.exit(0)
            else:
                print("Verification failed or some files missing. Storing new checksums...")
        store_all()
        sys.exit(0)
    else:
        print(f"Unknown action: {action}. Use 'verify', 'store', or run without args.")
        sys.exit(1)

if __name__ == "__main__":
    main()
