"""
Artifact Hashing and Versioning Script (Constitution V)

This script computes cryptographic hashes (SHA-256) for all critical project
artifacts (code, data, configs, schemas) and records them in the state file.
This ensures reproducibility and versioning of the research pipeline.

Constitution Principle V: Reproducibility & Versioning
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

import yaml

# Project root relative to this script (assuming script is in code/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
CONFIG_PATH = PROJECT_ROOT / "code" / "config.yaml"
DATA_DIRS = [
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
]
CODE_DIR = PROJECT_ROOT / "code"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-227-assessing-the-trade-offs-between-static-.yaml"

# Patterns to include in hashing
INCLUDE_PATTERNS = [
    "*.py",
    "*.yaml",
    "*.json",
    "*.csv",
    "*.txt",
    "*.md",
    "*.schema.yaml",
]

# Patterns to exclude
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    ".git",
    ".venv",
    "*.log",
]

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return "ERROR_READING_FILE"

def should_include(path: Path, base_path: Path) -> bool:
    """Check if a file should be included in hashing based on patterns."""
    rel_path = path.relative_to(base_path)
    name = path.name
    suffix = path.suffix

    # Check exclusions
    for pattern in EXCLUDE_PATTERNS:
        if pattern in str(rel_path) or name == pattern:
            return False

    # Check inclusion patterns (suffix or full name match)
    for pattern in INCLUDE_PATTERNS:
        if pattern.startswith("*."):
            if suffix == pattern[1:]:
                return True
        elif pattern in name:
            return True
    
    return False

def collect_artifacts(base_path: Path) -> List[Path]:
    """Recursively collect all files matching inclusion patterns."""
    artifacts = []
    if not base_path.exists():
        return artifacts
    
    for root, dirs, files in os.walk(base_path):
        # Filter directories to avoid descending into excluded ones
        dirs[:] = [d for d in dirs if d not in EXCLUDE_PATTERNS]
        
        for file in files:
            file_path = Path(root) / file
            if should_include(file_path, base_path):
                artifacts.append(file_path)
    
    return sorted(artifacts)

def hash_directory(dir_path: Path) -> Dict[str, str]:
    """Hash all files in a directory recursively."""
    if not dir_path.exists():
        return {}
    
    artifacts = collect_artifacts(dir_path)
    hashes = {}
    for artifact in artifacts:
        rel_path = artifact.relative_to(PROJECT_ROOT)
        hashes[str(rel_path)] = compute_file_hash(artifact)
    
    return hashes

def load_state() -> Dict[str, Any]:
    """Load existing state file or return a fresh structure."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    return {
        "project_id": "PROJ-227-assessing-the-trade-offs-between-static-",
        "last_updated": None,
        "artifact_hashes": {},
        "tool_versions": {},
        "metadata": {}
    }

def save_state(state: Dict[str, Any]) -> None:
    """Save state to YAML file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def get_tool_versions() -> Dict[str, str]:
    """Attempt to detect versions of critical tools."""
    versions = {}
    
    # Check Python version
    versions["python"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Check common tools if available (non-blocking)
    tools_to_check = [
        ("codeql", ["codeql", "version"]),
        ("sonar-scanner", ["sonar-scanner", "--version"]),
        ("pytest", ["pytest", "--version"]),
        ("black", ["black", "--version"]),
    ]
    
    import subprocess
    for tool_name, cmd in tools_to_check:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                versions[tool_name] = result.stdout.strip()[:100]
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            versions[tool_name] = "NOT_INSTALLED"
    
    return versions

def main():
    """Main entry point for artifact hashing."""
    print(f"Starting artifact hashing for project: {PROJECT_ROOT.name}")
    
    # Initialize state
    state = load_state()
    
    # Collect hashes from key directories
    all_hashes = {}
    
    # Code
    if CODE_DIR.exists():
        code_hashes = hash_directory(CODE_DIR)
        all_hashes.update(code_hashes)
    
    # Contracts (Schemas)
    if CONTRACTS_DIR.exists():
        contract_hashes = hash_directory(CONTRACTS_DIR)
        all_hashes.update(contract_hashes)
    
    # Data (Raw and Processed)
    for data_dir in DATA_DIRS:
        if data_dir.exists():
            data_hashes = hash_directory(data_dir)
            all_hashes.update(data_hashes)
    
    # Config
    if CONFIG_PATH.exists():
        all_hashes[str(CONFIG_PATH.relative_to(PROJECT_ROOT))] = compute_file_hash(CONFIG_PATH)
    
    # Update state
    from datetime import datetime
    state["last_updated"] = datetime.utcnow().isoformat()
    state["artifact_hashes"] = all_hashes
    state["tool_versions"] = get_tool_versions()
    
    # Save state
    save_state(state)
    
    print(f"Successfully hashed {len(all_hashes)} artifacts.")
    print(f"State saved to: {STATE_FILE}")
    
    # Print summary
    print("\n--- Hash Summary ---")
    for path, hash_val in sorted(all_hashes.items()):
        print(f"{path}: {hash_val[:16]}...")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())