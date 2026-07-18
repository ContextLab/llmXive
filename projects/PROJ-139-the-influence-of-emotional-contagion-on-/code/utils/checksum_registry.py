import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import os

from config.settings import get_config, DatasetPaths

logger = logging.getLogger(__name__)


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
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


def find_artifacts(base_dirs: List[Path], extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Recursively find all artifact files in given directories.
    
    Args:
        base_dirs: List of directories to search
        extensions: Optional list of file extensions to include (e.g., ['.json', '.csv'])
                   If None, includes all files
                   
    Returns:
        List of Path objects for all found artifact files
    """
    artifacts = []
    for base_dir in base_dirs:
        if not base_dir.exists():
            logger.warning(f"Directory does not exist, skipping: {base_dir}")
            continue
        
        for file_path in base_dir.rglob('*'):
            if file_path.is_file():
                if extensions is None or file_path.suffix in extensions:
                    artifacts.append(file_path)
                    
    return artifacts


def record_checksums(
    artifact_paths: List[Path],
    output_path: Path,
    project_state_path: Optional[Path] = None
) -> Dict[str, str]:
    """
    Compute and record checksums for a list of artifacts.
    
    Args:
        artifact_paths: List of paths to artifacts to hash
        output_path: Path where the checksum registry (JSON) will be saved
        project_state_path: Optional path to the project state YAML file to update
                           (e.g., state/projects/PROJ-139-*.yaml)
                           
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes
    """
    checksums = {}
    
    for file_path in artifact_paths:
        try:
            file_hash = compute_file_hash(file_path)
            # Store relative path for portability
            relative_path = str(file_path)
            checksums[relative_path] = file_hash
            logger.info(f"Checksum recorded: {relative_path} -> {file_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to compute hash for {file_path}: {e}")
    
    # Write the checksum registry to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksum registry saved to {output_path}")
    
    # Update the project state YAML if requested
    if project_state_path:
        update_project_state(project_state_path, checksums)
        
    return checksums


def update_project_state(state_path: Path, checksums: Dict[str, str]) -> None:
    """
    Update the project state YAML file with the new checksums.
    
    Args:
        state_path: Path to the project state YAML file
        checksums: Dictionary of file paths to hashes
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create new
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            state_data = yaml.safe_load(f) or {}
    else:
        state_data = {}
        
    # Ensure the checksums key exists
    if 'artifact_checksums' not in state_data:
        state_data['artifact_checksums'] = {}
        
    # Update with new checksums
    state_data['artifact_checksums'].update(checksums)
    
    # Add metadata
    state_data['last_updated'] = "auto-generated-by-T027"
    
    # Write back
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        
    logger.info(f"Project state updated at {state_path}")


def main():
    """
    Main entry point for T027: Record all artifact checksums.
    
    This script:
    1. Loads configuration to find project directories.
    2. Scans data/, code/, state/, and docs/ for artifacts.
    3. Computes SHA-256 hashes for all found files.
    4. Saves a JSON registry of checksums.
    5. Updates the project state YAML file with the checksum map.
    """
    logger.info("Starting T027: Recording artifact checksums...")
    
    config = get_config()
    paths = config.paths
    
    # Define directories to scan
    scan_dirs = [
        paths.raw_data,
        paths.processed_data,
        paths.code_dir,
        paths.state_dir,
        paths.docs_dir
    ]
    
    # Filter to existing directories
    existing_dirs = [d for d in scan_dirs if d.exists()]
    
    if not existing_dirs:
        logger.error("No valid directories found to scan for artifacts.")
        return
        
    logger.info(f"Scanning directories: {[str(d) for d in existing_dirs]}")
    
    # Find all artifacts (excluding common non-artifact files if needed)
    # We include all files, but could filter extensions if desired
    artifacts = find_artifacts(existing_dirs)
    
    logger.info(f"Found {len(artifacts)} artifact files.")
    
    if not artifacts:
        logger.warning("No artifacts found. Check directory paths and permissions.")
        return
        
    # Define output paths
    checksum_registry_path = paths.state_dir / "checksum_registry.json"
    project_state_path = paths.state_dir / "projects" / "PROJ-139-the-influence-of-emotional-contagion-on-.yaml"
    
    # Record checksums
    checksums = record_checksums(
        artifact_paths=artifacts,
        output_path=checksum_registry_path,
        project_state_path=project_state_path
    )
    
    logger.info(f"T027 completed successfully. Recorded {len(checksums)} checksums.")
    logger.info(f"Registry saved to: {checksum_registry_path}")
    logger.info(f"Project state updated at: {project_state_path}")


if __name__ == "__main__":
    # Setup basic logging if not already configured
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
