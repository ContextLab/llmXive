"""
fetch_clips.py

Implements the T032 task: download meeting background clips from the
HuggingFace dataset ``video-conference-backgrounds`` and record provenance
information (dataset version, source URL, per‑file SHA‑256 checksums) in
``data/metadata/dataset_manifest.json``.
"""

import argparse
import json
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict

from huggingface_hub import HfApi, hf_hub_download

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def ensure_output_directory(output_dir: Path) -> None:
    """
    Ensure that the required output directories exist.

    Parameters
    ----------
    output_dir: Path
        Directory where the downloaded stimuli will be stored.
    """
    # Create the stimuli raw directory
    output_dir.mkdir(parents=True, exist_ok=True)
    # Ensure the metadata directory exists as well
    metadata_dir = Path("data/metadata")
    metadata_dir.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of a file.

    Parameters
    ----------
    file_path: Path
        Path to the file.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    hash_sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

# ----------------------------------------------------------------------
# Core download logic
# ----------------------------------------------------------------------
def download_dataset_items(
    repo_id: str,
    output_dir: Path,
    revision: str = "main",
    repo_type: str = "dataset",
) -> List[Path]:
    """
    Download all files from a HuggingFace dataset repository.

    Parameters
    ----------
    repo_id: str
        Identifier of the HuggingFace dataset (e.g. ``video-conference-backgrounds``).
    output_dir: Path
        Directory where files will be saved.
    revision: str, optional
        Git revision / commit hash to fetch. Defaults to ``main``.
    repo_type: str, optional
        Repository type – always ``dataset`` for this project.

    Returns
    -------
    List[Path]
        List of paths to the downloaded files.
    """
    api = HfApi()
    # Retrieve the complete file list for the repository
    try:
        repo_files = api.list_repo_files(
            repo_id=repo_id, revision=revision, repo_type=repo_type
        )
    except Exception as exc:
        raise RuntimeError(
            f"Unable to list files for repository '{repo_id}' (revision={revision})."
        ) from exc

    downloaded_paths: List[Path] = []
    for file_name in repo_files:
        # Skip directories (the API returns only file paths)
        try:
            local_path = hf_hub_download(
                repo_id=repo_id,
                filename=file_name,
                revision=revision,
                repo_type=repo_type,
                local_dir=output_dir,
            )
            downloaded_paths.append(Path(local_path))
        except Exception as exc:
            # Propagate the error – we do **not** silently ignore failures
            raise RuntimeError(
                f"Failed to download '{file_name}' from '{repo_id}'."
            ) from exc
    return downloaded_paths

# ----------------------------------------------------------------------
# Manifest creation
# ----------------------------------------------------------------------
def save_manifest(
    repo_id: str,
    revision: str,
    files: List[Path],
    manifest_path: Path,
    source_url: str,
) -> None:
    """
    Write a JSON manifest containing dataset provenance and checksums.

    Parameters
    ----------
    repo_id: str
        The HuggingFace dataset identifier.
    revision: str
        The specific revision (commit hash) that was downloaded.
    files: List[Path]
        List of local file paths that were downloaded.
    manifest_path: Path
        Destination path for the JSON manifest.
    source_url: str
        Human‑readable URL of the dataset.
    """
    checksum_map: Dict[str, str] = {}
    for file_path in files:
        # Store checksums relative to the output directory for readability
        rel_path = file_path.relative_to(file_path.parents[2])  # data/stimuli/raw/<file>
        checksum_map[str(rel_path)] = compute_sha256(file_path)

    manifest = {
        "dataset": repo_id,
        "revision": revision,
        "source_url": source_url,
        "files": checksum_map,
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)

# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def parse_arguments(argv: List[str] | None = None) -> argparse.Namespace:
    """
    Parse command‑line arguments for the fetch script.

    Returns
    -------
    argparse.Namespace
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Download meeting background clips from a HuggingFace dataset "
        "and record a provenance manifest."
    )
    parser.add_argument(
        "--repo-id",
        default="video-conference-backgrounds",
        help="HuggingFace dataset identifier (default: video-conference-backgrounds).",
    )
    parser.add_argument(
        "--revision",
        default="main",
        help="Dataset revision / commit hash to download (default: main).",
    )
    parser.add_argument(
        "--output-dir",
        default="data/stimuli/raw",
        help="Directory where downloaded files will be stored.",
    )
    parser.add_argument(
        "--manifest-path",
        default="data/metadata/dataset_manifest.json",
        help="Path to write the dataset manifest JSON.",
    )
    return parser.parse_args(argv)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> None:
    """
    Orchestrate the download and manifest creation.

    This function is deliberately side‑effectful: it writes files to the
    repository's ``data/`` tree.  It raises on any failure so that the
    automated pipeline can detect missing real data rather than silently
    falling back to synthetic placeholders.
    """
    args = parse_arguments(argv)

    output_dir = Path(args.output_dir)
    manifest_path = Path(args.manifest_path)

    # Step 1: ensure directories exist
    ensure_output_directory(output_dir)

    # Step 2: download all dataset items
    downloaded_files = download_dataset_items(
        repo_id=args.repo_id,
        output_dir=output_dir,
        revision=args.revision,
        repo_type="dataset",
    )

    # Step 3: construct a human‑readable source URL
    source_url = f"https://huggingface.co/datasets/{args.repo_id}"

    # Step 4: write the manifest
    save_manifest(
        repo_id=args.repo_id,
        revision=args.revision,
        files=downloaded_files,
        manifest_path=manifest_path,
        source_url=source_url,
    )

    print(
        f"Download complete. Manifest written to '{manifest_path}'. "
        f"Total files: {len(downloaded_files)}."
    )

if __name__ == "__main__":
    main()