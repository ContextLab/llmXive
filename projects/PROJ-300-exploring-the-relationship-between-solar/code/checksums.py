"""
Checksum and state management for PROJ-300.
Implements Constitution Principle V: Verify all artifacts are checksummed and recorded.
"""
import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent

# Directories to scan
ARTIFACT_DIRS = [
    "code",
    "data",
    "tests",
    "specs",
    "results"
]

# File extensions to include
FILE_EXTENSIONS = {
    ".py", ".txt", ".md", ".json", ".csv", ".png", ".yaml", ".yml", ".log"
}

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Failed to compute hash for {file_path}: {e}")

def scan_artifacts(root_dir: Path) -> List[Dict[str, Any]]:
    """
    Scan project directories for artifacts and compute their checksums.
    Returns a list of artifact records.
    """
    artifacts = []
    for dir_name in ARTIFACT_DIRS:
        dir_path = root_dir / dir_name
        if not dir_path.exists():
            continue
        
        for file_path in dir_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in FILE_EXTENSIONS:
                # Skip __pycache__ and hidden files
                if "__pycache__" in str(file_path) or file_path.name.startswith("."):
                    continue
                
                rel_path = file_path.relative_to(root_dir)
                checksum = compute_sha256(file_path)
                size_bytes = file_path.stat().st_size
                
                artifacts.append({
                    "path": str(rel_path),
                    "checksum": checksum,
                    "size_bytes": size_bytes,
                    "type": file_path.suffix.lower()
                })
    
    return artifacts

def generate_state_file(artifacts: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generate a JSON state file recording all artifacts and their checksums.
    """
    state = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project_id": "PROJ-300-exploring-the-relationship-between-solar",
        "constitution_principle": "V",
        "artifact_count": len(artifacts),
        "artifacts": artifacts
    }
    
    with open(output_path, "w") as f:
        json.dump(state, f, indent=2)

def verify_checksums(state_path: Path) -> bool:
    """
    Verify that current artifacts match the recorded checksums in the state file.
    Returns True if all checksums match, False otherwise.
    """
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")
    
    with open(state_path, "r") as f:
        state = json.load(f)
    
    root_dir = state_path.parent
    all_match = True
    mismatches = []
    
    for artifact in state["artifacts"]:
        file_path = root_dir / artifact["path"]
        if not file_path.exists():
            mismatches.append(f"MISSING: {artifact['path']}")
            all_match = False
            continue
        
        current_checksum = compute_sha256(file_path)
        if current_checksum != artifact["checksum"]:
            mismatches.append(
                f"MISMATCH: {artifact['path']} "
                f"(expected: {artifact['checksum'][:16]}..., "
                f"got: {current_checksum[:16]}...)"
            )
            all_match = False
    
    if mismatches:
        print("Checksum verification FAILED:")
        for m in mismatches:
            print(f"  - {m}")
        return False
    
    print(f"Checksum verification PASSED: {len(state['artifacts'])} artifacts verified.")
    return True

def main():
    """Main entry point for checksum generation and verification."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Artifact checksum management")
    parser.add_argument(
        "--mode",
        choices=["generate", "verify"],
        default="generate",
        help="Mode: generate new state or verify against existing"
    )
    parser.add_argument(
        "--state-file",
        default=str(PROJECT_ROOT / "data" / "processed" / "project_state.json"),
        help="Path to the state file"
    )
    
    args = parser.parse_args()
    
    if args.mode == "generate":
        print(f"Scanning artifacts in {PROJECT_ROOT}...")
        artifacts = scan_artifacts(PROJECT_ROOT)
        
        if not artifacts:
            print("WARNING: No artifacts found to checksum.")
            return 1
        
        state_path = Path(args.state_file)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        generate_state_file(artifacts, state_path)
        
        print(f"State file generated: {state_path}")
        print(f"Total artifacts: {len(artifacts)}")
        return 0
    
    elif args.mode == "verify":
        state_path = Path(args.state_file)
        if not state_path.exists():
            print(f"ERROR: State file not found: {state_path}")
            return 1
        
        success = verify_checksums(state_path)
        return 0 if success else 1

if __name__ == "__main__":
    exit(main())
