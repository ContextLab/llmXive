import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_artifacts(base_dirs: List[str]) -> List[Dict[str, Any]]:
    """Scan directories for artifacts and compute checksums."""
    artifacts = []
    for base_dir in base_dirs:
        base_path = Path(base_dir)
        if not base_path.exists():
            continue
        for file_path in base_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                rel_path = file_path.relative_to(Path.cwd())
                checksum = compute_sha256(str(file_path))
                size = file_path.stat().st_size
                artifacts.append({
                    "path": str(rel_path),
                    "checksum": checksum,
                    "size_bytes": size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
    return artifacts

def generate_state_file(artifacts: List[Dict[str, Any]], output_path: str) -> None:
    """Generate a YAML-like state file with artifact checksums."""
    state = {
        "project_id": "PROJ-300-exploring-the-relationship-between-solar",
        "generated_at": datetime.now().isoformat(),
        "artifacts": artifacts
    }
    # Write as JSON for simplicity (YAML generation requires pyyaml which is a dependency)
    # The state format is effectively a structured data file
    with open(output_path, 'w') as f:
        json.dump(state, f, indent=2)

def verify_checksums(state_path: str) -> bool:
    """Verify checksums of artifacts against a state file."""
    with open(state_path, 'r') as f:
        state = json.load(f)
    
    for artifact in state.get("artifacts", []):
        file_path = artifact["path"]
        expected_checksum = artifact["checksum"]
        
        if not os.path.exists(file_path):
            print(f"Missing: {file_path}")
            return False
        
        actual_checksum = compute_sha256(file_path)
        if actual_checksum != expected_checksum:
            print(f"Checksum mismatch: {file_path}")
            print(f"  Expected: {expected_checksum}")
            print(f"  Actual:   {actual_checksum}")
            return False
    
    return True

def main():
    """Main entry point for checksum generation and verification."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python checksums.py [generate|verify] [output_path]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "generate":
        output_path = sys.argv[2] if len(sys.argv) > 2 else "state/projects/PROJ-300-exploring-the-relationship-between-solar.yaml"
        base_dirs = ["data/processed", "data/raw", "results"]
        artifacts = scan_artifacts(base_dirs)
        generate_state_file(artifacts, output_path)
        print(f"State file generated: {output_path}")
        print(f"Total artifacts: {len(artifacts)}")
    
    elif command == "verify":
        state_path = sys.argv[2] if len(sys.argv) > 2 else "state/projects/PROJ-300-exploring-the-relationship-between-solar.yaml"
        if verify_checksums(state_path):
            print("All checksums verified successfully.")
        else:
            print("Checksum verification failed.")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
