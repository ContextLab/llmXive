"""Create a sample EEG file for T012 verification.

This script reads data/raw/download_manifest.json and copies the first
available subject's data file to data/raw/sample_eeg_verification.fif.

Dependency: T009 (Download) must have completed successfully.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# Add project root to path for imports if run as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

MANIFEST_PATH = Path("data/raw/download_manifest.json")
OUTPUT_PATH = Path("data/raw/sample_eeg_verification.fif")

logger = get_logger("create_sample_verification")


def load_manifest() -> dict:
    """Load and return the download manifest."""
    if not MANIFEST_PATH.exists():
        logger.log("manifest_missing", path=str(MANIFEST_PATH))
        raise FileNotFoundError(
            f"Download manifest not found at {MANIFEST_PATH}. "
            "Please run code/download.py first."
        )
    
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)


def find_first_eeg_file(manifest: dict) -> Path:
    """Find the first EEG data file listed in the manifest."""
    files = manifest.get("files", [])
    
    if not files:
        logger.log("no_files_in_manifest")
        raise ValueError("No files found in download manifest.")
    
    # Look for .fif, .edf, or .npz files (common EEG formats)
    eeg_extensions = {".fif", ".edf", ".npz", ".eeg", ".vhdr"}
    
    for file_entry in files:
        file_path = Path(file_entry.get("path", ""))
        if file_path.suffix.lower() in eeg_extensions:
            absolute_path = Path(file_entry["path"])
            if absolute_path.exists():
                logger.log("found_eeg_file", path=str(absolute_path))
                return absolute_path
    
    # Fallback: use the first file if no specific extension matches
    first_file = Path(files[0].get("path", ""))
    if first_file.exists():
        logger.log("using_first_file", path=str(first_file), warning="No standard EEG extension found")
        return first_file
    
    logger.log("no_valid_eeg_file_found")
    raise ValueError("No valid EEG data file found in manifest.")


def copy_to_sample(source_path: Path, dest_path: Path) -> None:
    """Copy the source file to the sample verification location."""
    # Ensure destination directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.log("copying_file", source=str(source_path), dest=str(dest_path))
    shutil.copy2(source_path, dest_path)
    
    if not dest_path.exists():
        logger.log("copy_failed", dest=str(dest_path))
        raise RuntimeError(f"Failed to copy file to {dest_path}")
    
    logger.log("sample_created", path=str(dest_path))


def main() -> int:
    """Main entry point."""
    try:
        logger.log("starting_sample_creation")
        
        # Load manifest
        manifest = load_manifest()
        
        # Find first EEG file
        source_file = find_first_eeg_file(manifest)
        
        # Copy to sample location
        copy_to_sample(source_file, OUTPUT_PATH)
        
        logger.log("sample_creation_complete", path=str(OUTPUT_PATH))
        print(f"Sample file created at: {OUTPUT_PATH}")
        return 0
        
    except FileNotFoundError as e:
        logger.log("error", message=str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        logger.log("error", message=str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.log("unexpected_error", message=str(e))
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())