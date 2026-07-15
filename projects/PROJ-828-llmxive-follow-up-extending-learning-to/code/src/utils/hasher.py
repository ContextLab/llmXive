"""
Utility module for computing and managing SHA-256 hashes of derived artifacts.
Ensures data integrity and reproducibility for the llmXive pipeline.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

# Ensure imports work whether running as module or script
if __name__ != "__main__" and "code" not in sys.path:
    # Try to add code/ to path if running from within code/
    code_root = Path(__file__).resolve().parent.parent.parent
    if code_root.name == "code":
        sys.path.insert(0, str(code_root))

from src.utils.seeds import set_seed

def compute_file_hash(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read (default 8KB).

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def compute_directory_hash(dir_path: Union[str, Path], 
                           extensions: Optional[List[str]] = None,
                           exclude_dirs: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Compute SHA-256 hashes for all files in a directory (recursive).
    
    Args:
        dir_path: Path to the directory.
        extensions: Optional list of file extensions to include (e.g., ['.pt', '.npy']).
                   If None, all files are included.
        exclude_dirs: Optional list of directory names to exclude (e.g., ['__pycache__', '.git']).

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    dir_path = Path(dir_path)
    if not dir_path.exists() or not dir_path.is_dir():
        raise NotADirectoryError(f"Directory not found or invalid: {dir_path}")
    
    if exclude_dirs is None:
        exclude_dirs = ['__pycache__', '.git', '.pytest_cache']
    
    hashes = {}
    
    for root, dirs, files in os.walk(dir_path):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if extensions is not None:
                if not any(file.endswith(ext) for ext in extensions):
                    continue
            
            file_path = Path(root) / file
            rel_path = file_path.relative_to(dir_path)
            try:
                hashes[str(rel_path)] = compute_file_hash(file_path)
            except (FileNotFoundError, PermissionError) as e:
                # Log warning but continue
                print(f"Warning: Could not hash {file_path}: {e}", file=sys.stderr)
    
    return hashes

def save_hash_manifest(hashes: Dict[str, str], output_path: Union[str, Path]) -> None:
    """
    Save a dictionary of hashes to a JSON manifest file.
    
    Args:
        hashes: Dictionary mapping file paths to hashes.
        output_path: Path where the manifest will be saved.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    manifest = {
        "algorithm": "sha256",
        "files": hashes
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

def load_hash_manifest(manifest_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load a hash manifest from a JSON file.
    
    Args:
        manifest_path: Path to the manifest file.
        
    Returns:
        Dictionary mapping file paths to hashes.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if "files" not in data:
        raise ValueError("Invalid manifest format: missing 'files' key")
    
    return data["files"]

def verify_artifacts(hashes: Dict[str, str], base_path: Union[str, Path]) -> Dict[str, bool]:
    """
    Verify that files match their recorded hashes.
    
    Args:
        hashes: Dictionary mapping relative file paths to expected hashes.
        base_path: Base directory where files are located.
        
    Returns:
        Dictionary mapping file paths to verification status (True = valid).
    """
    base_path = Path(base_path)
    results = {}
    
    for rel_path, expected_hash in hashes.items():
        file_path = base_path / rel_path
        if not file_path.exists():
            results[rel_path] = False
            continue
        
        try:
            actual_hash = compute_file_hash(file_path)
            results[rel_path] = (actual_hash == expected_hash)
        except Exception:
            results[rel_path] = False
    
    return results

def generate_artifact_hash(content: Union[str, bytes]) -> str:
    """
    Generate SHA-256 hash for in-memory content.
    
    Args:
        content: String or bytes to hash.
        
    Returns:
        Hexadecimal SHA-256 hash.
    """
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()

def main():
    """
    CLI entry point for hashing utilities.
    Usage:
      python -m src.utils.hasher <command> [options]
    
    Commands:
      file <path>              - Hash a single file
      dir <path>               - Hash all files in a directory
      verify <manifest> <base> - Verify files against a manifest
      save <manifest_path>     - Save hashes to manifest (used with dir)
    """
    if len(sys.argv) < 2:
        print("Usage: python -m src.utils.hasher <command> [args]")
        print("Commands: file, dir, verify, save")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "file" and len(sys.argv) >= 3:
        path = sys.argv[2]
        try:
            hash_val = compute_file_hash(path)
            print(f"{hash_val}  {path}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
            
    elif command == "dir" and len(sys.argv) >= 3:
        path = sys.argv[2]
        exts = None
        if len(sys.argv) >= 5 and sys.argv[3] == "--ext":
            exts = sys.argv[4].split(",")
        
        try:
            hashes = compute_directory_hash(path, extensions=exts)
            for rel_path, hash_val in sorted(hashes.items()):
                print(f"{hash_val}  {rel_path}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
            
    elif command == "verify" and len(sys.argv) >= 4:
        manifest_path = sys.argv[2]
        base_path = sys.argv[3]
        try:
            hashes = load_hash_manifest(manifest_path)
            results = verify_artifacts(hashes, base_path)
            
            all_valid = all(results.values())
            for path, valid in results.items():
                status = "✓" if valid else "✗"
                print(f"{status} {path}")
            
            sys.exit(0 if all_valid else 1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
            
    elif command == "save" and len(sys.argv) >= 4:
        # Usage: save <manifest_path> <dir_path> [exts]
        manifest_path = sys.argv[2]
        dir_path = sys.argv[3]
        exts = None
        if len(sys.argv) >= 6 and sys.argv[4] == "--ext":
            exts = sys.argv[5].split(",")
        
        try:
            hashes = compute_directory_hash(dir_path, extensions=exts)
            save_hash_manifest(hashes, manifest_path)
            print(f"Manifest saved to: {manifest_path}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
            
    else:
        print(f"Unknown command or missing arguments: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
