"""
Versioning utilities for llmXive.

Implements Constitution Principle V: Compute SHA-256 hashes of code/ and data/
directories and update the state/ YAML file to track experiment reproducibility.
"""

import hashlib
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Constants relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
STATE_DIR = PROJECT_ROOT / "state"
STATE_FILE = STATE_DIR / "version_state.yaml"

# Paths to exclude from hashing (e.g., generated artifacts, caches)
EXCLUDED_PATTERNS = {
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".git",
    ".env",
    "*.log",
    "*.tmp",
    "models",  # Often large, versioned separately if needed
}


def _should_exclude(file_path: Path) -> bool:
    """Check if a file or directory should be excluded from hashing."""
    parts = file_path.parts
    for part in parts:
        if part in EXCLUDED_PATTERNS:
            return True
        if part.startswith(".") and part not in {".", ".."}:
            # Exclude hidden files/dirs unless they are config files
            if part in {".gitignore", ".env.example", ".gitkeep"}:
                continue
            return True
    return False


def _compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a single file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to read file {file_path} for hashing: {e}")


def _compute_directory_hash(dir_path: Path) -> str:
    """
    Compute a deterministic SHA-256 hash for a directory.

    The hash is derived by sorting all files by relative path and
    concatenating their individual hashes.
    """
    if not dir_path.exists():
        return hashlib.sha256(b"").hexdigest()  # Hash of empty

    file_hashes = []
    all_files = sorted(dir_path.rglob("*"))

    for file_path in all_files:
        if not file_path.is_file():
            continue
        if _should_exclude(file_path.relative_to(dir_path)):
            continue
        try:
            file_hash = _compute_file_hash(file_path)
            # Include relative path in the hash input to ensure path changes matter
            rel_path = str(file_path.relative_to(dir_path))
            file_hashes.append(f"{rel_path}:{file_hash}")
        except RuntimeError:
            # Skip files that can't be read
            continue

    combined_string = "\n".join(file_hashes)
    return hashlib.sha256(combined_string.encode("utf-8")).hexdigest()


def compute_version_state() -> Dict[str, Any]:
    """
    Compute the current version state of the project.

    Returns a dictionary containing:
    - timestamp: ISO format string
    - code_hash: SHA-256 of the code/ directory
    - data_hash: SHA-256 of the data/ directory
    - git_commit: (Optional) Current git commit hash if available
    """
    timestamp = datetime.utcnow().isoformat() + "Z"

    code_hash = _compute_directory_hash(CODE_DIR)
    data_hash = _compute_directory_hash(DATA_DIR)

    git_commit = None
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=5
        )
        if result.returncode == 0:
            git_commit = result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Git not available or not a git repo
        pass

    return {
        "timestamp": timestamp,
        "code_hash": code_hash,
        "data_hash": data_hash,
        "git_commit": git_commit,
    }


def update_state_file(
    state: Optional[Dict[str, Any]] = None,
    append_history: bool = True
) -> Path:
    """
    Update the state YAML file with the new version information.

    Args:
        state: Pre-computed state dict. If None, computes fresh.
        append_history: If True, appends the new state to a history list.
                       If False, overwrites the root keys.

    Returns:
        Path to the updated state file.
    """
    if state is None:
        state = compute_version_state()

    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    existing_data = {}
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                existing_data = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            existing_data = {}

    if append_history:
        history = existing_data.get("history", [])
        # Add current state to history with a run_id (timestamp-based)
        run_entry = {
            "run_id": state["timestamp"].replace(":", "-").replace(".", "-"),
            **state
        }
        history.append(run_entry)
        existing_data["history"] = history
        # Keep top-level keys updated as well for quick access
        existing_data["latest"] = state
    else:
        existing_data.update(state)

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        yaml.dump(existing_data, f, default_flow_style=False, sort_keys=False)

    return STATE_FILE


def get_latest_state() -> Optional[Dict[str, Any]]:
    """Retrieve the latest state from the state file."""
    if not STATE_FILE.exists():
        return None
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("latest") or data
    except yaml.YAMLError:
        return None


if __name__ == "__main__":
    # CLI entry point for manual updates
    print("Computing project version state...")
    state = compute_version_state()
    print(f"Code Hash: {state['code_hash'][:16]}...")
    print(f"Data Hash: {state['data_hash'][:16]}...")
    if state['git_commit']:
        print(f"Git Commit: {state['git_commit'][:8]}")
    print(f"Timestamp: {state['timestamp']}")

    file_path = update_state_file(state)
    print(f"State updated in {file_path}")
