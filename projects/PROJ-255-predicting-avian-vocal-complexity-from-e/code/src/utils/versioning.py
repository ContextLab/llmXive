"""
Versioning utilities for the Avian Vocal Complexity project.
Generates SHA-256 hashes for all critical data artifacts to ensure reproducibility (FR-005, SC-006).
"""
import os
import hashlib
import json
import logging
import glob
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.utils.config import (
    get_project_root,
    get_data_dir,
    get_raw_data_dir,
    get_interim_data_dir,
    get_processed_data_dir,
    get_figures_dir,
)
from src.utils.logging import setup_logger

logger = setup_logger("versioning")

# Define the specific files and patterns to hash as per task requirements
# We use a list of tuples: (relative_path_pattern, description)
TARGET_PATHS = [
    # Directory contents (hashing the directory itself isn't standard, so we hash files within)
    # We will iterate files in these dirs
    ("data/raw", "Raw data directory"),
    ("data/interim", "Interim data directory"),
    ("data/processed", "Processed data directory"),
    ("data/figures", "Figures directory"),
    # Specific files in processed
    ("data/processed/sensitivity_*.csv", "Sensitivity analysis CSVs"),
    ("data/processed/sensitivity_summary.csv", "Sensitivity summary CSV"),
    ("data/processed/false_positive_analysis.json", "False positive analysis JSON"),
    ("data/processed/report.md", "Final report markdown"),
]

def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    Reads in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash file {file_path}: {e}")
        raise

def get_files_to_hash(base_dir: Path, pattern: str) -> List[Path]:
    """
    Returns a sorted list of file paths matching the pattern in base_dir.
    Handles both directory patterns (hash all files) and glob patterns.
    """
    full_pattern = base_dir / pattern
    files = []
    
    # Check if pattern contains wildcards
    if "*" in pattern:
        matches = glob.glob(str(full_pattern))
        files = [Path(m) for m in matches if os.path.isfile(m)]
    else:
        # If it's a directory without wildcard, hash all files inside
        if full_pattern.is_dir():
            for root, _, filenames in os.walk(full_pattern):
                for filename in filenames:
                    files.append(Path(root) / filename)
        # If it's a specific file
        elif full_pattern.is_file():
            files.append(full_pattern)
    
    return sorted(files)

def generate_hashes() -> Dict[str, str]:
    """
    Iterates through all target paths, calculates hashes for each file,
    and returns a dictionary mapping relative paths to their SHA-256 hashes.
    """
    project_root = get_project_root()
    data_dir = get_data_dir()
    
    hashes = {}
    file_count = 0
    
    for pattern, description in TARGET_PATHS:
        logger.info(f"Processing {description}: {pattern}")
        
        # Resolve pattern relative to project root for glob, but we need to check existence
        # Some patterns are directories, some are specific files
        
        # Handle directory patterns vs file patterns
        if "*" in pattern:
            # It's a glob pattern for specific files
            base_path = project_root
            files = get_files_to_hash(base_path, pattern)
        else:
            # It's a directory or specific file path relative to data/
            # We treat it as relative to project_root/data/
            # But the pattern in TARGET_PATHS is relative to project root (e.g., "data/raw")
            
            # Check if it's a directory
            dir_path = project_root / pattern
            if dir_path.is_dir():
                files = get_files_to_hash(project_root, pattern)
            else:
                # It might be a specific file
                if dir_path.is_file():
                    files = [dir_path]
                else:
                    # Check relative to data dir just in case
                    data_rel_path = project_root / "data" / pattern
                    if data_rel_path.is_file():
                        files = [data_rel_path]
                    else:
                        logger.warning(f"Path not found: {dir_path}")
                        files = []
        
        for file_path in files:
            try:
                # Calculate relative path from project root for the key
                rel_path = str(file_path.relative_to(project_root))
                file_hash = calculate_file_hash(file_path)
                hashes[rel_path] = file_hash
                file_count += 1
                logger.debug(f"Hashed: {rel_path} -> {file_hash[:16]}...")
            except ValueError:
                # File is outside project root (shouldn't happen with our logic)
                logger.warning(f"Skipping file outside project root: {file_path}")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
    
    logger.info(f"Successfully generated {file_count} file hashes.")
    return hashes

def save_hashes(hashes: Dict[str, str], output_path: Optional[Path] = None) -> Path:
    """
    Saves the generated hashes to a JSON file.
    Default output: data/processed/version_hashes.json
    """
    if output_path is None:
        processed_dir = get_processed_data_dir()
        output_path = processed_dir / "version_hashes.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "project": "PROJ-255-predicting-avian-vocal-complexity-from-e",
        "task": "T039",
        "description": "SHA-256 hashes for reproducibility verification (FR-005, SC-006)",
        "hashes": hashes
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Hashes saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for the versioning script.
    Generates hashes for all specified data artifacts and saves them.
    """
    logger.info("Starting versioning process for T039...")
    
    try:
        hashes = generate_hashes()
        
        if not hashes:
            logger.warning("No files were hashed. Check if data directories exist.")
            # Still create the file even if empty, to signal the task ran
            save_hashes(hashes)
            return 1
        
        output_path = save_hashes(hashes)
        logger.info(f"Versioning complete. Output: {output_path}")
        return 0
        
    except Exception as e:
        logger.critical(f"Versioning process failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
