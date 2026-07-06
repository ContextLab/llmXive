import os
import hashlib
import datetime
import yaml
import sys

def create_structure():
    """Create the project directory structure as defined in T001."""
    dirs = [
        "code/data",
        "code/features",
        "code/models",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "results",
        "state"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"Created directory: {d}")

def calculate_file_checksum(filepath):
    """Calculate SHA-256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None

def calculate_directory_checksums(root_dir):
    """Calculate checksums for all files in the project structure."""
    checksums = {}
    for root, _, files in os.walk(root_dir):
        # Skip state directory to avoid infinite recursion or self-modification issues
        if "state" in root.split(os.sep):
            continue
        for file in files:
            filepath = os.path.join(root, file)
            # Skip this script itself in checksums to avoid circular dependency
            if "setup_structure.py" in filepath:
                continue
            checksum = calculate_file_checksum(filepath)
            if checksum:
                rel_path = os.path.relpath(filepath, root_dir)
                checksums[rel_path] = checksum
    return checksums

def update_state(checksums):
    """Update the state.yaml file with checksums and timestamp."""
    state_file = "state/state.yaml"
    os.makedirs("state", exist_ok=True)
    
    state_data = {
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "checksums": checksums,
        "task_id": "T001",
        "status": "completed"
    }
    
    with open(state_file, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    print(f"Updated state file: {state_file}")

def main():
    """Main entry point for T001 implementation."""
    print("Starting T001: Create project structure...")
    create_structure()
    
    # Calculate checksums for the newly created structure (excluding state file itself)
    # We calculate checksums of the structure definition or a marker file if empty
    # For T001, since files are empty, we might just log the structure creation
    # But to satisfy the requirement, we create a marker or log the directories
    
    # Since directories are empty, we create a .gitkeep in each to have something to checksum
    # Or we just update state with a timestamp and note that structure is created
    # Let's create .gitkeep files to ensure we have content to checksum
    for d in ["code/data", "code/features", "code/models", "tests/unit", "tests/integration", "data/raw", "data/processed", "results"]:
        gitkeep_path = os.path.join(d, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, "w") as f:
                f.write("# Placeholder to ensure directory exists in version control\n")
    
    checksums = calculate_directory_checksums(".")
    update_state(checksums)
    print("T001 completed successfully.")

if __name__ == "__main__":
    main()