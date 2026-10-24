"""Download real object patches for the counterfactual pipeline.

This script fetches the CIFAR‑100 dataset (a public, permissively‑licensed
image collection) via ``torchvision`` and extracts a single exemplar image
for each class. Each exemplar is saved as a PNG patch in
``data/patches/`` and a ``manifest.csv`` file is written that maps the
patch filename to the original dataset URL and the human‑readable class
label.

The script is deliberately lightweight and runs on CPU only.  It is
idempotent – existing patches are overwritten only if the script is run
again, which guarantees reproducibility for downstream stages that rely
on these patches (e.g. ``src.data.counterfactual``).

Usage (as a module):
    python -m src.data.patches_download

The quickstart driver will automatically invoke this script via the
``execute`` flag in the task definition, ensuring that the required
artifacts are present before any counterfactual generation begins.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import torch
from torchvision import datasets, transforms
from PIL import Image

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# CIFAR‑100 download URL (used for manifest reference)
CIFAR100_URL = "https://www.cs.toronto.edu/~kriz/cifar-100-python.tar.gz"

def _save_patch(image: Image.Image, dest_path: Path) -> None:
    """Save a single image patch as PNG, creating parent directories."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest_path, format="PNG")

def _write_manifest(manifest_path: Path, records: list[tuple[str, str, str]]) -> None:
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
    Download CIFAR‑100, extract one exemplar per class, and write patches.

    Returns
    -------
    int
        0 on success, non‑zero on failure.
    """
    try:
        # ``torchvision`` will download the dataset into ``root`` if needed.
        dataset = datasets.CIFAR100(
            root=str(root),
            train=True,
            download=True,
            transform=transforms.ToTensor(),
        )
    except Exception as exc:
        log.error("Failed to download CIFAR‑100 dataset: %s", exc)
        return 1

    # Map class index → class name (human‑readable)
    class_names = dataset.classes  # list of 100 class strings
    # Build a dict to hold the first encountered image per class
    first_per_class: dict[int, Image.Image] = {}

    # The raw dataset returns (PIL.Image, int) when ``transform`` is None.
    # We loaded with a Tensor transform, so we need to re‑load without it
    # to obtain PIL images for saving.
    raw_dataset = datasets.CIFAR100(
        root=str(root),
        train=True,
        download=False,
        transform=None,
    )

    for img, label in raw_dataset:
        if label not in first_per_class:
            first_per_class[label] = img
            if len(first_per_class) == len(class_names):
                break

    patches_dir = paths.data("patches")
    patches_dir.mkdir(parents=True, exist_ok=True)

    manifest_records: list[tuple[str, str, str]] = []

    for idx, class_name in enumerate(class_names):
        img = first_per_class.get(idx)
        if img is None:
            # This should never happen for CIFAR‑100, but we guard against it.
            log.warning("No exemplar found for class %s (index %d)", class_name, idx)
            continue
        filename = f"{class_name.replace(' ', '_').lower()}.png"
        dest_path = patches_dir / filename
        _save_patch(img, dest_path)
        manifest_records.append((filename, CIFAR100_URL, class_name))

    manifest_path = patches_dir / "manifest.csv"
    _write_manifest(manifest_path, manifest_records)

    # Verification step – ensure at least 20 distinct patches exist.
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

def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download real object patches (CIFAR‑100) for the pipeline."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=str(Path.cwd()),
        help="Root directory for downloading the CIFAR‑100 dataset.",
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    args = parse_cli_args(argv)
    return generate_patches(Path(args.root))

if __name__ == "__main__":
    sys.exit(main())
