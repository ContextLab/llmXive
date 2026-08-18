import os
import sys
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Optional

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error computing hash for {file_path}: {e}")

def scan_directory(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
    """Scan a directory for files, optionally filtering by extension."""
    files = []
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    
    for file_path in dir_path.rglob('*'):
        if file_path.is_file():
            if extensions is None or any(file_path.suffix == ext for ext in extensions):
                # Skip hidden checksum files and __pycache__
                if file_path.name.startswith('.') or '__pycache__' in str(file_path):
                    continue
                files.append(str(file_path))
    return files

def load_existing_checksums(state_file: str) -> Dict[str, Dict[str, str]]:
    """Load existing checksums from the state YAML file."""
    state_path = Path(state_file)
    if not state_path.exists():
        return {}
    
    try:
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f)
            return state.get('artifact_hashes', {})
    except Exception as e:
        raise RuntimeError(f"Error loading state file {state_file}: {e}")

def save_checksums(state_file: str, checksums: Dict[str, Dict[str, str]]) -> None:
    """Save updated checksums to the state YAML file."""
    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load existing state to preserve other fields like updated_at
        existing_state = {}
        if state_path.exists():
            with open(state_path, 'r') as f:
                existing_state = yaml.safe_load(f) or {}
        
        existing_state['artifact_hashes'] = checksums
        existing_state['updated_at'] = None  # Reset or update as needed, task doesn't specify a value source
        
        with open(state_path, 'w') as f:
            yaml.dump(existing_state, f, default_flow_style=False)
    except Exception as e:
        raise RuntimeError(f"Error saving state file {state_file}: {e}")

def verify_data_integrity(directory: str, existing_checksums: Dict[str, str]) -> Dict[str, bool]:
    """Verify data integrity by comparing computed hashes with existing ones."""
    results = {}
    files = scan_directory(directory)
    
    for file_path in files:
        try:
            current_hash = compute_sha256(file_path)
            # Use relative path from project root for comparison if stored that way
            # Assuming keys in existing_checksums might be relative or full paths
            # We will store relative paths in the state file for consistency
            rel_path = os.path.relpath(file_path, start=os.getcwd())
            
            if rel_path in existing_checksums:
                is_valid = existing_checksums[rel_path] == current_hash
                results[rel_path] = is_valid
            else:
                # New file, no existing checksum to compare against, mark as new/valid
                results[rel_path] = True
        except Exception as e:
            results[os.path.relpath(file_path, start=os.getcwd())] = False
            print(f"Error verifying {file_path}: {e}", file=sys.stderr)
    
    return results

def update_checksums(directory: str, current_checksums: Dict[str, str]) -> Dict[str, str]:
    """Update checksums for all files in the directory."""
    files = scan_directory(directory)
    new_checksums = {}
    
    for file_path in files:
        try:
            rel_path = os.path.relpath(file_path, start=os.getcwd())
            new_checksums[rel_path] = compute_sha256(file_path)
        except Exception as e:
            print(f"Error hashing {file_path}: {e}", file=sys.stderr)
    
    return new_checksums

def main():
    """Main entry point for checksum verification and state update."""
    project_root = Path(__file__).resolve().parent.parent
    state_file = project_root / "state" / "projects" / "PROJ-860-llmxive-follow-up-extending-dragmesh-2-p.yaml"
    data_raw_dir = project_root / "data" / "raw"
    data_generated_dir = project_root / "data" / "generated"
    
    # Ensure state file exists (initialized in T009)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    if not state_file.exists():
        # Initialize empty state if missing, though T009 should have created it
        with open(state_file, 'w') as f:
            yaml.dump({'artifact_hashes': {}, 'updated_at': None}, f)
    
    # Load existing checksums from state
    existing_state = load_existing_checksums(str(state_file))
    raw_checksums = existing_state.get('data_raw', {})
    generated_checksums = existing_state.get('data_generated', {})
    
    all_checksums = {}
    
    # Process data/raw
    if data_raw_dir.exists():
        print(f"Scanning {data_raw_dir}...")
        # Verify existing
        verify_data_integrity(str(data_raw_dir), raw_checksums)
        # Update checksums
        raw_checksums = update_checksums(str(data_raw_dir), raw_checksums)
        all_checksums['data_raw'] = raw_checksums
    else:
        print(f"Warning: Directory {data_raw_dir} does not exist.", file=sys.stderr)
    
    # Process data/generated
    if data_generated_dir.exists():
        print(f"Scanning {data_generated_dir}...")
        # Verify existing
        verify_data_integrity(str(data_generated_dir), generated_checksums)
        # Update checksums
        generated_checksums = update_checksums(str(data_generated_dir), generated_checksums)
        all_checksums['data_generated'] = generated_checksums
    else:
        print(f"Warning: Directory {data_generated_dir} does not exist.", file=sys.stderr)
    
    # Save updated checksums to state
    save_checksums(str(state_file), all_checksums)
    print(f"Checksums updated successfully in {state_file}")

if __name__ == "__main__":
    main()
