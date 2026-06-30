"""
Archiver utility for packaging project artifacts for reproducibility.

Implements FR-007: Package prompts, seeds, scripts, and anonymized ratings 
for public reproducibility.
"""
import os
import json
import shutil
import tarfile
import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from utils.io import load_json, load_csv, safe_write_json, ensure_dir
from utils.logging import get_logger

# Configure module logger
logger = get_logger(__name__)

# Standard project directories to archive
ARCHIVE_DIRECTORIES = [
    "code/generation",
    "code/analysis",
    "code/validation",
    "code/utils",
    "data/prompts",
    "data/raw",
    "data/processed",
    "data/qualitative",
    "specs/contracts",
]

# Files to always include (metadata, configs, rubrics)
ARCHIVE_FILES = [
    "code/config.py",
    "code/main.py",
    "code/validation/rubric.md",
    "README.md",
    "tasks.md",
    "requirements.txt",
]

# Patterns for anonymization
ANONYMIZE_FIELDS = [
    "rater_id",
    "anonymized_id",
    "participant_id",
    "user_id",
    "session_id",
]


class ArchiverError(Exception):
    """Custom exception for archiving errors."""
    pass


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load the archive manifest if it exists.
    
    Args:
        manifest_path: Path to the manifest JSON file
        
    Returns:
        Dictionary containing archive metadata, or empty dict if not found
    """
    if manifest_path.exists():
        try:
            return load_json(manifest_path)
        except Exception as e:
            logger.warning(f"Could not load existing manifest: {e}")
    return {}


def create_archive_manifest(
    project_root: Path,
    output_dir: Path,
    archive_name: str
) -> Dict[str, Any]:
    """
    Create a manifest documenting the archive contents.
    
    Args:
        project_root: Root directory of the project
        output_dir: Directory where archive will be created
        archive_name: Name of the archive file
        
    Returns:
        Manifest dictionary
    """
    manifest = {
        "archive_name": archive_name,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "project_root": str(project_root),
        "directories_included": [],
        "files_included": [],
        "anonymization_applied": True,
        "version": "1.0",
    }
    
    # Record included directories
    for dir_path in ARCHIVE_DIRECTORIES:
        full_path = project_root / dir_path
        if full_path.exists():
            manifest["directories_included"].append(dir_path)
            
    # Record included files
    for file_path in ARCHIVE_FILES:
        full_path = project_root / file_path
        if full_path.exists():
            manifest["files_included"].append(file_path)
            
    return manifest


def anonymize_rating_data(
    input_path: Path,
    output_path: Path
) -> int:
    """
    Anonymize rating data by replacing identifiers with sequential IDs.
    
    Args:
        input_path: Path to the input CSV file
        output_path: Path to write the anonymized CSV
        
    Returns:
        Number of records anonymized
    """
    if not input_path.exists():
        logger.warning(f"Input file not found: {input_path}")
        return 0
        
    try:
        rows = load_csv(input_path)
    except Exception as e:
        raise ArchiverError(f"Failed to load rating data: {e}")
        
    if not rows:
        logger.info("No data to anonymize")
        return 0
        
    # Track mapping from original IDs to anonymized IDs
    id_mapping: Dict[str, str] = {}
    counter = 1
    
    anonymized_rows = []
    for row in rows:
        anonymized_row = row.copy()
        
        # Anonymize each relevant field
        for field in ANONYMIZE_FIELDS:
            if field in anonymized_row and anonymized_row[field]:
                original_id = str(anonymized_row[field])
                if original_id not in id_mapping:
                    id_mapping[original_id] = f"anon_{counter:04d}"
                    counter += 1
                anonymized_row[field] = id_mapping[original_id]
                
        anonymized_rows.append(anonymized_row)
        
    # Write anonymized data
    try:
        safe_write_csv(output_path, anonymized_rows)
        logger.info(f"Anonymized {len(anonymized_rows)} records from {input_path}")
        return len(anonymized_rows)
    except Exception as e:
        raise ArchiverError(f"Failed to write anonymized data: {e}")


def anonymize_json_data(
    input_path: Path,
    output_path: Path
) -> int:
    """
    Anonymize JSON data by replacing identifiers in nested structures.
    
    Args:
        input_path: Path to the input JSON file
        output_path: Path to write the anonymized JSON
        
    Returns:
        Number of records anonymized
    """
    if not input_path.exists():
        logger.warning(f"Input file not found: {input_path}")
        return 0
        
    try:
        data = load_json(input_path)
    except Exception as e:
        raise ArchiverError(f"Failed to load JSON data: {e}")
        
    if not isinstance(data, list):
        data = [data]
        
    id_mapping: Dict[str, str] = {}
    counter = 1
    anonymized_count = 0
    
    def anonymize_value(value: Any) -> Any:
        nonlocal counter, anonymized_count
        
        if isinstance(value, dict):
            result = {}
            for k, v in value.items():
                if k in ANONYMIZE_FIELDS and v:
                    original_id = str(v)
                    if original_id not in id_mapping:
                        id_mapping[original_id] = f"anon_{counter:04d}"
                        counter += 1
                        anonymized_count += 1
                    result[k] = id_mapping[original_id]
                else:
                    result[k] = anonymize_value(v)
            return result
        elif isinstance(value, list):
            return [anonymize_value(item) for item in value]
        else:
            return value
            
    anonymized_data = [anonymize_value(item) for item in data]
    
    try:
        safe_write_json(output_path, anonymized_data)
        logger.info(f"Anonymized {anonymized_count} identifiers in {input_path}")
        return anonymized_count
    except Exception as e:
        raise ArchiverError(f"Failed to write anonymized JSON: {e}")


def prepare_anonymized_ratings(
    project_root: Path,
    temp_dir: Path
) -> List[str]:
    """
    Prepare anonymized versions of all rating files.
    
    Args:
        project_root: Project root directory
        temp_dir: Temporary directory for anonymized files
        
    Returns:
        List of paths to anonymized files
    """
    anonymized_files = []
    
    # Find all rating-related files
    rating_dirs = [
        project_root / "data" / "qualitative",
        project_root / "data" / "processed",
    ]
    
    for rating_dir in rating_dirs:
        if not rating_dir.exists():
            continue
            
        # Process CSV files
        for csv_file in rating_dir.glob("*.csv"):
            if "rating" in csv_file.name.lower() or "anonymized" not in csv_file.name.lower():
                relative_path = csv_file.relative_to(project_root)
                temp_path = temp_dir / "anonymized_ratings" / relative_path
                ensure_dir(temp_path.parent)
                
                try:
                    anonymize_rating_data(csv_file, temp_path)
                    anonymized_files.append(str(temp_path))
                except ArchiverError as e:
                    logger.error(f"Failed to anonymize {csv_file}: {e}")
                    
        # Process JSON files
        for json_file in rating_dir.glob("*.json"):
            if "rating" in json_file.name.lower() or "anonymized" not in json_file.name.lower():
                relative_path = json_file.relative_to(project_root)
                temp_path = temp_dir / "anonymized_ratings" / relative_path
                ensure_dir(temp_path.parent)
                
                try:
                    anonymize_json_data(json_file, temp_path)
                    anonymized_files.append(str(temp_path))
                except ArchiverError as e:
                    logger.error(f"Failed to anonymize {json_file}: {e}")
                    
    return anonymized_files


def create_reproducibility_archive(
    project_root: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    archive_name: Optional[str] = None
) -> str:
    """
    Create a complete reproducibility archive of the project.
    
    This function:
    1. Creates a temporary staging directory
    2. Copies all required files and directories
    3. Anonymizes rating data
    4. Creates a manifest
    5. Packages everything into a tarball
    
    Args:
        project_root: Root directory of the project (default: current directory)
        output_dir: Directory to write the archive (default: data/archives/)
        archive_name: Name of the archive file (default: auto-generated)
        
    Returns:
        Path to the created archive file
    """
    if project_root is None:
        project_root = Path.cwd()
        
    if output_dir is None:
        output_dir = project_root / "data" / "archives"
        
    if archive_name is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        archive_name = f"reproducibility_archive_{timestamp}.tar.gz"
        
    output_path = output_dir / archive_name
    ensure_dir(output_dir)
    
    logger.info(f"Creating reproducibility archive: {output_path}")
    
    # Create temporary staging directory
    temp_dir = project_root / "data" / "archives" / f".temp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    ensure_dir(temp_dir)
    
    try:
        # 1. Copy project files and directories
        logger.info("Copying project files...")
        for dir_path in ARCHIVE_DIRECTORIES:
            src = project_root / dir_path
            if src.exists():
                dest = temp_dir / dir_path
                shutil.copytree(src, dest)
                
        for file_path in ARCHIVE_FILES:
            src = project_root / file_path
            if src.exists():
                dest = temp_dir / file_path
                ensure_dir(dest.parent)
                shutil.copy2(src, dest)
                
        # 2. Anonymize rating data
        logger.info("Anonymizing rating data...")
        prepare_anonymized_ratings(project_root, temp_dir)
        
        # 3. Create manifest
        logger.info("Creating archive manifest...")
        manifest = create_archive_manifest(project_root, output_dir, archive_name)
        manifest_path = temp_dir / "ARCHIVE_MANIFEST.json"
        safe_write_json(manifest_path, manifest)
        
        # 4. Create tarball
        logger.info("Creating tarball...")
        with tarfile.open(output_path, "w:gz") as tar:
            for item in temp_dir.iterdir():
                tar.add(item, arcname=item.name)
                
        # 5. Cleanup temporary directory
        shutil.rmtree(temp_dir)
        
        logger.info(f"Archive created successfully: {output_path}")
        return str(output_path)
        
    except Exception as e:
        # Cleanup on error
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise ArchiverError(f"Failed to create archive: {e}")


def run_archiver(
    project_root: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    archive_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the archiver with optional parameters.
    
    Args:
        project_root: Root directory of the project
        output_dir: Directory to write the archive
        archive_name: Name of the archive file
        
    Returns:
        Dictionary with archive path and manifest
    """
    archive_path = create_reproducibility_archive(project_root, output_dir, archive_name)
    
    # Load the manifest for return
    temp_dir = Path(archive_path).parent / f".temp_{Path(archive_path).stem.replace('reproducibility_archive_', '')}"
    # We need to re-extract to get manifest, or we can just return the path
    # For simplicity, return the path and a summary
    
    return {
        "archive_path": archive_path,
        "status": "success",
        "message": f"Archive created at {archive_path}",
    }


def main():
    """Main entry point for the archiver script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create a reproducibility archive of the phenomenological AI project."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for the archive (default: data/archives/)"
    )
    parser.add_argument(
        "--archive-name",
        type=str,
        default=None,
        help="Name of the archive file (default: auto-generated)"
    )
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root) if args.project_root else None
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    try:
        result = run_archiver(project_root, output_dir, args.archive_name)
        print(json.dumps(result, indent=2))
    except ArchiverError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
        
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
