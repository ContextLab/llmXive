import os
import sys
import hashlib
import yaml
from pathlib import Path
from datetime import datetime, timezone

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the SHA-256 hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def main():
    """
    Generate initial project state YAML file with content hashes.
    
    This script satisfies Constitution Principle V by recording the
    cryptographic hashes of the project's dependency configuration files
    (requirements.txt and pyproject.toml) at the time of project initialization.
    """
    # Determine project root (assume running from code/scripts/)
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    
    # Define target files relative to project root
    requirements_path = project_root / "requirements.txt"
    pyproject_path = project_root / "pyproject.toml"
    
    # Define output path
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    project_id = "PROJ-500-neural-correlates-of-predictive-error-si"
    output_path = state_dir / f"{project_id}.yaml"
    
    # Verify input files exist
    missing_files = []
    if not requirements_path.exists():
        missing_files.append(str(requirements_path))
    if not pyproject_path.exists():
        missing_files.append(str(pyproject_path))
        
    if missing_files:
        print(f"ERROR: Required configuration files missing: {', '.join(missing_files)}")
        print("Ensure requirements.txt and pyproject.toml exist before generating project state.")
        sys.exit(1)
    
    # Compute hashes
    try:
        requirements_hash = compute_file_hash(requirements_path)
        pyproject_hash = compute_file_hash(pyproject_path)
    except (FileNotFoundError, IOError) as e:
        print(f"ERROR: Failed to compute file hashes: {e}")
        sys.exit(1)
    
    # Construct state dictionary
    project_state = {
        "project_id": project_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "constitution_principle_v": {
            "description": "Content hashes of dependency configuration files",
            "files": {
                "requirements.txt": {
                    "path": str(requirements_path.relative_to(project_root)),
                    "sha256": requirements_hash
                },
                "pyproject.toml": {
                    "path": str(pyproject_path.relative_to(project_root)),
                    "sha256": pyproject_hash
                }
            }
        },
        "git_status": {
            "initialized": True,
            "note": "Git repository initialized in T005c"
        }
    }
    
    # Write YAML output
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(project_state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        print(f"SUCCESS: Project state written to {output_path}")
        print(f"  - requirements.txt hash: {requirements_hash[:16]}...")
        print(f"  - pyproject.toml hash: {pyproject_hash[:16]}...")
    except IOError as e:
        print(f"ERROR: Failed to write project state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()