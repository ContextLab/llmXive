import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
import datetime

from logger import get_logger, get_project_root

logger = get_logger(__name__)

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a single file.
    Reads file in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_checksums(
    root_dir: Path,
    extensions: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute checksums for all files in a directory tree.
    
    Args:
        root_dir: Root directory to scan
        extensions: Optional list of file extensions to include (e.g., ['.py', '.txt'])
        exclude_dirs: Optional list of directory names to exclude (e.g., ['__pycache__', '.git'])
    
    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums
    """
    checksums = {}
    default_exclude = {'__pycache__', '.git', '.pytest_cache', 'node_modules', '.venv', 'venv'}
    exclude_dirs = set(exclude_dirs or []) | default_exclude

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Modify dirnames in-place to skip excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        for filename in filenames:
            if extensions and not any(filename.endswith(ext) for ext in extensions):
                continue

            file_path = Path(dirpath) / filename
            rel_path = file_path.relative_to(root_dir)
            
            try:
                checksums[str(rel_path)] = compute_file_checksum(file_path)
            except (PermissionError, OSError) as e:
                logger.warning(f"Could not compute checksum for {rel_path}: {e}")

    return checksums

def compute_and_record_checksums(
    project_root: Optional[Path] = None,
    state_file_name: str = "PROJ-304-statistical-analysis-of-publicly-availab.yaml"
) -> Dict[str, Any]:
    """
    Compute checksums for key project artifacts and record them in the state file.
    
    This function:
    1. Scans key directories (data/processed, code, tests) for checksums
    2. Updates or creates the state file with the new checksums
    3. Logs the operation and any errors encountered
    
    Args:
        project_root: Optional override for project root. Defaults to get_project_root().
        state_file_name: Name of the state file to update in state/projects/
    
    Returns:
        Dictionary containing the updated state record
    """
    if project_root is None:
        project_root = get_project_root()
    
    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    state_file_path = state_dir / state_file_name
    
    # Load existing state if it exists
    existing_state = {}
    if state_file_path.exists():
        try:
            with open(state_file_path, "r", encoding="utf-8") as f:
                existing_state = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse existing state file {state_file_path}: {e}")
            existing_state = {}
    
    # Define paths to checksum
    paths_to_scan = {
        "data/processed": ["data/processed"],
        "code": ["code"],
        "tests": ["tests"],
    }
    
    new_checksums = {}
    
    for label, path_list in paths_to_scan.items():
        for rel_path_str in path_list:
            full_path = project_root / rel_path_str
            if full_path.exists():
                logger.info(f"Computing checksums for {label} at {full_path}")
                try:
                    dir_checksums = compute_directory_checksums(full_path)
                    if dir_checksums:
                        new_checksums[label] = dir_checksums
                    else:
                        logger.warning(f"No files found to checksum in {full_path}")
                except Exception as e:
                    logger.error(f"Failed to compute checksums for {full_path}: {e}")
            else:
                logger.warning(f"Path does not exist, skipping: {full_path}")
    
    # Prepare the record to save
    record = {
        "last_updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "project_id": "PROJ-304-statistical-analysis-of-publicly-availab",
        "checksums": new_checksums
    }
    
    # Merge into existing state (preserving other project info if any)
    # If this is the first run, just set the project key
    if "projects" not in existing_state:
        existing_state["projects"] = {}
    
    # Use the project ID derived from the filename (without .yaml) as the key
    project_key = state_file_name.replace(".yaml", "")
    existing_state["projects"][project_key] = record
    
    # Write back to file
    try:
        with open(state_file_path, "w", encoding="utf-8") as f:
            yaml.dump(existing_state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Successfully updated state file: {state_file_path}")
    except IOError as e:
        logger.error(f"Failed to write state file {state_file_path}: {e}")
        raise
    
    return record

def main():
    """CLI entry point for checksum computation."""
    logger.info("Starting checksum computation and recording...")
    try:
        result = compute_and_record_checksums()
        logger.info(f"Completed. Updated {len(result.get('checksums', {}))} sections.")
        # Print summary to stdout for quick verification
        for section, files in result.get('checksums', {}).items():
            logger.info(f"  {section}: {len(files)} files checksummed")
    except Exception as e:
        logger.critical(f"Checksum process failed: {e}")
        raise

if __name__ == "__main__":
    main()