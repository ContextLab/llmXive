import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import logger from existing infrastructure
from utils.logger import get_logger

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
INTERMEDIATES_DIR = DATA_DIR / "intermediates"
RAW_DIR = DATA_DIR / "raw"
BINARIES_DIR = PROJECT_ROOT / "binaries"  # Assuming binaries are stored here or in a specific build dir

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logging.warning(f"File not found for hashing: {file_path}")
        return ""
    except Exception as e:
        logging.error(f"Error hashing file {file_path}: {e}")
        return ""

def scan_directory(directory: Path, extensions: List[str], recursive: bool = True) -> List[Path]:
    """Scan a directory for files with specific extensions."""
    files = []
    if not directory.exists():
        logging.warning(f"Directory does not exist: {directory}")
        return files
    
    if recursive:
        for ext in extensions:
            files.extend(directory.rglob(f"*{ext}"))
    else:
        for ext in extensions:
            files.extend(directory.glob(f"*{ext}"))
    
    return files

def generate_manifest(output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate a manifest.json with SHA-256 hashes for all relevant artifacts.
    
    Scans:
    - data/raw/
    - data/intermediates/
    - data/results/
    - binaries/ (if it exists)
    
    Returns a dictionary that can be serialized to JSON.
    """
    logger = get_logger(__name__)
    logger.info("Starting manifest generation...")
    
    manifest = {
        "generated_at": datetime.utcnow().isoformat(),
        "project": "PROJ-057-investigating-the-impact-of-compiler-opt",
        "files": []
    }
    
    # Define search paths and extensions
    search_paths = [
        (RAW_DIR, [".json", ".csv", ".bin", ".npy"]),
        (INTERMEDIATES_DIR, [".jsonl", ".json", ".csv"]),
        (RESULTS_DIR, [".csv", ".png", ".json"]),
        (DATA_DIR, [".json"]), # Catch-all for manifest itself or config
    ]
    
    # Check for binaries directory if it exists in project root
    if (PROJECT_ROOT / "binaries").exists():
        search_paths.append((PROJECT_ROOT / "binaries", [".out", ".bin", ""])) # Empty string for executables without extension
    
    # Also check for compiled kernel binaries in a potential build folder
    build_dir = PROJECT_ROOT / "code" / "kernels"
    if build_dir.exists():
        search_paths.append((build_dir, [".out", ".bin"]))

    total_files = 0
    for base_path, extensions in search_paths:
        if not base_path.exists():
            continue
        
        logger.info(f"Scanning {base_path} for {extensions}...")
        files = scan_directory(base_path, extensions, recursive=True)
        
        for file_path in files:
            # Skip the manifest file itself if it's in the scan path
            if file_path.name == "manifest.json":
                continue
            
            # Calculate relative path from project root
            rel_path = file_path.relative_to(PROJECT_ROOT)
            file_hash = calculate_sha256(file_path)
            
            if file_hash:
                manifest["files"].append({
                    "path": str(rel_path),
                    "sha256": file_hash,
                    "size_bytes": file_path.stat().st_size,
                    "type": "binary" if file_path.suffix in [".bin", ".out"] else "data" if file_path.suffix in [".csv", ".json", ".jsonl", ".npy"] else "plot" if file_path.suffix in [".png"] else "unknown"
                })
                total_files += 1
            else:
                logger.warning(f"Failed to hash file: {file_path}")

    manifest["total_files"] = total_files
    
    # Save manifest if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest saved to {output_path}")
    else:
        # Default output
        default_output = DATA_DIR / "manifest.json"
        with open(default_output, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest saved to {default_output}")
        
    return manifest

def main():
    """Entry point for manifest generation."""
    logging.basicConfig(level=logging.INFO)
    manifest = generate_manifest()
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()