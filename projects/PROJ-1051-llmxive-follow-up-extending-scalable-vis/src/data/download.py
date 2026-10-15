"""
src/data/download.py

Downloads scientific document corpora from verified HuggingFace repositories
without relying on the `datasets` library (which pulls in `pyarrow`). The
implementation uses `huggingface_hub` to fetch the raw files (images and
JSON annotations) directly, stores them on disk, and records SHA‑256 checksums
for reproducibility.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict

import yaml
from tqdm import tqdm
from huggingface_hub import snapshot_download

def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of ``file_path``."""
    h = hashlib.sha256()
    try:
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except (FileNotFoundError, PermissionError):
        return "<file not accessible>"
    return h.hexdigest()


def log_and_store_checksums(dataset_name: str, dataset_dir: Path, checksum_path: Path) -> None:
    """
    Compute SHA‑256 checksums for every file under ``dataset_dir`` (the
    downloaded corpus) and write them to ``checksum_path`` in YAML format.
    """
    checksums: Dict[str, str] = {}
    for file in dataset_dir.rglob("*"):
        if file.is_file():
            rel = str(file.relative_to(dataset_dir))
            checksums[rel] = compute_sha256(file)

    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with checksum_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump({dataset_name: checksums}, f, sort_keys=False)

    print(f"=== SHA‑256 checksums for {dataset_name} written to {checksum_path} ===")


def count_pages_with_layout(dataset_dir: Path) -> int:
    """
    Count the number of JSON annotation files (one per page) present in
    ``dataset_dir``. This is a lightweight proxy for pages that have layout
    annotations.
    """
    return sum(1 for _ in dataset_dir.rglob("*.json"))


def _download_repo(repo_id: str, output_root: Path) -> Path:
    """
    Download a HuggingFace dataset repository (type=dataset) into ``output_root``.
    Only image files (png, jpg, jpeg, tif, tiff) and JSON annotation files
    are retained to keep the size manageable.
    The function returns the path to the downloaded directory.
    """
    print(f"Downloading repository '{repo_id}'...")
    # Use snapshot_download to get the whole repo; we limit files with allow_patterns
    repo_path = snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        allow_patterns=["*.png", "*.jpg", "*.jpeg", "*.tif", "*.tiff", "*.json"],
        local_dir=output_root,
        cache_dir=str(Path.home() / ".cache" / "huggingface" / "datasets"),
    )
    return Path(repo_path)


def download_layout_corpus(output_dir: Path, min_pages: int = 10_000) -> None:
    """
    Download the primary PubMed‑Layout corpus, falling back to its official
    fallback if necessary. The function ensures at least ``min_pages``
    pages with layout annotations.
    The downloaded files are placed under ``output_dir / "layout_corpus"``.
    """
    primary_repo = "allenai/pubmed-layout"
    fallback_repo = "allenai/pubmed-layout-fallback"

    target_dir = output_dir / "layout_corpus"

    # Try primary
    try:
        primary_path = _download_repo(primary_repo, target_dir)
        primary_pages = count_pages_with_layout(primary_path)
        print(f"Primary dataset pages with layout: {primary_pages}")
    except Exception as e:
        print(f"Failed to download primary dataset '{primary_repo}': {e}")
        primary_path = None
        primary_pages = 0

    # If primary insufficient, try fallback
    if primary_pages < min_pages:
        needed = min_pages - primary_pages
        print(f"Primary pages ({primary_pages}) < {min_pages}. Trying fallback...")
        try:
            fallback_path = _download_repo(fallback_repo, target_dir)
            fallback_pages = count_pages_with_layout(fallback_path)
            print(f"Fallback dataset pages with layout: {fallback_pages}")
            # Merge fallback into primary directory (if primary exists)
            if primary_path:
                for src_file in fallback_path.rglob("*"):
                    rel = src_file.relative_to(fallback_path)
                    dest_file = primary_path / rel
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    if not dest_file.exists():
                        dest_file.write_bytes(src_file.read_bytes())
                combined_path = primary_path
            else:
                combined_path = fallback_path
                # Ensure the final directory name is still 'layout_corpus'
                combined_path.rename(target_dir / "layout_corpus")
                combined_path = target_dir / "layout_corpus"
            total_pages = count_pages_with_layout(combined_path)
        except Exception as e:
            print(f"Fallback download failed: {e}")
            total_pages = primary_pages
    else:
        combined_path = primary_path
        total_pages = primary_pages

    print(f"Total pages with layout after fallback handling: {total_pages}")

    if total_pages < min_pages:
        raise RuntimeError(
            f"Insufficient annotated pages (FR-007). Found {total_pages}, need {min_pages}."
        )

    # Record checksums
    checksum_path = Path("artifacts/checksums/downloads.yaml")
    log_and_store_checksums("layout_corpus", combined_path, checksum_path)


def download_docvqa(output_dir: Path) -> None:
    """
    Download the DocVQA benchmark dataset and store it under
    ``output_dir / "docvqa"``.
    """
    repo_id = "allenai/docvqa"
    target_dir = output_dir / "docvqa"
    try:
        _download_repo(repo_id, target_dir)
    except Exception as e:
        print(f"DocVQA download failed: {e}")
        raise

    checksum_path = Path("artifacts/checksums/downloads.yaml")
    log_and_store_checksums("docvqa", target_dir, checksum_path)


def download_dataset(dataset_name: str, output_dir: Path) -> None:
    """Dispatcher for dataset downloads."""
    name = dataset_name.lower()
    if name in ("publaynet", "layout_corpus"):
        download_layout_corpus(output_dir)
    elif name == "docvqa":
        download_docvqa(output_dir)
    else:
        raise ValueError(f"Unsupported dataset: {dataset_name}")


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-name", type=str, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        download_dataset(args.dataset_name, args.output_dir)
        print("✅ Download and verification completed successfully.")
    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
