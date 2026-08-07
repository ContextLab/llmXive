"""
Reproducibility Package Generator (Task T031)

Generates the final reproducibility package bundle for OSF publication.
Includes analysis results, anonymized logs, and documentation.
Explicitly excludes consent data to satisfy Constitution Principle VI.
"""
import os
import sys
import tarfile
import json
import shutil
import tempfile
import logging
from pathlib import Path
from typing import List, Set

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Define paths
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
README_PATH = PROJECT_ROOT / "README.md"
OUTPUT_DIR = DATA_DIR
OUTPUT_FILENAME = "reproducibility_package_v1.0.tar.gz"

# Required input files that MUST exist
REQUIRED_FILES = [
    DATA_DIR / "analysis_results" / "results.csv",
    DATA_DIR / "interaction_logs" / "anonymized_logs.csv",
    README_PATH,
]

# Directories to include
INCLUDE_DIRS = [
    DATA_DIR / "analysis_results",
    DATA_DIR / "interaction_logs",
    CODE_DIR / "analysis",
    CODE_DIR / "data_prep",
    CODE_DIR / "utils",
]

# Directories to EXCLUDE (Constitution Principle VI)
EXCLUDE_DIRS = [
    DATA_DIR / "consent",
    DATA_DIR / "interaction_logs" / "raw_logs.csv", # Just in case, though anonymized is preferred
    DATA_DIR / "defects4j", # Too large, only need the script to regenerate if needed, or specific small subset
]

# Specific files to exclude even if in included dirs
EXCLUDE_FILES = {
    "raw_logs.csv",
    "consent_forms",
    ".env",
    ".git",
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".DS_Store",
    "baseline_results.json", # Internal ground truth, not for public release usually, but task says include results.csv
}

logger = logging.getLogger(__name__)

def should_exclude(path: Path, base_dir: Path) -> bool:
    """
    Determine if a path should be excluded from the package.
    
    Args:
        path: The full path of the file/directory being considered.
        base_dir: The root directory of the inclusion scope.
        
    Returns:
        True if the path should be excluded, False otherwise.
    """
    rel_path = path.relative_to(base_dir)
    parts = rel_path.parts
    
    # Check if any part is in EXCLUDE_DIRS (relative to base)
    for exclude_dir in EXCLUDE_DIRS:
        try:
            exclude_rel = exclude_dir.relative_to(base_dir)
            if parts[:len(exclude_rel)] == exclude_rel.parts:
                return True
        except ValueError:
            # exclude_dir is not under base_dir, ignore
            continue
    
    # Check if filename matches EXCLUDE_FILES patterns
    if path.name in EXCLUDE_FILES:
        return True
    
    # Check for hidden files/dirs (except .gitkeep if we had one, but we don't)
    if path.name.startswith('.') and path.name != '.gitkeep':
        return True
        
    return False

def create_reproducibility_package(output_path: Path, files: List[Path], dirs: List[Path]) -> str:
    """
    Creates the tar.gz reproducibility package.
    
    Args:
        output_path: Full path where the .tar.gz will be saved.
        files: List of specific files to include.
        dirs: List of directories to include (recursively).
        
    Returns:
        Path to the created archive.
        
    Raises:
        FileNotFoundError: If any required file is missing.
        ValueError: If output path is invalid.
    """
    # Verify required files exist
    for f in REQUIRED_FILES:
        if not f.exists():
            raise FileNotFoundError(f"Required file missing: {f}")
    
    # Create temporary directory to stage files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        
        # 1. Copy specific files
        for file_path in files:
            if file_path.exists():
                dest = temp_root / file_path.name
                shutil.copy2(file_path, dest)
                logger.info(f"Copied file: {file_path} -> {dest}")
            else:
                logger.warning(f"File not found (skipping): {file_path}")
        
        # 2. Copy directories recursively, filtering exclusions
        for dir_path in dirs:
            if not dir_path.exists():
                logger.warning(f"Directory not found (skipping): {dir_path}")
                continue
                
            # Get relative name for the archive
            dest_dir = temp_root / dir_path.name
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            for root, dirs, files in os.walk(dir_path):
                current_root = Path(root)
                
                # Filter out excluded directories from os.walk traversal
                # We modify dirs in-place to prevent descending into them
                dirs[:] = [d for d in dirs if not should_exclude(current_root / d, dir_path)]
                
                # Create corresponding directory in temp
                dest_sub = dest_dir / current_root.relative_to(dir_path)
                dest_sub.mkdir(parents=True, exist_ok=True)
                
                # Copy files
                for file in files:
                    src_file = current_root / file
                    if should_exclude(src_file, dir_path):
                        continue
                    dst_file = dest_sub / file
                    shutil.copy2(src_file, dst_file)
                    logger.debug(f"Copied: {src_file} -> {dst_file}")
        
        # 3. Create the tar.gz archive
        logger.info(f"Creating archive: {output_path}")
        with tarfile.open(output_path, "w:gz") as tar:
            # Add all files from temp_root
            for item in temp_root.iterdir():
                tar.add(item, arcname=item.name)
                
        logger.info(f"Successfully created reproducibility package: {output_path}")
        return str(output_path)

def main():
    """Main entry point for the reproducibility package generation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    output_path = OUTPUT_DIR / OUTPUT_FILENAME
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Remove existing file if present
        if output_path.exists():
            logger.warning(f"Removing existing archive: {output_path}")
            output_path.unlink()
        
        # Collect files to include
        files_to_include = [f for f in REQUIRED_FILES if f.exists()]
        
        # Add README specifically if not in REQUIRED_FILES (it is, but double check)
        if README_PATH.exists() and README_PATH not in files_to_include:
            files_to_include.append(README_PATH)
        
        package_path = create_reproducibility_package(
            output_path=output_path,
            files=files_to_include,
            dirs=INCLUDE_DIRS
        )
        
        # Verify size
        size_mb = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"Package size: {size_mb:.2f} MB")
        
        print(f"SUCCESS: Reproducibility package created at {package_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Missing required file: {e}")
        print(f"ERROR: Missing required file. {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.error(f"Failed to create package: {e}", exc_info=True)
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
