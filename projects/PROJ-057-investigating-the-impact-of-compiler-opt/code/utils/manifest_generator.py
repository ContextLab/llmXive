import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure we can import from the project root if run as a script
# The import style matches the API surface provided:
# from utils.logger import ... (relative to code/)
# We are in code/utils/, so we use relative imports or absolute if sys.path adjusted.
# However, to be safe and consistent with the "import as" provided in the surface:
# The surface says: import as `from utils.manifest_generator import ...`
# This implies the script is run from the project root with `code` in path, or imported as `utils.manifest_generator`.
# We will write standard Python code.

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        raise
    except PermissionError:
        logging.error(f"Permission denied: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error hashing {file_path}: {e}")
        raise

def scan_directory(directory: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """Scan directory for files, optionally filtering by extensions."""
    if not directory.exists():
        logging.warning(f"Directory does not exist: {directory}")
        return []
    
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = Path(root) / filename
            if extensions:
                if any(filename.endswith(ext) for ext in extensions):
                    files.append(file_path)
            else:
                files.append(file_path)
    return files

def generate_manifest(
    base_dir: Path,
    output_path: Path,
    include_dirs: List[str],
    extensions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a manifest.json with SHA-256 hashes for specified files.
    
    Args:
        base_dir: The root directory to scan (project root usually).
        output_path: Path where manifest.json will be written.
        include_dirs: List of relative directory paths to include (e.g., ['data', 'code/kernels']).
        extensions: Optional list of file extensions to include (e.g., ['.json', '.csv', '.png', '.cpp']).
    
    Returns:
        The manifest dictionary.
    """
    manifest = {
        "generated_at": None, # Will be set if needed, or left out per spec
        "files": {}
    }
    
    logging.info(f"Generating manifest for directories: {include_dirs}")
    
    for rel_dir in include_dirs:
        full_dir = base_dir / rel_dir
        if not full_dir.exists():
            logging.warning(f"Skipping non-existent directory: {full_dir}")
            continue
        
        files = scan_directory(full_dir, extensions)
        for file_path in files:
            # Store relative path from base_dir
            rel_path = file_path.relative_to(base_dir)
            try:
                file_hash = calculate_sha256(file_path)
                manifest["files"][str(rel_path)] = {
                    "sha256": file_hash,
                    "size_bytes": file_path.stat().st_size
                }
            except Exception as e:
                logging.error(f"Failed to hash {file_path}: {e}")
                # Continue scanning, but log the failure
    
    # Write to output path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    logging.info(f"Manifest written to {output_path} with {len(manifest['files'])} entries.")
    return manifest

def main():
    """
    Main entry point for generating the manifest.
    Scans 'data' and 'code' directories (excluding source code if desired, but spec says binaries/logs/csv/plots).
    Specifically targets:
    - data/raw, data/intermediates, data/results
    - code/kernels (for .cpp and compiled binaries if they exist)
    """
    import argparse
    import sys
    from datetime import datetime

    parser = argparse.ArgumentParser(description="Generate SHA-256 manifest for project artifacts.")
    parser.add_argument(
        "--base-dir", 
        type=Path, 
        default=Path.cwd(), 
        help="Base directory of the project (default: current working directory)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/manifest.json"),
        help="Output path for manifest.json (default: data/manifest.json)"
    )
    parser.add_argument(
        "--include",
        nargs="+",
        default=["data", "code/kernels", "code/benchmarks", "code/analysis"],
        help="Relative directories to include in the scan"
    )
    parser.add_argument(
        "--ext",
        nargs="+",
        default=[".json", ".csv", ".png", ".jpg", ".txt", ".log", ".jsonl", ".cpp", ".bin"],
        help="File extensions to include"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Add timestamp to manifest if desired, or keep it simple
    # The spec says "manifest.json generation with SHA-256 hashes"
    manifest = generate_manifest(
        base_dir=args.base_dir,
        output_path=args.output,
        include_dirs=args.include,
        extensions=args.ext
    )
    
    # Optionally add metadata
    manifest["metadata"] = {
        "generated_at": datetime.now().isoformat(),
        "project": "PROJ-057-investigating-the-impact-of-compiler-opt",
        "task": "T034"
    }

    # Re-write with metadata
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Manifest generated: {args.output}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
