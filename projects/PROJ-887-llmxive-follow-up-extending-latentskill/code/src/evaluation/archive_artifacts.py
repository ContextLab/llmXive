import os
import sys
import shutil
import json
import logging
import tarfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Ensure we can import from the project root if running as a script
if 'code' in str(Path(__file__).parent):
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
elif 'src' in str(Path(__file__).parent):
    sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import get_project_root, get_data_path, get_artifacts_path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_archive_structure(archive_root: Path) -> None:
    """
    Creates the directory structure for the archive.
    Structure:
    archive/
      <timestamp>/
        data/
        artifacts/
        code/
        reports/
        logs/
        metadata/
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_version = archive_root / timestamp
    
    dirs = [
        archive_version / "data",
        archive_version / "artifacts",
        archive_version / "code",
        archive_version / "reports",
        archive_version / "logs",
        archive_version / "metadata"
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {d}")
    
    return archive_version

def collect_files(archive_version: Path) -> Dict[str, List[str]]:
    """
    Collects lists of files to be archived based on standard project directories.
    Returns a manifest mapping category to file paths (relative to archive_version).
    """
    project_root = get_project_root()
    manifest = {
        "data": [],
        "artifacts": [],
        "reports": [],
        "logs": [],
        "metadata": []
    }

    # Define source directories
    source_dirs = {
        "data": project_root / "data",
        "artifacts": project_root / "artifacts",
        "reports": project_root / "reports",
        "logs": project_root / "logs", # Assuming logs might be here, or we scan for .log files
        "metadata": project_root / "specs"
    }

    # File extensions to include
    include_extensions = {'.json', '.yaml', '.yml', '.npz', '.pt', '.safetensors', '.gguf', '.csv', '.md', '.txt', '.log', '.png', '.jpg', '.py'}
    exclude_patterns = {'__pycache__', '.git', '.DS_Store', '*.tmp', '*.bak'}

    for category, source_path in source_dirs.items():
        if not source_path.exists():
            logger.warning(f"Source path does not exist, skipping: {source_path}")
            continue

        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                # Check exclusions
                if any(part.startswith('.') for part in file_path.parts) or any(p in str(file_path) for p in exclude_patterns):
                    continue
                
                # Check extension
                if file_path.suffix.lower() not in include_extensions and file_path.suffix != '':
                    # Allow files without extensions if they are known configs
                    if file_path.name not in ['Dockerfile', 'Makefile', 'requirements.txt']:
                        continue

                # Calculate relative path for the archive
                rel_path = file_path.relative_to(project_root)
                manifest[category].append(str(rel_path))
                logger.debug(f"Added to {category}: {rel_path}")

    return manifest

def copy_to_archive(archive_version: Path, manifest: Dict[str, List[str]]) -> int:
    """
    Copies files from the project root to the archive version based on the manifest.
    Returns the count of copied files.
    """
    project_root = get_project_root()
    copied_count = 0

    for category, file_paths in manifest.items():
        dest_dir = archive_version / category
        dest_dir.mkdir(parents=True, exist_ok=True)

        for rel_path_str in file_paths:
            src_file = project_root / rel_path_str
            if not src_file.exists():
                logger.warning(f"Source file missing during copy, skipping: {src_file}")
                continue

            dest_file = dest_dir / rel_path_str
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                shutil.copy2(src_file, dest_file)
                copied_count += 1
                logger.debug(f"Copied: {src_file} -> {dest_file}")
            except Exception as e:
                logger.error(f"Failed to copy {src_file}: {e}")

    return copied_count

def generate_archive_manifest(archive_version: Path, manifest: Dict[str, List[str]], copied_count: int) -> Path:
    """
    Generates a manifest.json file describing the archive contents.
    """
    metadata_dir = archive_version / "metadata"
    manifest_path = metadata_dir / "archive_manifest.json"
    
    manifest_data = {
        "created_at": datetime.now().isoformat(),
        "project_root": str(get_project_root()),
        "total_files_copied": copied_count,
        "contents": manifest
    }

    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2, default=str)
    
    logger.info(f"Generated archive manifest: {manifest_path}")
    return manifest_path

def main():
    """
    Main entry point for the archiving task.
    Orchestrates the creation of the archive structure, collection of files,
    copying, and manifest generation.
    """
    logger.info("Starting artifact archiving process for T086")
    
    project_root = get_project_root()
    archive_root = project_root / "archive"
    
    # Ensure archive root exists
    archive_root.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Create structure
        archive_version = create_archive_structure(archive_root)
        
        # 2. Collect file lists
        logger.info("Collecting file lists...")
        manifest = collect_files(archive_version)
        
        # 3. Copy files
        logger.info("Copying files to archive...")
        copied_count = copy_to_archive(archive_version, manifest)
        
        if copied_count == 0:
            logger.warning("No files were copied. Archive may be empty.")
        
        # 4. Generate manifest
        logger.info("Generating manifest...")
        generate_archive_manifest(archive_version, manifest, copied_count)
        
        # 5. Create a compressed tarball for long-term storage
        tar_path = archive_root / f"archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        logger.info(f"Creating compressed archive: {tar_path}")
        
        with tarfile.open(tar_path, "w:gz") as tar:
            # Add the versioned directory
            tar.add(archive_version, arcname=archive_version.name)
        
        logger.info(f"Archive process completed successfully.")
        logger.info(f"Archive contents: {archive_version}")
        logger.info(f"Compressed archive: {tar_path}")
        
        return 0

    except Exception as e:
        logger.error(f"Archive process failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
