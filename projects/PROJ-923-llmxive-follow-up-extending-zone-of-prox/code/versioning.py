"""
Versioning module for llmXive pipeline.
Implements Principle V: Data Integrity and Reproducibility.

This module provides functionality to:
1. Generate checksums for all files in the data directory
2. Update the project state YAML with versioning information
3. Ensure data integrity across pipeline runs
"""
import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from utils.logging import get_logger, info, debug, warning, error
from config import get_config
from utils.validation import ensure_directory, validate_file_exists

logger = get_logger(__name__)


def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hex digest of the file hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def get_all_data_files(data_dir: Path) -> List[Path]:
    """
    Recursively get all files in the data directory.
    
    Args:
        data_dir: Path to the data directory
        
    Returns:
        List of Path objects for all files
    """
    if not data_dir.exists():
        warning(f"Data directory does not exist: {data_dir}")
        return []
    
    files = []
    for root, _, filenames in os.walk(data_dir):
        for filename in filenames:
            file_path = Path(root) / filename
            # Skip hidden files and temporary files
            if not filename.startswith('.') and not filename.endswith('.tmp'):
                files.append(file_path)
    
    return sorted(files)


def generate_data_manifest(data_dir: Path) -> Dict[str, Any]:
    """
    Generate a manifest of all data files with their checksums.
    
    Args:
        data_dir: Path to the data directory
        
    Returns:
        Dictionary containing manifest information
    """
    files = get_all_data_files(data_dir)
    
    manifest = {
        'data_directory': str(data_dir),
        'generated_at': datetime.utcnow().isoformat(),
        'total_files': len(files),
        'total_size_bytes': 0,
        'files': []
    }
    
    for file_path in files:
        try:
            checksum = compute_file_checksum(file_path)
            file_size = file_path.stat().st_size
            manifest['total_size_bytes'] += file_size
            
            file_info = {
                'path': str(file_path.relative_to(data_dir)),
                'checksum': checksum,
                'size_bytes': file_size,
                'last_modified': datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat()
            }
            manifest['files'].append(file_info)
            
            debug(f"Checksummed: {file_path} -> {checksum[:16]}...")
            
        except Exception as e:
            error(f"Failed to checksum {file_path}: {e}")
            # Continue with other files
            continue
    
    return manifest


def update_state_file(state_path: Path, manifest: Dict[str, Any]) -> None:
    """
    Update the project state YAML file with versioning information.
    
    Args:
        state_path: Path to the state YAML file
        manifest: Data manifest to store in state
    """
    ensure_directory(state_path.parent)
    
    # Load existing state if it exists
    if state_path.exists():
        try:
            with open(state_path, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            warning(f"Failed to load existing state file: {e}")
            state_data = {}
    else:
        state_data = {}
    
    # Update with new versioning information
    state_data['versioning'] = {
        'last_checksum': datetime.utcnow().isoformat(),
        'data_manifest': manifest
    }
    
    # Ensure project metadata exists
    if 'project' not in state_data:
        state_data['project'] = {
            'id': 'PROJ-923-llmxive-follow-up-extending-zone-of-prox',
            'name': 'llmXive Follow-up: Extending Zone of Proximal Policy Optimization'
        }
    
    # Write updated state
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    info(f"State file updated: {state_path}")


def run_versioning(data_dir: Optional[Path] = None, 
                  state_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main versioning function that checksums data and updates state.
    
    Args:
        data_dir: Path to data directory (uses config if not provided)
        state_dir: Path to state directory (uses config if not provided)
        
    Returns:
        Dictionary with versioning results
    """
    config = get_config()
    
    # Use provided paths or fall back to config
    if data_dir is None:
        data_dir = Path(config.data_dir)
    
    if state_dir is None:
        state_dir = Path(config.state_dir)
    
    # Validate data directory
    if not data_dir.exists():
        error(f"Data directory does not exist: {data_dir}")
        return {
            'success': False,
            'error': f"Data directory does not exist: {data_dir}",
            'data_dir': str(data_dir)
        }
    
    info(f"Starting versioning process for data directory: {data_dir}")
    
    try:
        # Generate manifest
        manifest = generate_data_manifest(data_dir)
        
        # Update state file
        project_id = config.project_id
        state_path = state_dir / 'projects' / f"{project_id}.yaml"
        
        update_state_file(state_path, manifest)
        
        info(f"Versioning complete. Processed {manifest['total_files']} files "
             f"({manifest['total_size_bytes']:,} bytes)")
        
        return {
            'success': True,
            'data_dir': str(data_dir),
            'state_file': str(state_path),
            'total_files': manifest['total_files'],
            'total_size_bytes': manifest['total_size_bytes'],
            'checksum_timestamp': manifest['generated_at']
        }
        
    except Exception as e:
        error(f"Versioning failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'data_dir': str(data_dir)
        }


def main():
    """Entry point for versioning script."""
    info("Running versioning script...")
    
    result = run_versioning()
    
    if result['success']:
        info("Versioning completed successfully")
        print(json.dumps(result, indent=2))
    else:
        error(f"Versioning failed: {result.get('error', 'Unknown error')}")
        print(json.dumps(result, indent=2))
        return 1
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
