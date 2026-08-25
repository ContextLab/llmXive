import os
import hashlib
from pathlib import Path
from typing import Optional
import json

# Define the project root relative to this file's location
# The project structure is: code/setup_directories.py, so root is parent of parent?
# Actually, based on tasks.md, root is `projects/PROJ-065-assessing-the-generalizability-of-statis/`
# and code/ is inside it.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUTS = PROJECT_ROOT / "outputs"
OUTPUTS_FIGURES = OUTPUTS / "figures"
OUTPUTS_REPORTS = OUTPUTS / "reports"
STATE_DIR = PROJECT_ROOT / "state"
STATE_FILE = STATE_DIR / "projects" / "PROJ-065-assessing-the-generalizability-of-statis.yaml"

def ensure_directory_structure() -> None:
    """
    Creates the required directory structure for the project.
    Includes:
    - data/raw/
    - data/processed/
    - outputs/figures/
    - outputs/reports/
    - state/projects/ (for artifact tracking)
    
    Raises:
        OSError: If directories cannot be created.
    """
    dirs = [
        DATA_RAW,
        DATA_PROCESSED,
        OUTPUTS,
        OUTPUTS_FIGURES,
        OUTPUTS_REPORTS,
        STATE_DIR,
        STATE_FILE.parent,
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        # Ensure .gitkeep exists in each directory to preserve them in git
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> Optional[str]:
    """
    Calculates the hash of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hex digest string or None if file doesn't exist.
    """
    if not file_path.exists():
        return None
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def calculate_directory_hash(dir_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculates a deterministic hash representing the content of a directory.
    This iterates over all files, sorts them by path, and hashes their contents
    concatenated with their relative paths to ensure structural changes are detected.
    
    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use.
        
    Returns:
        Hex digest string representing the directory state.
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    hash_func = hashlib.new(algorithm)
    # Update with directory path to distinguish between different root dirs
    hash_func.update(str(dir_path).encode('utf-8'))
    
    # Collect all files
    files = []
    for root, _, filenames in os.walk(dir_path):
        for filename in filenames:
            if filename == ".gitkeep":
                continue
            f_path = Path(root) / filename
            rel_path = f_path.relative_to(dir_path)
            files.append((rel_path, f_path))
    
    # Sort by relative path for determinism
    files.sort(key=lambda x: x[0])
    
    for rel_path, f_path in files:
        # Include relative path in hash
        hash_func.update(str(rel_path).encode('utf-8'))
        # Include file content in hash
        if f_path.exists():
            file_hash = calculate_file_hash(f_path, algorithm)
            if file_hash:
                hash_func.update(file_hash.encode('utf-8'))
        
    return hash_func.hexdigest()

def create_initial_files() -> None:
    """
    Creates initial placeholder files if they don't exist.
    Currently ensures .gitkeep files are present in all data directories.
    """
    ensure_directory_structure()
    # The ensure_directory_structure already creates .gitkeep, 
    # but we can add specific READMEs if needed later.

def main() -> None:
    """
    Entry point for the setup script.
    Creates directories and prints a summary hash of the data directories.
    """
    print("Setting up project directory structure...")
    ensure_directory_structure()
    
    print(f"Created: {DATA_RAW}")
    print(f"Created: {DATA_PROCESSED}")
    print(f"Created: {OUTPUTS_FIGURES}")
    print(f"Created: {OUTPUTS_REPORTS}")
    
    # Calculate and print initial hashes
    if DATA_RAW.exists():
        raw_hash = calculate_directory_hash(DATA_RAW)
        print(f"Initial hash for data/raw/: {raw_hash}")
    
    if DATA_PROCESSED.exists():
        proc_hash = calculate_directory_hash(DATA_PROCESSED)
        print(f"Initial hash for data/processed/: {proc_hash}")
        
    print("Setup complete.")

if __name__ == "__main__":
    main()
