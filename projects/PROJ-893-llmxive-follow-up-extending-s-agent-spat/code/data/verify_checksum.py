"""
T006a: Verify the downloaded dataset's SHA-256 checksums against
data/raw/sampled_manifest.json (Constitution Principle III) before extraction.

Gate behavior:
  - If data/raw/sampled_manifest.json is missing -> abort with error (exit 1).
  - If any manifest file is missing or its checksum mismatches -> abort (exit 1).
  - If all checksums match -> exit 0.

Dependency: must run AFTER T006 (download.py) has produced both
data/raw/sampled_scenes.jsonl and data/raw/sampled_manifest.json.
"""
import os
import sys
import hashlib
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import Config

config = Config()

# Resolve data/raw robustly across Config attribute shapes.
def _resolve_data_raw() -> Path:
    if hasattr(config, "DATA_RAW") and isinstance(getattr(config, "DATA_RAW"), Path):
        return config.DATA_RAW
    if hasattr(config, "DATA_DIR"):
        return Path(config.DATA_DIR) / "raw"
    return PROJECT_ROOT / "data" / "raw"

DATA_RAW_PATH = _resolve_data_raw()
MANIFEST_PATH = DATA_RAW_PATH / "sampled_manifest.json"
# Legacy fallback location for the manifest.
FALLBACK_MANIFEST = PROJECT_ROOT / "data" / "sampled_manifest.json"
if not MANIFEST_PATH.exists() and FALLBACK_MANIFEST.exists():
    MANIFEST_PATH = FALLBACK_MANIFEST


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hex digest of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_manifest(manifest_path: Optional[Path] = None) -> List[Dict[str, str]]:
    """Load and validate the sampled_manifest.json file.

    Raises FileNotFoundError if the manifest is missing (gate failure),
    ValueError if it is malformed.
    """
    path = Path(manifest_path) if manifest_path else MANIFEST_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Manifest not found at {path}. "
            "Please ensure T006 (download.py) has run successfully and "
            "generated data/raw/sampled_manifest.json."
        )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Manifest at {path} must be a JSON list.")
    if len(data) == 0:
        raise ValueError(f"Manifest at {path} is empty.")
    for item in data:
        if not isinstance(item, dict) or "file" not in item or "sha256" not in item:
            raise ValueError(
                f"Manifest item missing 'file' or 'sha256': {item!r}"
            )
    return data


def verify_directory_integrity(
    directory: Path,
    manifest: Optional[List[Dict[str, str]]] = None,
) -> bool:
    """Verify SHA-256 checksums of manifest-listed files in a directory.

    Returns True only if every manifest entry has an existing file whose
    hash matches. Missing files or hash mismatches -> False.
    """
    directory = Path(directory)
    if manifest is None:
        manifest = load_manifest()

    all_valid = True
    files_checked = 0

    for item in manifest:
        filename = item["file"]
        expected_hash = item["sha256"]

        file_path = directory / filename
        if not file_path.exists():
            # Allow manifest entries recorded relative to project root.
            alt = PROJECT_ROOT / filename
            if alt.exists():
                file_path = alt
            else:
                print(f"Missing file: {filename} (expected in {directory})")
                all_valid = False
                continue

        actual_hash = compute_sha256(file_path)
        if actual_hash != expected_hash:
            print(
                f"Checksum mismatch for {filename}: "
                f"expected {expected_hash}, got {actual_hash}"
            )
            all_valid = False
        else:
            print(f"Verified: {filename}")
            files_checked += 1

    if files_checked == 0:
        print(f"Warning: No files from manifest found in {directory}.")
        return False

    return all_valid


def main():
    """CLI entry point for the checksum verification gate."""
    parser = argparse.ArgumentParser(
        description="Verify directory checksums against manifest (T006a)"
    )
    parser.add_argument(
        "--directory",
        type=str,
        default=str(DATA_RAW_PATH),
        help="Directory to verify (default: data/raw)",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=str(MANIFEST_PATH),
        help="Path to sampled_manifest.json (default: data/raw/sampled_manifest.json)",
    )
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist.")
        sys.exit(1)

    try:
        manifest = load_manifest(Path(args.manifest))
    except (FileNotFoundError, ValueError) as e:
        # Gate: missing or malformed manifest -> abort.
        print(f"Verification error: {e}")
        sys.exit(1)

    try:
        if verify_directory_integrity(directory, manifest):
            print("Verification successful: All checksums match.")
            sys.exit(0)
        else:
            print(
                "Verification failed: Checksum mismatches or missing files detected."
            )
            sys.exit(1)
    except Exception as e:  # unexpected I/O errors -> fail loudly
        print(f"Verification error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
