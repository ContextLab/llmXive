import os
import json
from datetime import datetime
from pathlib import Path

def ensure_directories(base_path: str) -> None:
    """Create the required project directory structure."""
    paths = [
        os.path.join(base_path, "code"),
        os.path.join(base_path, "data"),
        os.path.join(base_path, "data", "raw"),
        os.path.join(base_path, "data", "processed"),
        os.path.join(base_path, "data", "final"),
        os.path.join(base_path, "data", "logs"),
        os.path.join(base_path, "tests"),
        os.path.join(base_path, "docs"),
    ]
    for path in paths:
        os.makedirs(path, exist_ok=True)

def verify_directories(base_path: str) -> list:
    """Verify that the required directories exist and return their paths."""
    required_paths = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/final",
        "data/logs",
        "tests",
        "docs",
    ]
    verified = []
    for rel_path in required_paths:
        full_path = os.path.join(base_path, rel_path)
        if os.path.isdir(full_path):
            verified.append(rel_path)
    return verified

def log_setup_status(base_path: str, status: str, verified_paths: list) -> dict:
    """Create the setup log JSON file."""
    log_entry = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "paths_verified": verified_paths,
    }
    log_path = os.path.join(base_path, "data", "setup_log.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_entry, f, indent=2)
    return log_entry

def main():
    """Main entry point for the setup task."""
    base_path = Path(__file__).resolve().parent.parent
    ensure_directories(str(base_path))
    verified = verify_directories(str(base_path))
    
    if len(verified) == 8:
        log_setup_status(str(base_path), "SUCCESS", verified)
        print("Setup completed successfully. Directories verified.")
    else:
        log_setup_status(str(base_path), "FAILED", verified)
        raise RuntimeError(f"Directory verification failed. Only {len(verified)} paths verified.")

if __name__ == "__main__":
    main()
