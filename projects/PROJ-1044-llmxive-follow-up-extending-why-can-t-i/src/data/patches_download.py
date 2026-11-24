"""Download real object patches for the counterfactual pipeline.

This script fetches the CIFAR‑100 dataset (a public, permissively‑licensed
image collection) via a direct HTTP request, extracts one exemplar image
for each class, and writes those exemplars as PNG patches into
``data/patches/``.  A ``manifest.csv`` file is also written that maps the
patch filename to the original dataset URL and the human‑readable class
label.

The implementation avoids importing heavyweight ``torch``/``torchvision``
packages to keep start‑up time low and to stay comfortably within the
300 s execution budget on the CI runner.

Usage (as a module):
    python -m src.data.patches_download

The quickstart driver will automatically invoke this script via the
``run_all`` pipeline, ensuring that the required artifacts are present
before any counterfactual generation begins.
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import pickle
import tarfile
import sys
from pathlib import Path
from typing import List, Tuple

import numpy as np
import requests
from PIL import Image

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# CIFAR‑100 download URL (used for manifest reference)
CIFAR100_URL = "https://www.cs.toronto.edu/~kriz/cifar-100-python.tar.gz"

# Directory inside the repository where we cache the downloaded archive
# and its extracted contents.  Using a hidden folder avoids clutter.
_CACHE_DIR_NAME = ".cifar100_cache"


def _download_archive(root: Path) -> Path:
    """
    Download the CIFAR‑100 ``tar.gz`` archive into ``root`` if it does not
    already exist, and return the path to the downloaded file.
    """
    cache_dir = root / _CACHE_DIR_NAME
    cache_dir.mkdir(parents=True, exist_ok=True)
    archive_path = cache_dir / "cifar-100-python.tar.gz"

    if archive_path.is_file():
        log.info("CIFAR‑100 archive already present at %s", archive_path)
        return archive_path

    log.info("Downloading CIFAR‑100 archive from %s", CIFAR100_URL)
    try:
        with requests.get(CIFAR100_URL, stream=True, timeout=120) as r:
            r.raise_for_status()
            with archive_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
    except Exception as exc:
        log.error("Failed to download CIFAR‑100 archive: %s", exc)
        raise

    log.info("Download complete: %s", archive_path)
    return archive_path


def _extract_archive(archive_path: Path, root: Path) -> Path:
    """
    Extract ``archive_path`` into a sub‑directory of ``root`` and return the
    path to the extracted top‑level folder (``cifar-100-python``).
    """
    extract_dir = root / _CACHE_DIR_NAME / "extracted"
    if (extract_dir / "cifar-100-python").is_dir():
        log.info("CIFAR‑100 already extracted at %s", extract_dir)
        return extract_dir / "cifar-100-python"

    log.info("Extracting CIFAR‑100 archive to %s", extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=extract_dir)

    extracted_path = extract_dir / "cifar-100-python"
    if not extracted_path.is_dir():
        raise RuntimeError("Extraction failed – expected directory missing.")
    log.info("Extraction complete.")
    return extracted_path


def _load_meta(meta_path: Path) -> List[str]:
    """
    Load the list of fine‑grained class names from ``meta_path``.
    """
    with meta_path.open("rb") as f:
        meta = pickle.load(f, encoding="latin1")
    return meta["fine_label_names"]  # type: ignore[return-value]


def _load_training_data(train_path: Path) -> Tuple[np.ndarray, List[int]]:
    """
    Load training images and their fine‑grained labels.
    Returns a tuple ``(images, labels)`` where ``images`` is a NumPy array
    of shape ``(N, 3, 32, 32)`` and ``labels`` is a list of integers.
    """
    with train_path.open("rb") as f:
        data_dict = pickle.load(f, encoding="latin1")
    raw = data_dict["data"]  # shape (N, 3072)
    images = raw.reshape(-1, 3, 32, 32)  # (N, C, H, W)
    labels = data_dict["fine_labels"]
    return images, labels


def _save_patch(image: Image.Image, dest_path: Path) -> None:
    """Save a single image patch as PNG, creating parent directories."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest_path, format="PNG")


def _write_manifest(manifest_path: Path, records: List[Tuple[str, str, str]]) -> None:
    """
    Write ``manifest.csv`` with columns ``filename,source_url,class_label``.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "source_url", "class_label"])
        for filename, source_url, class_label in records:
            writer.writerow([filename, source_url, class_label])
    log.info("Wrote manifest with %d entries to %s", len(records), manifest_path)


def generate_patches(root: Path) -> int:
    """
    Download CIFAR‑100 (if necessary), extract one exemplar per class,
    and write the patches to ``data/patches/`` together with a manifest.

    Returns
    -------
    int
        0 on success, non‑zero on failure.
    """
    try:
        archive_path = _download_archive(root)
        extracted_path = _extract_archive(archive_path, root)

        meta_path = extracted_path / "meta"
        train_path = extracted_path / "train"

        class_names = _load_meta(meta_path)
        images, labels = _load_training_data(train_path)

        # Build a dict: class index -> first image index encountered
        first_idx_per_class: dict[int, int] = {}
        for idx, label in enumerate(labels):
            if label not in first_idx_per_class:
                first_idx_per_class[label] = idx
                if len(first_idx_per_class) == len(class_names):
                    break

        patches_dir = paths.data("patches")
        patches_dir.mkdir(parents=True, exist_ok=True)

        manifest_records: List[Tuple[str, str, str]] = []

        for class_idx, class_name in enumerate(class_names):
            img_idx = first_idx_per_class.get(class_idx)
            if img_idx is None:
                log.warning("No exemplar found for class %s (index %d)", class_name, class_idx)
                continue

            # CIFAR‑100 images are 32×32; upscale to 64×64 for consistency
            img_array = images[img_idx].transpose(1, 2, 0)  # (H, W, C)
            pil_img = Image.fromarray(img_array)
            pil_img = pil_img.resize((64, 64), Image.BILINEAR)

            filename = f"{class_name.replace(' ', '_').lower()}.png"
            dest_path = patches_dir / filename
            _save_patch(pil_img, dest_path)

            manifest_records.append((filename, CIFAR100_URL, class_name))

        manifest_path = patches_dir / "manifest.csv"
        _write_manifest(manifest_path, manifest_records)

        # Verification – ensure we have at least 20 distinct patches.
        patch_files = list(patches_dir.glob("*.png"))
        if len(patch_files) < 20:
            log.error(
                "Expected at least 20 patches, but only %d were created.",
                len(patch_files),
            )
            return 1
        if len(patch_files) != len(manifest_records):
            log.error(
                "Patch count (%d) does not match manifest rows (%d).",
                len(patch_files),
                len(manifest_records),
            )
            return 1

        log.info(
            "Successfully created %d object patches in %s",
            len(patch_files),
            patches_dir,
        )
        return 0

    except Exception as exc:
        log.error("Patch generation failed: %s", exc)
        return 1


def parse_cli_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download real object patches (CIFAR‑100) for the pipeline."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=str(Path.cwd()),
        help="Root directory for caching the CIFAR‑100 download.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_cli_args(argv)
    return generate_patches(Path(args.root))


if __name__ == "__main__":
    sys.exit(main())