import os
import hashlib
import sys
import yaml
from pathlib import Path
from code.config import DATA_RAW_DIR, DATA_CHECKSUMS_FILE, STATE_FILE

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_raw_directory() -> None:
    """Ensure the data/raw directory exists."""
    Path(DATA_RAW_DIR).mkdir(parents=True, exist_ok=True)

def load_checksums() -> dict:
    """Load existing checksums from the state file."""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f) or {}
            return state.get("artifact_hashes", {})
    except Exception:
        return {}

def save_checksums(checksums: dict) -> None:
    """Save checksums to the state file."""
    ensure_raw_directory()
    state_path = Path(STATE_FILE)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    state = {}
    if state_path.exists():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state = yaml.safe_load(f) or {}
        except Exception:
            state = {}
    
    state["artifact_hashes"] = checksums
    state["last_updated"] = str(Path(STATE_FILE).stat().st_mtime)
    
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False)

def verify_file(file_path: str, expected_hash: str) -> bool:
    """Verify a file's hash against the expected hash."""
    if not os.path.exists(file_path):
        return False
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def compute_and_store_checksum(file_path: str, artifact_name: str) -> str:
    """Compute checksum for a file and store it in the state file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    checksum = compute_sha256(file_path)
    checksums = load_checksums()
    checksums[artifact_name] = checksum
    save_checksums(checksums)
    return checksum

def verify_all() -> bool:
    """Verify all artifacts listed in the state file."""
    checksums = load_checksums()
    all_valid = True
    
    for artifact_name, expected_hash in checksums.items():
        # Construct path relative to project root
        # Assuming artifact_name is relative to data/raw or similar
        if artifact_name.startswith("data/"):
            file_path = artifact_name
        else:
            file_path = os.path.join("data", "raw", artifact_name)
        
        if not verify_file(file_path, expected_hash):
            print(f"Verification FAILED for {file_path}")
            all_valid = False
        else:
            print(f"Verification PASSED for {file_path}")
    
    return all_valid

def store_all() -> None:
    """Compute and store checksums for all files in data/raw/."""
    ensure_raw_directory()
    checksums = load_checksums()
    
    raw_dir = Path(DATA_RAW_DIR)
    for file_path in raw_dir.glob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(Path.cwd()))
            print(f"Storing checksum for {rel_path}")
            checksums[rel_path] = compute_sha256(str(file_path))
    
    save_checksums(checksums)

def main():
    """Main entry point for checksum verification."""
    if len(sys.argv) < 2:
        print("Usage: python -m code.checksum_verify <command> [args]")
        print("Commands: verify, store, compute <file_path>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "verify":
        if verify_all():
            print("All artifacts verified successfully.")
            sys.exit(0)
        else:
            print("Verification failed for some artifacts.")
            sys.exit(1)
    elif command == "store":
        store_all()
        print("All checksums stored successfully.")
        sys.exit(0)
    elif command == "compute":
        if len(sys.argv) < 3:
            print("Usage: python -m code.checksum_verify compute <file_path>")
            sys.exit(1)
        file_path = sys.argv[2]
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        checksum = compute_and_store_checksum(file_path, file_path)
        print(f"Checksum for {file_path}: {checksum}")
        sys.exit(0)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
