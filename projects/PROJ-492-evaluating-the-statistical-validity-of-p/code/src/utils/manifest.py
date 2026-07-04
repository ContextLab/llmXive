"""
Manifest generation and validation utilities.
Computes SHA256 hashes for generated artifacts and manages manifest.json.
"""
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from code.src.utils.logger import get_default_logger, AuditLogger, get_error_message

logger = get_default_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for hashing: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        raise

def find_files_to_hash(
    output_dir: Path,
    exclude_patterns: Optional[List[str]] = None
) -> List[Path]:
    """
    Recursively find all files in output_dir to include in manifest.
    Excludes patterns like __pycache__, *.pyc, and specific directories.
    """
    exclude_patterns = exclude_patterns or []
    files = []
    for root, dirs, filenames in Path(output_dir).rglob("*"):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if not any(d.startswith(p) for p in ["__pycache__", ".git"])]
        
        for filename in filenames:
            file_path = root / filename
            # Skip excluded file extensions
            if any(filename.endswith(ext) for ext in [".pyc", ".pyo"]):
                continue
            # Skip specific patterns
            if any(pattern in str(file_path) for pattern in exclude_patterns):
                continue
            files.append(file_path)
    return sorted(files)

def generate_manifest(
    output_dir: Path,
    output_manifest_path: Optional[Path] = None,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a manifest.json with SHA256 hashes for all files in output_dir.
    
    Args:
        output_dir: Directory containing generated artifacts.
        output_manifest_path: Path to write the manifest file. If None, defaults to output_dir/manifest.json.
        exclude_patterns: List of patterns to exclude.
        
    Returns:
        Dictionary containing the manifest data.
    """
    if not output_dir.exists():
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")
    
    if output_manifest_path is None:
        output_manifest_path = output_dir / "manifest.json"
    
    files = find_files_to_hash(output_dir, exclude_patterns)
    
    if not files:
        logger.warning(f"No files found to hash in {output_dir}")
    
    manifest_data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project_id": "PROJ-492-evaluating-the-statistical-validity-of-p",
        "version": "1.0.0",
        "files": {}
    }
    
    for file_path in files:
        try:
            relative_path = file_path.relative_to(output_dir)
            sha256_hash = compute_sha256(file_path)
            manifest_data["files"][str(relative_path)] = {
                "sha256": sha256_hash,
                "size_bytes": file_path.stat().st_size
            }
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            # Continue with other files rather than failing completely
            continue
    
    # Write manifest to file
    try:
        with open(output_manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
        logger.info(f"Manifest written to {output_manifest_path}")
    except Exception as e:
        logger.error(f"Failed to write manifest to {output_manifest_path}: {e}")
        raise
    
    return manifest_data

def validate_manifest(
    manifest_path: Path,
    output_dir: Path
) -> Tuple[bool, List[str]]:
    """
    Validate that the manifest hashes match the actual file hashes.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    if not manifest_path.exists():
        return False, [f"Manifest file not found: {manifest_path}"]
    
    if not output_dir.exists():
        return False, [f"Output directory not found: {output_dir}"]
    
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in manifest: {e}"]
    
    errors = []
    files_in_manifest = manifest_data.get("files", {})
    
    for relative_path_str, file_info in files_in_manifest.items():
        file_path = output_dir / relative_path_str
        expected_hash = file_info.get("sha256")
        
        if not file_path.exists():
            errors.append(f"File missing: {relative_path_str}")
            continue
        
        try:
            actual_hash = compute_sha256(file_path)
            if actual_hash != expected_hash:
                errors.append(
                    f"Hash mismatch for {relative_path_str}: "
                    f"expected {expected_hash}, got {actual_hash}"
                )
        except Exception as e:
            errors.append(f"Error hashing {relative_path_str}: {e}")
    
    is_valid = len(errors) == 0
    return is_valid, errors

def main():
    """CLI entry point for manifest generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate or validate manifest.json")
    parser.add_argument(
        "action",
        choices=["generate", "validate"],
        help="Action to perform: generate or validate"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory containing artifacts"
    )
    parser.add_argument(
        "--manifest-path",
        type=str,
        default=None,
        help="Path to manifest file (for validation)"
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    
    if args.action == "generate":
        try:
            manifest = generate_manifest(output_dir)
            print(f"Manifest generated successfully with {len(manifest['files'])} files.")
            return 0
        except Exception as e:
            print(f"Error generating manifest: {e}", file=sys.stderr)
            return 1
    elif args.action == "validate":
        manifest_path = Path(args.manifest_path) if args.manifest_path else output_dir / "manifest.json"
        is_valid, errors = validate_manifest(manifest_path, output_dir)
        
        if is_valid:
            print("Manifest validation passed.")
            return 0
        else:
            print("Manifest validation failed:")
            for error in errors:
                print(f"  - {error}")
            return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
