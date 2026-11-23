"""
Task T032b: Verify Clips & Record Source
Computes SHA-256 checksums of fetched clips and writes a manifest containing
dataset URL, version ID, and per-clip checksums to data/metadata/clip_manifest.json.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Import existing utility from project API surface
from src.lib.utils import compute_file_checksum
from src.config import DATA_DIR


def verify_clips(clips_dir: Path, manifest_path: Path, dataset_info: Dict[str, str]) -> Dict[str, Any]:
    """
    Verifies clips in the given directory by computing SHA-256 checksums.
    
    Args:
        clips_dir: Path to the directory containing clip files.
        manifest_path: Path where the manifest JSON will be written.
        dataset_info: Dictionary containing 'url' and 'version_id' of the source dataset.
        
    Returns:
        Dictionary representing the manifest content.
        
    Raises:
        FileNotFoundError: If the clips directory does not exist.
        ValueError: If no clip files are found.
    """
    if not clips_dir.exists():
        raise FileNotFoundError(f"Clips directory not found: {clips_dir}")
        
    # Find all video files (mp4, mov, avi, etc.)
    clip_files = list(clips_dir.glob("*"))
    # Filter for common video extensions
    video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.wmv'}
    clip_files = [f for f in clip_files if f.suffix.lower() in video_extensions]
    
    if not clip_files:
        raise ValueError(f"No video files found in {clips_dir}")
        
    manifest = {
        "dataset_url": dataset_info.get("url", "unknown"),
        "dataset_version_id": dataset_info.get("version_id", "unknown"),
        "verification_status": "success",
        "clips": []
    }
    
    for clip_path in sorted(clip_files):
        try:
            checksum = compute_file_checksum(clip_path, algorithm="sha256")
            clip_entry = {
                "filename": clip_path.name,
                "relative_path": str(clip_path.relative_to(clips_dir)),
                "checksum_sha256": checksum,
                "size_bytes": clip_path.stat().st_size
            }
            manifest["clips"].append(clip_entry)
        except Exception as e:
            manifest["verification_status"] = "partial_failure"
            manifest["errors"].append({
                "filename": clip_path.name,
                "error": str(e)
            })
    
    # Ensure manifest directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write manifest to disk
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
        
    return manifest


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify fetched clips and record source checksums."
    )
    parser.add_argument(
        "--clips-dir",
        type=str,
        default=str(DATA_DIR / "stimuli" / "raw"),
        help="Directory containing the fetched clip files."
    )
    parser.add_argument(
        "--manifest-output",
        type=str,
        default=str(DATA_DIR / "metadata" / "clip_manifest.json"),
        help="Path to write the verification manifest JSON."
    )
    parser.add_argument(
        "--dataset-url",
        type=str,
        required=True,
        help="URL of the source dataset."
    )
    parser.add_argument(
        "--dataset-version",
        type=str,
        required=True,
        help="Version ID of the source dataset."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    
    clips_dir = Path(args.clips_dir)
    manifest_path = Path(args.manifest_output)
    dataset_info = {
        "url": args.dataset_url,
        "version_id": args.dataset_version
    }
    
    try:
        manifest = verify_clips(clips_dir, manifest_path, dataset_info)
        print(f"Verification complete. Manifest written to: {manifest_path}")
        print(f"Total clips verified: {len(manifest['clips'])}")
        print(f"Status: {manifest['verification_status']}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error during verification: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
