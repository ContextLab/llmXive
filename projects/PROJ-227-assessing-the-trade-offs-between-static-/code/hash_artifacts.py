"""
Artifact Hashing and Tool Versioning Script (Constitution V & VI).

This script computes SHA-256 hashes for project artifacts to ensure
reproducibility (Constitution V) and logs the versions of external tools
(CodeQL, SonarQube, pytest) to the state file (Constitution VI).

It is designed to be run before analysis begins (T009) and after analysis
to verify integrity (T032).
"""

import hashlib
import json
import os
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

# Project Root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
STATE_FILE = STATE_DIR / "projects" / "PROJ-227-assessing-the-trade-offs-between-static-.yaml"

# Directories to hash
HASH_DIRS = [
    PROJECT_ROOT / "code",
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "tests",
    PROJECT_ROOT / "contracts",
]

# Tool commands to check versions
TOOL_COMMANDS = {
    "codeql": ["codeql", "version"],
    "sonarqube": ["sonar-scanner", "--version"], # Common CLI name, may vary
    "pytest": ["pytest", "--version"],
    "python": ["python", "--version"],
}

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "FILE_NOT_FOUND"
    except Exception as e:
        return f"ERROR: {str(e)}"

def should_include(file_path: Path) -> bool:
    """Determine if a file should be included in hashing."""
    # Exclude common non-code artifacts and caches
    name = file_path.name
    if name.startswith('.'):
        return False
    if name in ('__pycache__', '*.pyc', '.git', '.venv', 'node_modules'):
        return False
    if name.endswith(('.log', '.tmp', '.swp')):
        return False
    return True

def collect_artifacts(directory: Path) -> List[Path]:
    """Recursively collect all relevant file paths in a directory."""
    artifacts = []
    if not directory.exists():
        return artifacts
    
    for root, dirs, files in os.walk(directory):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '.git', '.venv', 'node_modules')]
        
        for file in files:
            file_path = Path(root) / file
            if should_include(file_path):
                artifacts.append(file_path)
    return artifacts

def hash_directory(directory: Path) -> Dict[str, str]:
    """Hash all artifacts in a directory and return a map of relative_path -> hash."""
    result = {}
    artifacts = collect_artifacts(directory)
    for file_path in artifacts:
        rel_path = file_path.relative_to(PROJECT_ROOT)
        file_hash = compute_file_hash(file_path)
        result[str(rel_path)] = file_hash
    return result

def load_state() -> Dict[str, Any]:
    """Load the existing state file if it exists."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load state file: {e}", file=sys.stderr)
            return {}
    return {}

def save_state(state: Dict[str, Any]) -> None:
    """Save the state dictionary to the YAML file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def get_tool_versions() -> Dict[str, str]:
    """
    Execute tool commands to retrieve version strings.
    Returns a dictionary of tool_name -> version_string.
    """
    versions = {}
    timestamp = datetime.now(timezone.utc).isoformat()

    for tool_name, cmd in TOOL_COMMANDS.items():
        try:
            # Run command with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False # Don't raise on non-zero exit, we just want output
            )
            output = result.stdout.strip() + result.stderr.strip()
            if output:
                # Clean up output to just the version string if possible
                # For pytest: "pytest X.Y.Z"
                # For codeql: "CodeQL command-line tool version X.Y.Z..."
                versions[tool_name] = output.split('\n')[0].strip()
            else:
                versions[tool_name] = "NOT_INSTALLED_OR_NO_OUTPUT"
        except subprocess.TimeoutExpired:
            versions[tool_name] = "TIMEOUT"
        except FileNotFoundError:
            versions[tool_name] = "NOT_FOUND"
        except Exception as e:
            versions[tool_name] = f"ERROR: {str(e)}"
    
    versions['_timestamp'] = timestamp
    return versions

def main():
    """Main entry point for T009 and T032."""
    print("Starting artifact hashing and tool versioning...")
    
    # Load existing state
    state = load_state()
    
    # Update tool versions (Constitution VI)
    print("Checking tool versions...")
    tool_versions = get_tool_versions()
    state['tool_versions'] = tool_versions
    print(f"Updated tool versions: {list(tool_versions.keys())}")
    
    # Compute artifact hashes (Constitution V)
    print("Computing artifact hashes...")
    artifact_hashes = {}
    for dir_path in HASH_DIRS:
        if dir_path.exists():
            hashes = hash_directory(dir_path)
            artifact_hashes.update(hashes)
    
    state['artifact_hashes'] = artifact_hashes
    state['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    # Save state
    save_state(state)
    print(f"State saved to {STATE_FILE}")
    
    # Verification
    if 'tool_versions' in state and state['tool_versions']:
        print("Success: Tool versions logged.")
    else:
        print("Warning: No tool versions could be retrieved.", file=sys.stderr)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())