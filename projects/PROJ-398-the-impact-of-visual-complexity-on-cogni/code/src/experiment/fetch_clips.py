"""
fetch_clips.py

Fetch real meeting background frames/clips from the HuggingFace
`video-conference-backgrounds` dataset.

This script downloads the media files to a specified output directory and
writes a manifest JSON file containing metadata (filename, source URL,
SHA‑256 checksum). It is intended for the main study (US2) and must operate
on real data – no synthetic fall‑backs are provided.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

import requests
from datasets import load_dataset

# Local utilities for checksum computation
from src.lib.utils import compute_file_checksum

def ensure_output_directory(output_dir: Path) -> None:
    """
    Ensure that the output directory exists.

    Parameters
    ----------
    output_dir : Path
        Directory where downloaded files will be stored.
    """
    output_dir.mkdir(parents=True, exist_ok=True)


def download_dataset_items(
    dataset_name: str = "HuggingFaceM4/video-conference-backgrounds",
    split: str = "train",
    output_dir: Path = Path("data/stimuli/meeting_clips"),
    max_items: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Stream the dataset and download each media item.

    The dataset contains either an ``image`` field (URL to a JPEG/PNG) or a
    ``video`` field (URL to a video file). Only items with a direct URL are
    downloaded; others are skipped with a warning.

    Parameters
    ----------
    dataset_name : str
        HuggingFace dataset identifier.
    split : str
        Split to download (e.g., ``train``).
    output_dir : Path
        Destination directory for downloaded files.
    max_items : int | None
        Optional cap on the number of items to fetch. ``None`` means download
        the full split.

    Returns
    -------
    List[Dict[str, Any]]
        Manifest entries for each successfully downloaded file.
    """
    manifest: List[Dict[str, Any]] = []

    # Load dataset in streaming mode to avoid materialising the whole split.
    try:
        ds = load_dataset(dataset_name, split=split, streaming=True)
    except Exception as exc:
        print(f"Failed to load dataset {dataset_name} (split={split}): {exc}", file=sys.stderr)
        raise

    for idx, item in enumerate(ds):
        if max_items is not None and idx >= max_items:
            break

        # Determine the media URL. The dataset may provide either `image` or `video`.
        url = item.get("image") or item.get("video")
        if not isinstance(url, str):
            print(f"Skipping item {idx}: no downloadable URL found.", file=sys.stderr)
            continue

        # Derive a filename from the URL.
        filename = Path(url).name
        if not filename:
            print(f"Skipping item {idx}: could not extract filename from URL.", file=sys.stderr)
            continue

        dest_path = output_dir / filename

        # Skip already‑downloaded files to make the script resumable.
        if dest_path.is_file():
            checksum = compute_file_checksum(dest_path)
            manifest.append(
                {
                    "filename": filename,
                    "url": url,
                    "checksum": checksum,
                    "status": "already_exists",
                }
            )
            continue

        try:
            with requests.get(url, stream=True, timeout=30) as response:
                response.raise_for_status()
                with open(dest_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep‑alive chunks
                            f.write(chunk)
        except Exception as exc:
            print(f"Failed to download {url}: {exc}", file=sys.stderr)
            continue

        # Compute checksum for integrity verification.
        checksum = compute_file_checksum(dest_path)

        manifest.append(
            {
                "filename": filename,
                "url": url,
                "checksum": checksum,
                "status": "downloaded",
            }
        )

        # Simple progress output.
        if (idx + 1) % 50 == 0:
            print(f"Downloaded {idx + 1} items...")

    return manifest


def save_manifest(manifest: List[Dict[str, Any]], output_dir: Path) -> None:
    """
    Write the manifest JSON file to the output directory.

    Parameters
    ----------
    manifest : List[Dict[str, Any]]
        List of metadata dictionaries for each downloaded file.
    output_dir : Path
        Directory where ``manifest.json`` will be written.
    """
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    print(f"Manifest written to {manifest_path}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch real meeting background clips from the HuggingFace dataset."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/stimuli/meeting_clips"),
        help="Directory to store downloaded clips (default: %(default)s).",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help="Maximum number of items to download (default: all).",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="train",
        help="Dataset split to download (default: %(default)s).",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="HuggingFaceM4/video-conference-backgrounds",
        help="HuggingFace dataset identifier (default: %(default)s).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    output_dir: Path = args.output_dir
    ensure_output_directory(output_dir)

    start = time.time()
    manifest = download_dataset_items(
        dataset_name=args.dataset,
        split=args.split,
        output_dir=output_dir,
        max_items=args.max_items,
    )
    save_manifest(manifest, output_dir)
    elapsed = time.time() - start
    print(f"Finished downloading. Total items: {len(manifest)}. Elapsed time: {elapsed:.2f}s")


if __name__ == "__main__":
    main()