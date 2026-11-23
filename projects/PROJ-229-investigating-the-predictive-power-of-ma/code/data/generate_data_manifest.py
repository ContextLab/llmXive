"""
generate_data_manifest.py

This script scans the project's data directories, computes SHA256 checksums for each file,
and writes a manifest JSON file summarizing raw, processed, external, and result artifacts.

The manifest is written to `data/results/data_manifest.json` with the following structure:

{
    "generated_at": "<ISO timestamp>",
    "entries": [
        {
            "path": "data/raw/materials_project_data.json",
            "category": "raw",
            "size_bytes": 12345,
            "sha256": "deadbeef..."
        },
        ...
    ]
}

The script can be executed directly:
    python code/data/generate_data_manifest.py

It relies on the project's `utils.checksum.compute_sha256` helper.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from utils.checksum import compute_sha256

# Configure a basic logger for this script
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def collect_files(base_dir: Path, category: str) -> List[Dict]:
    """
    Recursively collect file metadata from ``base_dir``.

    Parameters
    ----------
    base_dir : Path
        Directory to scan.
    category : str
        Logical category for the files (e.g., "raw", "processed", "external", "results").

    Returns
    -------
    List[Dict]
        A list of dictionaries with keys: path, category, size_bytes, sha256.
    """
    entries = []
    if not base_dir.is_dir():
        logger.warning("Directory %s does not exist; skipping.", base_dir)
        return entries

    for file_path in base_dir.rglob("*"):
        if file_path.is_file():
            try:
                rel_path = file_path.relative_to(Path.cwd())
            except ValueError:
                # If the script is run from a different cwd, fallback to a relative path from project root
                rel_path = file_path.relative_to(Path(__file__).parents[3])

            size = file_path.stat().st_size
            try:
                checksum = compute_sha256(file_path)
            except Exception as exc:
                logger.error("Failed to compute checksum for %s: %s", file_path, exc)
                checksum = None

            entry = {
                "path": str(rel_path).replace("\\", "/"),
                "category": category,
                "size_bytes": size,
                "sha256": checksum,
            }
            entries.append(entry)
    return entries


def generate_manifest() -> Dict:
    """
    Build the complete manifest dictionary by scanning the standard data sub‑directories.
    """
    manifest_entries: List[Dict] = []

    # Define the directories and their logical categories
    data_root = Path.cwd() / "data"
    categories = {
        "raw": data_root / "raw",
        "processed": data_root / "processed",
        "external": data_root / "external",
        "results": data_root / "results",
    }

    for cat, dir_path in categories.items():
        logger.info("Collecting %s files from %s", cat, dir_path)
        manifest_entries.extend(collect_files(dir_path, cat))

    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "entries": manifest_entries,
    }
    return manifest


def write_manifest(manifest: Dict, output_path: Path) -> None:
    """
    Write the manifest dictionary to ``output_path`` as pretty‑printed JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    logger.info("Data manifest written to %s", output_path)


def main() -> None:
    """
    Entry point for the script.
    """
    logger.info("Starting data manifest generation")
    manifest = generate_manifest()
    output_file = Path.cwd() / "data" / "results" / "data_manifest.json"
    write_manifest(manifest, output_file)
    logger.info("Data manifest generation completed")


if __name__ == "__main__":
    main()
