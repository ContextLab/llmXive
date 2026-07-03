import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

from config import get_config
from utils.logging import get_logger


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger = get_logger("hash_artifacts")
        logger.error(f"Failed to hash {file_path}: {e}")
        raise


def scan_directory(directory: Path, extensions: List[str] = None) -> List[Path]:
    """Scan directory for files, optionally filtering by extensions."""
    files = []
    if not directory.exists():
        return files
    
    for item in directory.rglob("*"):
        if item.is_file():
            if extensions is None:
                files.append(item)
            else:
                suffix = item.suffix.lower()
                if suffix in extensions:
                    files.append(item)
    return files


def hash_artifacts(directories: List[Path], output_path: Path, extensions: List[str] = None) -> Dict[str, Any]:
    """Hash all artifacts in given directories and save to output file."""
    logger = get_logger("hash_artifacts")
    logger.info(f"Starting artifact hashing for directories: {directories}")
    
    results = {
        "status": "success",
        "files": {},
        "summary": {
            "total_files": 0,
            "total_size_bytes": 0,
            "directories_processed": []
        }
    }
    
    for directory in directories:
        if not directory.exists():
            logger.warning(f"Directory does not exist, skipping: {directory}")
            results["summary"]["directories_processed"].append({
                "path": str(directory),
                "status": "skipped",
                "reason": "not_exists"
            })
            continue
        
        logger.info(f"Processing directory: {directory}")
        files = scan_directory(directory, extensions)
        
        dir_status = {
            "path": str(directory),
            "status": "processed",
            "files_count": len(files),
            "total_size_bytes": 0
        }
        
        for file_path in files:
            try:
                file_size = file_path.stat().st_size
                file_hash = calculate_sha256(file_path)
                relative_path = str(file_path.relative_to(Path.cwd()))
                
                results["files"][relative_path] = {
                    "hash": file_hash,
                    "size_bytes": file_size
                }
                
                dir_status["total_size_bytes"] += file_size
                results["summary"]["total_size_bytes"] += file_size
                results["summary"]["total_files"] += 1
            except Exception as e:
                logger.error(f"Failed to hash {file_path}: {e}")
                results["files"][str(file_path)] = {
                    "error": str(e),
                    "hash": None,
                    "size_bytes": None
                }
        
        results["summary"]["directories_processed"].append(dir_status)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Hash report saved to {output_path}")
    logger.info(f"Total files processed: {results['summary']['total_files']}")
    
    return results


def main():
    """Main entry point for artifact hashing."""
    logger = get_logger("hash_artifacts")
    config = get_config()
    
    # Define directories to hash based on task requirements
    # T019: data/processed/features.csv
    # T024a: data/processed/ (VIF diagnostics, though output not explicitly named, likely in processed)
    # T024b: data/processed/labels_k2.csv, data/processed/labels_k3.csv
    # T023a: data/processed/ (bootstrap stability results, likely in processed)
    # We hash the entire data/processed directory to capture all these artifacts
    
    processed_dir = config.PROCESSED_DATA_DIR
    raw_dir = config.RAW_DATA_DIR
    state_dir = config.STATE_DIR
    
    directories_to_hash = [processed_dir]
    
    # Also hash raw data if it exists (for completeness after T015)
    if raw_dir.exists():
        directories_to_hash.insert(0, raw_dir)
    
    # Output path for hash report
    output_path = state_dir / "hash_report_features_labels.json"
    
    # File extensions to include
    extensions = [".csv", ".json", ".yaml", ".yml", ".txt", ".log", ".png", ".pdf"]
    
    try:
        results = hash_artifacts(directories_to_hash, output_path, extensions)
        
        if results["summary"]["total_files"] == 0:
            logger.warning("No files were hashed. Ensure data has been generated by T019, T023a, T024a, T024b.")
            return 1
        
        logger.info(f"Successfully hashed {results['summary']['total_files']} files")
        return 0
        
    except Exception as e:
        logger.error(f"Artifact hashing failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())