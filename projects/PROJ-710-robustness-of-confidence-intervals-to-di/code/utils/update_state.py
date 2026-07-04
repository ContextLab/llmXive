"""
Post-run artifact hashing and state updates for the CI robustness simulation.

This module provides utilities to:
1. Compute cryptographic hashes (SHA-256) for all generated artifacts in the `artifacts/` directory.
2. Generate a deterministic `state.json` manifest recording the hash of every output file,
   the git commit hash (if available), and the timestamp of the run.
3. Update the project state to ensure reproducibility and integrity checks.
"""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import project config to resolve paths dynamically
# Assuming the script is run from the project root or code/ directory
# We use a relative import approach or sys.path manipulation if run as a script
try:
    from code.config import ARTIFACTS_DIR, PROJECT_ROOT
except ImportError:
    # Fallback for direct execution without package structure in path
    import sys
    from pathlib import Path

    # Add project root to path if running as __main__
    _current_dir = Path(__file__).resolve().parent
    _project_root = _current_dir.parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))
    
    from code.config import ARTIFACTS_DIR, PROJECT_ROOT


def compute_file_hash(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "file_not_found"
    except Exception as e:
        return f"error_hashing: {str(e)}"


def get_git_commit_hash() -> Optional[str]:
    """
    Retrieve the current git commit hash.

    Returns:
        Short git commit hash string, or None if not in a git repo.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=PROJECT_ROOT
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def scan_artifacts(artifacts_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Scan the artifacts directory for all files and compute their hashes.

    Args:
        artifacts_dir: Path to the artifacts directory. Defaults to config.ARTIFACTS_DIR.

    Returns:
        List of dictionaries containing file info (path, size, hash).
    """
    if artifacts_dir is None:
        artifacts_dir = Path(ARTIFACTS_DIR)
    
    if not artifacts_dir.exists():
        return []

    file_manifest = []
    for file_path in artifacts_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(artifacts_dir)
            file_info = {
                "path": str(relative_path),
                "size_bytes": file_path.stat().st_size,
                "hash_sha256": compute_file_hash(file_path),
                "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            file_manifest.append(file_info)
    
    # Sort for deterministic ordering
    file_manifest.sort(key=lambda x: x["path"])
    return file_manifest


def update_state_manifest(
    output_path: Optional[Path] = None,
    artifacts_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate and save the state manifest (state.json).

    This function scans the artifacts directory, computes hashes,
    and writes a JSON file containing the run state.

    Args:
        output_path: Path to write the state.json. Defaults to PROJECT_ROOT / "state.json".
        artifacts_dir: Path to the artifacts directory to scan.

    Returns:
        The generated state dictionary.
    """
    if output_path is None:
        output_path = Path(PROJECT_ROOT) / "state.json"
    if artifacts_dir is None:
        artifacts_dir = Path(ARTIFACTS_DIR)

    manifest = {
        "generated_at": datetime.now().isoformat(),
        "git_commit": get_git_commit_hash(),
        "artifacts_directory": str(artifacts_dir),
        "files": scan_artifacts(artifacts_dir)
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"State manifest written to: {output_path}")
    print(f"Total artifacts hashed: {len(manifest['files'])}")
    
    return manifest


def verify_state_integrity(
    state_path: Optional[Path] = None,
    artifacts_dir: Optional[Path] = None
) -> bool:
    """
    Verify that the current artifacts match the recorded hashes in state.json.

    Args:
        state_path: Path to the state.json file.
        artifacts_dir: Path to the artifacts directory.

    Returns:
        True if all hashes match, False otherwise.
    """
    if state_path is None:
        state_path = Path(PROJECT_ROOT) / "state.json"
    if artifacts_dir is None:
        artifacts_dir = Path(ARTIFACTS_DIR)

    if not state_path.exists():
        print(f"State file not found: {state_path}")
        return False

    with open(state_path, "r", encoding="utf-8") as f:
        saved_state = json.load(f)

    current_files = {item["path"]: item for item in scan_artifacts(artifacts_dir)}
    saved_files = {item["path"]: item for item in saved_state["files"]}

    if set(current_files.keys()) != set(saved_files.keys()):
        print("File set mismatch between current state and saved state.")
        return False

    all_match = True
    for path, saved_info in saved_files.items():
        current_info = current_files[path]
        if current_info["hash_sha256"] != saved_info["hash_sha256"]:
            print(f"Hash mismatch for {path}:")
            print(f"  Saved:  {saved_info['hash_sha256']}")
            print(f"  Current: {current_info['hash_sha256']}")
            all_match = False

    if all_match:
        print("Integrity check passed: All artifact hashes match.")
    else:
        print("Integrity check FAILED: Some artifacts have changed.")
    
    return all_match


def main() -> None:
    """
    CLI entry point for updating and verifying state.
    Usage: python -m code.utils.update_state [update|verify]
    """
    if len(sys.argv) < 2:
        print("Usage: python -m code.utils.update_state [update|verify]")
        print("  update  - Scan artifacts and write state.json")
        print("  verify  - Check current artifacts against state.json")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "update":
        update_state_manifest()
    elif command == "verify":
        success = verify_state_integrity()
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()