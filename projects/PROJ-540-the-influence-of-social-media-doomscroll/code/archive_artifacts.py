import os
import zipfile
import logging
import sys
from pathlib import Path
from datetime import datetime

# Ensure logging is configured (relying on project-wide setup if available, 
# otherwise basic config for standalone execution)
if not logging.root.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
logger = logging.getLogger(__name__)

def create_archive(
    source_dirs: list[str],
    output_filename: str,
    base_dir: Path | None = None
) -> str:
    """
    Create a zip archive of the specified directories relative to base_dir.
    
    Args:
        source_dirs: List of directory names to archive (e.g., ['data/processed', 'outputs']).
        output_filename: Name of the resulting zip file (e.g., 'archive_20231027.zip').
        base_dir: Root directory of the project. Defaults to current working directory.
    
    Returns:
        The absolute path to the created archive.
    
    Raises:
        FileNotFoundError: If any source directory does not exist.
        ValueError: If source_dirs is empty.
    """
    if not source_dirs:
        raise ValueError("source_dirs cannot be empty.")
    
    base = Path(base_dir) if base_dir else Path.cwd()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not output_filename.endswith('.zip'):
        output_filename = f"{output_filename}.zip"
    
    archive_name = output_filename.replace('.zip', f"_{timestamp}.zip")
    archive_path = base / archive_name
    
    logger.info(f"Starting archive creation: {archive_path}")
    
    # Verify all source directories exist before starting
    for dir_name in source_dirs:
        target_path = base / dir_name
        if not target_path.exists():
            raise FileNotFoundError(f"Source directory not found: {target_path}")
        if not target_path.is_dir():
            raise FileNotFoundError(f"Source path is not a directory: {target_path}")
    
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for dir_name in source_dirs:
            target_path = base / dir_name
            logger.info(f"Archiving: {target_path}")
            
            # Walk through the directory and add files
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    file_path = Path(root) / file
                    # Calculate relative path for the archive structure
                    arcname = file_path.relative_to(base)
                    zipf.write(file_path, arcname)
                    logger.debug(f"Added to archive: {arcname}")
    
    logger.info(f"Archive successfully created: {archive_path}")
    return str(archive_path)

def main() -> int:
    """
    Main entry point for the archive artifacts task (T044).
    Archives data/processed, outputs, and code.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        # Define the directories to archive based on T044 description
        # "Create a zip archive of `data/processed/`, `outputs/`, and `code/`"
        # We archive the parent directories to preserve structure, 
        # or specifically the folders if they are distinct.
        # Based on project structure: data/processed, outputs, code
        dirs_to_archive = [
            "data/processed",
            "outputs",
            "code"
        ]
        
        # Verify existence of these specific paths
        # If data/processed doesn't exist but data does, we might need to adjust,
        # but per spec T013, data/processed/analysis_data.csv should exist.
        base_dir = Path.cwd()
        
        # Check for existence
        missing = []
        for d in dirs_to_archive:
            if not (base_dir / d).exists():
                missing.append(d)
        
        if missing:
            # If specific subdirs missing, try to archive the parent if it exists
            # This is a fallback to ensure the script doesn't fail if a sub-step 
            # hasn't created a specific folder yet, though T044 implies they exist.
            # For strict adherence, we raise if the exact paths are missing.
            raise FileNotFoundError(f"Required directories missing: {missing}")

        output_name = "project_archive"
        archive_path = create_archive(dirs_to_archive, output_name, base_dir)
        
        logger.info("T044 Task Completed Successfully.")
        return 0
    
    except Exception as e:
        logger.error(f"T044 Task Failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
