import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate the content hash of a file."""
    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files without OOM
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error hashing file {file_path}: {e}")

def should_include_file(file_path: Path, project_root: Path) -> bool:
    """
    Determine if a file should be included in the manifest.
    Excludes:
    - __pycache__ directories
    - .git directories
    - .pyc files
    - Temporary files (~)
    - The manifest itself (to avoid circular dependency)
    - data/raw/* (raw data is usually large and handled separately, 
      but we include processed data)
    """
    path_str = str(file_path)
    
    # Skip hidden files/dirs and pycache
    if any(part.startswith('.') for part in file_path.parts) or '__pycache__' in path_str:
        return False
    
    # Skip compiled python
    if file_path.suffix == '.pyc':
        return False
    
    # Skip the manifest file itself
    if file_path.name == 'manifest.json':
        return False

    # We generally include code, processed data, and config
    # Exclude raw data if it's massive, but the task asks for a manifest of artifacts.
    # We will include everything under code/, config/, data/processed/, tests/
    # and exclude data/raw/ if it exists to keep manifest size manageable.
    try:
        rel_path = file_path.relative_to(project_root)
        if rel_path.parts and rel_path.parts[0] == 'data' and len(rel_path.parts) > 1 and rel_path.parts[1] == 'raw':
            return False
    except ValueError:
        return False
        
    return True

def generate_manifest(project_root: Path, output_path: Path) -> Dict[str, Any]:
    """
    Recursively walk the project root and generate a manifest of content hashes.
    """
    manifest = {
        "generated_by": "code/src/pipeline/manifest.py",
        "project_root": str(project_root),
        "files": {}
    }

    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)
        
        # Filter out excluded directories on the fly
        dirs[:] = [d for d in dirs if d != '__pycache__' and not d.startswith('.')]
        
        for file in files:
            file_path = root_path / file
            
            if not should_include_file(file_path, project_root):
                continue
            
            try:
                file_hash = calculate_file_hash(file_path)
                rel_path = str(file_path.relative_to(project_root))
                manifest["files"][rel_path] = {
                    "hash": file_hash,
                    "size_bytes": file_path.stat().st_size
                }
            except (FileNotFoundError, RuntimeError) as e:
                # Log error but continue processing other files
                print(f"Warning: Skipping {file_path}: {e}", file=sys.stderr)

    return manifest

def write_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """Write the manifest dictionary to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

def main():
    """
    Entry point for the manifest generation script.
    Generates data/processed/manifest.json containing hashes of code, config, and processed data.
    """
    # Determine project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent # code/src/pipeline -> code -> root
    
    output_file = project_root / "data" / "processed" / "manifest.json"
    
    print(f"Generating manifest for project at: {project_root}")
    print(f"Output will be written to: {output_file}")
    
    try:
        manifest = generate_manifest(project_root, output_file)
        write_manifest(manifest, output_file)
        print(f"Manifest generated successfully with {len(manifest['files'])} files.")
    except Exception as e:
        print(f"Failed to generate manifest: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()