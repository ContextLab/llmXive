"""
Stimulus Content Hashing Module.

Computes SHA-256 hashes for all HTML stimulus files to ensure
experimental consistency and prevent silent drift in conditions.
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any

# Import shared helper for project root and file operations
# Note: We import the specific function to avoid circular dependencies if any
try:
    from utils.helpers import get_project_root
except ImportError:
    # Fallback if running as __main__ or in a different context
    def get_project_root() -> Path:
        """Return the project root directory."""
        return Path(__file__).resolve().parent.parent.parent

STIMULI_DIR_NAME = "stimuli"
STATE_DIR_NAME = "state"
HASHES_FILENAME = "stimuli_hashes.json"
EXCLUDED_FILES = {".gitkeep", ".DS_Store"}


def compute_file_sha256(filepath: Path) -> str:
    """
    Compute SHA-256 hash of a file's contents.
    
    Args:
        filepath: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read in chunks to handle large files efficiently
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_stimuli_files(stimuli_dir: Path) -> list:
    """
    Get a list of all HTML stimulus files in the stimuli directory.
    
    Args:
        stimuli_dir: Path to the stimuli directory.
        
    Returns:
        List of Path objects for HTML files.
    """
    if not stimuli_dir.exists():
        raise FileNotFoundError(f"Stimuli directory not found: {stimuli_dir}")
        
    html_files = []
    for file_path in stimuli_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() == ".html":
            if file_path.name not in EXCLUDED_FILES:
                html_files.append(file_path)
                
    return sorted(html_files)


def compute_stimuli_hashes(stimuli_dir: Path = None) -> Dict[str, str]:
    """
    Compute hashes for all stimulus files in the directory.
    
    Args:
        stimuli_dir: Optional path to stimuli directory. Defaults to project default.
        
    Returns:
        Dictionary mapping filename to SHA-256 hash.
    """
    if stimuli_dir is None:
        root = get_project_root()
        stimuli_dir = root / STIMULI_DIR_NAME
        
    hashes = {}
    files = get_stimuli_files(stimuli_dir)
    
    for file_path in files:
        try:
            file_hash = compute_file_sha256(file_path)
            hashes[file_path.name] = file_hash
        except Exception as e:
            raise IOError(f"Failed to hash {file_path.name}: {e}")
            
    return hashes


def load_stored_hashes(state_dir: Path = None) -> Dict[str, str]:
    """
    Load previously stored hashes from the state file.
    
    Args:
        state_dir: Optional path to state directory. Defaults to project default.
        
    Returns:
        Dictionary of stored hashes.
    """
    if state_dir is None:
        root = get_project_root()
        state_dir = root / STATE_DIR_NAME
        
    hash_file = state_dir / HASHES_FILENAME
    
    if not hash_file.exists():
        return {}
        
    try:
        with open(hash_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("stimuli_hashes", {})
    except (json.JSONDecodeError, IOError) as e:
        raise IOError(f"Failed to load stored hashes: {e}")


def save_stimuli_hashes(hashes: Dict[str, str], state_dir: Path = None) -> None:
    """
    Save computed hashes to the state file.
    
    Args:
        hashes: Dictionary of filename -> hash.
        state_dir: Optional path to state directory.
    """
    if state_dir is None:
        root = get_project_root()
        state_dir = root / STATE_DIR_NAME
        
    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)
    
    hash_file = state_dir / HASHES_FILENAME
    
    output_data = {
        "stimuli_hashes": hashes,
        "generated_at": "now" # In a real implementation, use datetime.now().isoformat()
    }
    
    # Write atomically to prevent partial writes
    temp_file = hash_file.with_suffix(".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        os.replace(temp_file, hash_file)
    except Exception as e:
        # Clean up temp file if write fails
        if temp_file.exists():
            temp_file.unlink()
        raise IOError(f"Failed to save hashes: {e}")


def verify_stimuli_integrity(stimuli_dir: Path = None, state_dir: Path = None) -> bool:
    """
    Verify that current stimulus files match stored hashes.
    
    This is the critical check used before survey launch.
    
    Args:
        stimuli_dir: Path to stimuli directory.
        state_dir: Path to state directory.
        
    Returns:
        True if all hashes match.
        
    Raises:
        RuntimeError: If any hash mismatch is detected or if state file is missing.
    """
    if state_dir is None:
        root = get_project_root()
        state_dir = root / STATE_DIR_NAME
        
    stored_hashes = load_stored_hashes(state_dir)
    
    if not stored_hashes:
        raise RuntimeError(
            "No stored hashes found in state/stimuli_hashes.json. "
            "Run the initialization step first."
        )
        
    if stimuli_dir is None:
        root = get_project_root()
        stimuli_dir = root / STIMULI_DIR_NAME
        
    current_files = get_stimuli_files(stimuli_dir)
    
    # Check for missing files
    stored_names = set(stored_hashes.keys())
    current_names = {f.name for f in current_files}
    
    missing = stored_names - current_names
    extra = current_names - stored_names
    
    if missing:
        raise RuntimeError(f"Stimulus files missing from disk: {missing}")
    if extra:
        raise RuntimeError(f"Unexpected stimulus files found: {extra}")
        
    # Verify content
    mismatches = []
    for file_path in current_files:
        current_hash = compute_file_sha256(file_path)
        stored_hash = stored_hashes.get(file_path.name)
        
        if stored_hash is None:
            mismatches.append((file_path.name, "No stored hash"))
        elif current_hash != stored_hash:
            mismatches.append((file_path.name, "Hash mismatch"))
            
    if mismatches:
        error_msg = "Stimulus integrity check FAILED:\n"
        for name, reason in mismatches:
            error_msg += f"  - {name}: {reason}\n"
        error_msg += "\nHALTING: Survey launch blocked due to stimulus drift."
        raise RuntimeError(error_msg)
        
    return True


def initialize_stimuli_hashes(stimuli_dir: Path = None, state_dir: Path = None) -> None:
    """
    Compute and save initial hashes for all stimulus files.
    
    This should be run once during project setup or after any stimulus update.
    
    Args:
        stimuli_dir: Path to stimuli directory.
        state_dir: Path to state directory.
    """
    if stimuli_dir is None:
        root = get_project_root()
        stimuli_dir = root / STIMULI_DIR_NAME
        
    if state_dir is None:
        root = get_project_root()
        state_dir = root / STATE_DIR_NAME
        
    hashes = compute_stimuli_hashes(stimuli_dir)
    save_stimuli_hashes(hashes, state_dir)
    
    print(f"Initialized {len(hashes)} stimulus hashes.")
    for name, h in hashes.items():
        print(f"  {name}: {h[:16]}...")


def main():
    """
    Command-line entry point for stimulus hashing.
    
    Usage:
        python -m code.utils.stimuli_hash init    # Initialize/Update hashes
        python -m code.utils.stimuli_hash verify  # Verify integrity
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m code.utils.stimuli_hash <init|verify>")
        sys.exit(1)
        
    command = sys.argv[1].lower()
    
    try:
        if command == "init":
            initialize_stimuli_hashes()
        elif command == "verify":
            verify_stimuli_integrity()
            print("Stimulus integrity verified successfully.")
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
