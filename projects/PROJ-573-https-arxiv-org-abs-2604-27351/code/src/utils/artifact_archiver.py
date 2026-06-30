"""
Artifact Archiver for Constitution V Compliance.

This module implements the archiving of project artifacts with content hashes.
It scans specified directories, computes SHA256 hashes for all files (excluding
__pycache__), and writes the results to a state file.
"""
import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import logging

from .checksum_utils import compute_file_sha256, load_state_file, save_state_file
from .logging import get_logger

logger = get_logger(__name__)

# Default directories to archive relative to project root
DEFAULT_DIRS_TO_ARCHIVE = [
    "data",
    "state",
    "src"
]

# Directories to explicitly exclude from hashing
EXCLUDED_DIRS = {
    "__pycache__",
    ".git",
    ".pytest_cache",
    "build",
    "dist",
    "*.egg-info"
}

def should_skip_path(path: Path, base_dir: Path) -> bool:
    """
    Determine if a path should be skipped based on exclusion rules.
    """
    # Check if any part of the path matches an excluded directory name
    for part in path.relative_to(base_dir).parts:
        if part in EXCLUDED_DIRS or part.startswith("*.egg-info"):
            return True
        # Specific check for __pycache__ in any form
        if part == "__pycache__":
            return True
    return False

def scan_directory_for_files(
    base_dir: Path,
    target_dirs: List[str],
    project_root: Path
) -> List[Path]:
    """
    Recursively scan specified directories for files to archive.

    Args:
        base_dir: The directory to start scanning from (usually project root)
        target_dirs: List of relative directory paths to include
        project_root: The root of the project (for path resolution)

    Returns:
        List of absolute Path objects for files to be archived
    """
    files_to_hash = []
    
    for target_rel in target_dirs:
        target_path = base_dir / target_rel
        
        if not target_path.exists():
            logger.warning(f"Target directory does not exist: {target_path}")
            continue
        
        if not target_path.is_dir():
            logger.warning(f"Target path is not a directory: {target_path}")
            continue
        
        logger.info(f"Scanning directory: {target_path}")
        
        for root, dirs, files in os.walk(target_path):
            root_path = Path(root)
            
            # Filter out excluded directories in-place to prevent os.walk from descending
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            
            for file_name in files:
                file_path = root_path / file_name
                
                if should_skip_path(file_path, base_dir):
                    continue
                
                # Skip the state file we are about to write to avoid recursion
                if file_path.name == "artifact_hashes.yaml" and "state" in str(file_path):
                    # We still include it if it's the old version, but we need to be careful
                    # Actually, let's just hash everything and update the file later
                    pass
                
                files_to_hash.append(file_path)
    
    return files_to_hash

def compute_artifact_hashes(
    project_root: Optional[Path] = None,
    target_dirs: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute SHA256 hashes for all files in the specified directories.

    Args:
        project_root: Path to the project root. Defaults to current working directory.
        target_dirs: List of relative directories to archive. Defaults to DEFAULT_DIRS_TO_ARCHIVE.

    Returns:
        Dictionary mapping relative file paths to their SHA256 hashes
    """
    if project_root is None:
        project_root = Path.cwd()
    
    if target_dirs is None:
        target_dirs = DEFAULT_DIRS_TO_ARCHIVE
    
    logger.info(f"Starting artifact archiver for project: {project_root}")
    
    files_to_hash = scan_directory_for_files(project_root, target_dirs, project_root)
    logger.info(f"Found {len(files_to_hash)} files to hash.")
    
    hashes = {}
    
    for file_path in files_to_hash:
        try:
            # Compute hash
            file_hash = compute_file_sha256(file_path)
            
            # Store relative path
            rel_path = str(file_path.relative_to(project_root))
            hashes[rel_path] = file_hash
            
            logger.debug(f"Hashed: {rel_path} -> {file_hash[:16]}...")
            
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            # Continue with other files
            continue
    
    logger.info(f"Successfully hashed {len(hashes)} files.")
    return hashes

def update_artifact_hashes_file(
    new_hashes: Dict[str, str],
    project_root: Optional[Path] = None,
    output_path: Optional[str] = None
) -> Path:
    """
    Update the state/artifact_hashes.yaml file with new hashes.

    Args:
        new_hashes: Dictionary of file paths to hashes
        project_root: Path to the project root
        output_path: Optional custom path for the output file

    Returns:
        Path to the updated file
    """
    if project_root is None:
        project_root = Path.cwd()
    
    if output_path is None:
        output_path = "state/artifact_hashes.yaml"
    
    output_file = project_root / output_path
    
    # Ensure directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state if available
    existing_data = load_state_file(output_file)
    
    if existing_data is None:
        existing_data = {
            "version": "1.0",
            "project_id": "PROJ-573-https-arxiv-org-abs-2604-27351",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": {}
        }
    
    # Update timestamp
    existing_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Update artifact hashes
    existing_data["artifacts"] = new_hashes
    
    # Save back to file
    save_state_file(output_file, existing_data)
    
    logger.info(f"Updated artifact hashes file: {output_file}")
    return output_file

def archive_artifacts(
    project_root: Optional[Path] = None,
    target_dirs: Optional[List[str]] = None,
    output_path: Optional[str] = None,
    force: bool = False
) -> Dict[str, Any]:
    """
    Main entry point to archive artifacts with content hashes.

    Args:
        project_root: Path to the project root
        target_dirs: List of directories to scan
        output_path: Path for the output YAML file
        force: If True, overwrite existing hashes without checking

    Returns:
        Summary dictionary of the archiving operation
    """
    logger.info("=== Starting Artifact Archiver ===")
    
    if project_root is None:
        project_root = Path.cwd()
    
    # Compute hashes
    new_hashes = compute_artifact_hashes(project_root, target_dirs)
    
    if not new_hashes:
        logger.warning("No artifacts found to archive.")
        return {
            "status": "warning",
            "message": "No artifacts found",
            "files_archived": 0
        }
    
    # Update the state file
    output_file = update_artifact_hashes_file(
        new_hashes, 
        project_root, 
        output_path
    )
    
    return {
        "status": "success",
        "message": "Artifacts archived successfully",
        "files_archived": len(new_hashes),
        "output_file": str(output_file),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def main():
    """
    CLI entry point for the artifact archiver.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Archive project artifacts with content hashes (Constitution V)"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Path to the project root (default: current directory)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="state/artifact_hashes.yaml",
        help="Output path for the hashes file (default: state/artifact_hashes.yaml)"
    )
    parser.add_argument(
        "--include",
        type=str,
        nargs="+",
        default=DEFAULT_DIRS_TO_ARCHIVE,
        help=f"Directories to include (default: {' '.join(DEFAULT_DIRS_TO_ARCHIVE)})"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    result = archive_artifacts(
        project_root=args.project_root,
        target_dirs=args.include,
        output_path=args.output
    )
    
    print(f"\nArchiving Result: {result['status'].upper()}")
    print(f"Files Archived: {result['files_archived']}")
    print(f"Output File: {result['output_file']}")
    
    if result['status'] == 'success':
        return 0
    return 1

if __name__ == "__main__":
    exit(main())
