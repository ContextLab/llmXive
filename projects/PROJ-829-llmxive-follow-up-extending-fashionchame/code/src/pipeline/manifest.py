"""
Manifest generator for content hashing of code and data artifacts.
Implements FR-013: Generate a manifest.json with content hashes for all
artifacts in the project tree (code/, data/, tests/).
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Supported extensions for hashing
CODE_EXTENSIONS = {'.py', '.yaml', '.yml', '.json', '.md', '.txt', '.sh'}
DATA_EXTENSIONS = {'.csv', '.parquet', '.json', '.txt', '.png', '.jpg', '.jpeg', '.pt', '.pth', '.h5', '.npy'}
TEST_EXTENSIONS = {'.py'}

# Directories to include
TARGET_DIRS = ['code', 'data', 'tests']

def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate the hash of a file's contents.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
    
    Returns:
        Hexadecimal hash string
    """
    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to read file {file_path} for hashing: {e}")

def should_include_file(file_path: Path) -> bool:
    """
    Determine if a file should be included in the manifest based on extension.
    
    Args:
        file_path: Path to the file
    
    Returns:
        True if the file should be included, False otherwise
    """
    suffix = file_path.suffix.lower()
    parent = file_path.parent.name
    
    # Include based on directory context
    if parent == 'code' or parent == 'src':
        return suffix in CODE_EXTENSIONS
    elif parent == 'data' or 'data' in str(file_path):
        return suffix in DATA_EXTENSIONS
    elif parent == 'tests' or parent == 'unit' or parent == 'integration':
        return suffix in TEST_EXTENSIONS
    elif suffix in CODE_EXTENSIONS:
        # Fallback for files in root or other dirs with code extensions
        return True
    
    return False

def generate_manifest(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate a manifest of all artifacts in the project with their content hashes.
    
    Args:
        project_root: Path to the project root. Defaults to current working directory.
    
    Returns:
        Dictionary containing the manifest data
    """
    if project_root is None:
        project_root = Path.cwd()
    
    artifacts = []
    
    for dir_name in TARGET_DIRS:
        target_dir = project_root / dir_name
        if not target_dir.exists():
            continue
        
        for file_path in target_dir.rglob('*'):
            if file_path.is_file() and should_include_file(file_path):
                try:
                    file_hash = calculate_file_hash(file_path)
                    relative_path = file_path.relative_to(project_root)
                    
                    # Get file size
                    file_size = file_path.stat().st_size
                    
                    artifact_entry = {
                        'path': str(relative_path),
                        'hash': file_hash,
                        'algorithm': 'sha256',
                        'size_bytes': file_size
                    }
                    artifacts.append(artifact_entry)
                except Exception as e:
                    # Log error but continue processing other files
                    print(f"Warning: Could not hash {file_path}: {e}", file=sys.stderr)
    
    manifest = {
        'version': '1.0',
        'generated_at': None,  # Will be set by caller if needed
        'project_root': str(project_root),
        'artifacts': artifacts,
        'total_artifacts': len(artifacts)
    }
    
    return manifest

def write_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """
    Write the manifest to a JSON file.
    
    Args:
        manifest: The manifest dictionary to write
        output_path: Path where the manifest should be written
    """
    # Add timestamp if not present
    if 'generated_at' not in manifest or manifest['generated_at'] is None:
        from datetime import datetime
        manifest['generated_at'] = datetime.utcnow().isoformat() + 'Z'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

def main():
    """
    Main entry point for generating the manifest.
    Reads project root from environment or uses current directory.
    Outputs manifest to data/processed/manifest.json.
    """
    # Determine project root
    project_root = Path(os.environ.get('PROJECT_ROOT', Path.cwd()))
    
    # Ensure we are at the project root level (where code/, data/, tests/ are)
    if not (project_root / 'code').exists() and not (project_root / 'data').exists():
        # Try to find project root by looking for known directories
        current = project_root
        while current != current.parent:
            if (current / 'code').exists() or (current / 'data').exists():
                project_root = current
                break
            current = current.parent
    
    print(f"Generating manifest for project at: {project_root}")
    
    # Generate manifest
    manifest = generate_manifest(project_root)
    
    # Define output path
    output_dir = project_root / 'data' / 'processed'
    output_path = output_dir / 'manifest.json'
    
    # Write manifest
    write_manifest(manifest, output_path)
    
    print(f"Manifest written to: {output_path}")
    print(f"Total artifacts hashed: {manifest['total_artifacts']}")
    
    return manifest

if __name__ == '__main__':
    main()
