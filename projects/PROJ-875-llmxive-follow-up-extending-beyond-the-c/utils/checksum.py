"""
Checksum utility for llmXive project.

Generates SHA-256 checksums for files in data/processed/ and records them
into a state manifest YAML file.

Implements Constitution Principle III: Data Integrity via Checksums.
"""
import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent

DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STATE_DIR = PROJECT_ROOT / "state"
CHECKSUM_MANIFEST_PATH = STATE_DIR / "checksums.yaml"

# Supported file extensions for checksumming
SUPPORTED_EXTENSIONS = {'.json', '.ascii', '.csv', '.txt', '.log', '.yaml', '.yml'}

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the SHA-256 hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def get_files_to_checksum(directory: Path, extensions: Optional[set] = None) -> List[Path]:
    """
    Recursively find all files in a directory with supported extensions.
    
    Args:
        directory: Root directory to search
        extensions: Set of file extensions to include (default: SUPPORTED_EXTENSIONS)
        
    Returns:
        List of Path objects for files to checksum
    """
    if extensions is None:
        extensions = SUPPORTED_EXTENSIONS
        
    files = []
    if not directory.exists():
        return files
        
    for file_path in directory.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            files.append(file_path)
            
    return sorted(files)  # Sort for deterministic ordering

def generate_checksum_manifest(directory: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate a manifest of checksums for all files in the directory.
    
    Args:
        directory: Directory to checksum (default: DATA_PROCESSED_DIR)
        
    Returns:
        Dictionary containing manifest metadata and checksums
        
    Raises:
        FileNotFoundError: If the directory does not exist
    """
    if directory is None:
        directory = DATA_PROCESSED_DIR
        
    if not directory.exists():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
        
    files = get_files_to_checksum(directory)
    
    checksums = {}
    for file_path in files:
        relative_path = file_path.relative_to(PROJECT_ROOT)
        checksum = calculate_sha256(file_path)
        checksums[str(relative_path)] = {
            "sha256": checksum,
            "size_bytes": file_path.stat().st_size,
            "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
    
    manifest = {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "directory": str(directory.relative_to(PROJECT_ROOT)),
        "algorithm": "sha256",
        "file_count": len(checksums),
        "checksums": checksums
    }
    
    return manifest

def save_manifest(manifest: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save the checksum manifest to a YAML file.
    
    Args:
        manifest: The manifest dictionary to save
        output_path: Path to save the manifest (default: CHECKSUM_MANIFEST_PATH)
        
    Returns:
        Path to the saved manifest file
    """
    if output_path is None:
        output_path = CHECKSUM_MANIFEST_PATH
        
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(manifest, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
    return output_path

def load_manifest(manifest_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Load a checksum manifest from a YAML file.
    
    Args:
        manifest_path: Path to the manifest file (default: CHECKSUM_MANIFEST_PATH)
        
    Returns:
        Manifest dictionary or None if file does not exist
    """
    if manifest_path is None:
        manifest_path = CHECKSUM_MANIFEST_PATH
        
    if not manifest_path.exists():
        return None
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def verify_checksums(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Verify that current file checksums match the stored manifest.
    
    Args:
        manifest_path: Path to the manifest file (default: CHECKSUM_MANIFEST_PATH)
        
    Returns:
        Dictionary with verification results
    """
    if manifest_path is None:
        manifest_path = CHECKSUM_MANIFEST_PATH
        
    if not manifest_path.exists():
        return {
            "status": "error",
            "message": f"Manifest not found: {manifest_path}",
            "verified": 0,
            "failed": 0,
            "missing": 0,
            "details": []
        }
        
    manifest = load_manifest(manifest_path)
    if manifest is None:
        return {
            "status": "error",
            "message": "Failed to load manifest",
            "verified": 0,
            "failed": 0,
            "missing": 0,
            "details": []
        }
        
    results = {
        "status": "success",
        "verified": 0,
        "failed": 0,
        "missing": 0,
        "details": []
    }
    
    for relative_path, info in manifest.get("checksums", {}).items():
        file_path = PROJECT_ROOT / relative_path
        
        if not file_path.exists():
            results["missing"] += 1
            results["details"].append({
                "path": relative_path,
                "status": "missing"
            })
            continue
            
        current_hash = calculate_sha256(file_path)
        stored_hash = info["sha256"]
        
        if current_hash == stored_hash:
            results["verified"] += 1
            results["details"].append({
                "path": relative_path,
                "status": "ok",
                "sha256": current_hash
            })
        else:
            results["failed"] += 1
            results["details"].append({
                "path": relative_path,
                "status": "mismatch",
                "stored_sha256": stored_hash,
                "current_sha256": current_hash
            })
    
    if results["failed"] > 0 or results["missing"] > 0:
        results["status"] = "warning"
        
    return results

def main():
    """
    Main entry point for checksum generation and verification.
    
    Usage:
        python utils/checksum.py [--verify] [--output <path>]
    """
    import sys
    
    verify_mode = "--verify" in sys.argv
    output_path_str = None
    
    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            output_path_str = sys.argv[i + 1]
    
    output_path = Path(output_path_str) if output_path_str else None
    
    if verify_mode:
        print("Verifying checksums...")
        results = verify_checksums()
        print(f"Status: {results['status']}")
        print(f"Verified: {results['verified']}")
        print(f"Failed: {results['failed']}")
        print(f"Missing: {results['missing']}")
        
        if results["details"]:
            print("\nDetails:")
            for detail in results["details"]:
                print(f"  {detail['path']}: {detail['status']}")
        
        return 0 if results["status"] == "success" else 1
    else:
        print(f"Generating checksums for {DATA_PROCESSED_DIR}...")
        
        if not DATA_PROCESSED_DIR.exists():
            print(f"Warning: {DATA_PROCESSED_DIR} does not exist. Creating empty manifest.")
            manifest = {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "directory": "data/processed",
                "algorithm": "sha256",
                "file_count": 0,
                "checksums": {}
            }
        else:
            manifest = generate_checksum_manifest(DATA_PROCESSED_DIR)
            print(f"Found {manifest['file_count']} files to checksum.")
        
        if output_path is None:
            output_path = CHECKSUM_MANIFEST_PATH
        
        saved_path = save_manifest(manifest, output_path)
        print(f"Manifest saved to: {saved_path}")
        print(f"Total files: {manifest['file_count']}")
        
        return 0

if __name__ == "__main__":
    sys.exit(main())
