import argparse
import hashlib
import json
import os
import sys
import datetime
from pathlib import Path

# Project root is the parent of the code directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories to scan for artifacts
ARTIFACT_DIRS = [
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "code",
    PROJECT_ROOT / "contracts",
    PROJECT_ROOT / "figures",
]

# Files to exclude from hashing (e.g., state files, logs, caches)
EXCLUDE_PATTERNS = {
    "state_hashes.json",
    "exclusions.csv",
    "runtime_log.json",
    "processing.log",
    ".gitkeep",
}

# Output path for the state file
STATE_FILE_PATH = PROJECT_ROOT / "data" / "state_hashes.json"


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the hash of a file's contents."""
    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"Error computing hash for {file_path}: {e}", file=sys.stderr)
        return ""


def find_artifacts() -> list:
    """Find all relevant artifacts in the project directories."""
    artifacts = []
    for directory in ARTIFACT_DIRS:
        if not directory.exists():
            continue
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                # Check exclusions
                if file_path.name in EXCLUDE_PATTERNS:
                    continue
                if "state_hashes.json" in str(file_path):
                    continue
                artifacts.append(file_path)
    return artifacts


def load_state() -> dict:
    """Load the existing state file if it exists."""
    if STATE_FILE_PATH.exists():
        try:
            with open(STATE_FILE_PATH, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load state file: {e}", file=sys.stderr)
            return {}
    return {}


def save_state(state: dict) -> None:
    """Save the state to the state file."""
    STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE_PATH, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    print(f"State saved to {STATE_FILE_PATH}")


def generate_hashes() -> dict:
    """Generate hashes for all current artifacts."""
    artifacts = find_artifacts()
    state = {
        "version": 1,
        "generated_at": datetime.datetime.now().isoformat(),
        "hashes": {}
    }
    
    for file_path in artifacts:
        rel_path = str(file_path.relative_to(PROJECT_ROOT))
        file_hash = compute_file_hash(file_path)
        if file_hash:
            state["hashes"][rel_path] = file_hash
    
    return state


def verify_hashes(new_state: dict, old_state: dict) -> bool:
    """Verify if the new hashes match the old state."""
    if not old_state or not old_state.get("hashes"):
        print("No previous state found to verify against.")
        return False

    new_hashes = new_state.get("hashes", {})
    old_hashes = old_state.get("hashes", {})

    all_match = True
    mismatches = []

    # Check for missing or changed files
    for path, old_hash in old_hashes.items():
        if path not in new_hashes:
            print(f"MISSING: {path}")
            all_match = False
        elif new_hashes[path] != old_hash:
            print(f"CHANGED: {path}")
            mismatches.append(path)
            all_match = False

    # Check for new files (optional: depending on strictness, new files might be okay)
    # For verification, we usually care if existing files changed.
    # If strict integrity is needed, we might flag new files too.
    # Here we just report changes.
    
    if all_match:
        print("Verification passed: No changes detected in tracked artifacts.")
    else:
        print(f"Verification failed: {len(mismatches)} files changed or missing.")
    
    return all_match


def main():
    parser = argparse.ArgumentParser(
        description="Generate or verify content hashes for project artifacts."
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify current artifacts against the saved state file.",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate new hashes and save them to the state file.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force generation even if verification is requested first.",
    )

    args = parser.parse_args()

    # Default behavior: if no args, generate
    if not args.generate and not args.verify:
        args.generate = True

    if args.verify:
        current_state = generate_hashes()
        previous_state = load_state()
        if not previous_state:
            print("No previous state file found. Generating new state.")
            save_state(current_state)
        else:
            if not verify_hashes(current_state, previous_state):
                if not args.force:
                    print("Use --force to update state despite mismatches.")
                    sys.exit(1)
                else:
                    print("Updating state despite mismatches...")
                    save_state(current_state)
    elif args.generate:
        new_state = generate_hashes()
        save_state(new_state)


if __name__ == "__main__":
    main()