"""
fetch_and_archive.py
---------------------

One‑time setup script for the Visual Complexity pilot study.

It downloads the first 500 images from the HuggingFace
``video-conference-backgrounds`` dataset (train split), saves them
under ``data/stimuli/raw/`` and records a SHA‑256 checksum for each
file in a ``checksums.json`` manifest.  Subsequent executions are a
no‑op if the archive (both the image files **and** the manifest) already
exists.

The script is deliberately lightweight and raises on any failure so
that the execution gate can surface real‑data problems.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict

from datasets import load_dataset
from PIL import Image
from io import BytesIO

# Re‑use the project's checksum helper to stay consistent.
from src.lib.utils import compute_file_checksum

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
OUTPUT_DIR = Path("data/stimuli/raw")
MANIFEST_PATH = OUTPUT_DIR / "checksums.json"
NUM_ITEMS = 500
DATASET_NAME = "video-conference-backgrounds"
SPLIT = "train"


def _ensure_output_dir() -> None:
    """Create the output directory if it does not exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _load_existing_manifest() -> Dict[str, str]:
    """Load an existing manifest if present, otherwise return an empty dict."""
    if MANIFEST_PATH.is_file():
        with MANIFEST_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_manifest(manifest: Dict[str, str]) -> None:
    """Write the manifest to disk (pretty‑printed JSON)."""
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)


def _download_and_save() -> Dict[str, str]:
    """
    Download the first ``NUM_ITEMS`` examples from the dataset,
    store each image as ``{index:05d}.png`` and compute its checksum.
    Returns a mapping ``filename -> checksum``.
    """
    manifest: Dict[str, str] = {}
    # ``streaming=True`` avoids pulling the entire dataset into memory.
    ds = load_dataset(DATASET_NAME, split=SPLIT, streaming=True)

    for idx, example in enumerate(ds):
        if idx >= NUM_ITEMS:
            break

        # The dataset stores the image under the ``image`` key.
        raw_image = example["image"]

        # ``raw_image`` can be either a PIL.Image (eager mode) or a dict
        # with a ``bytes`` field when streaming.  Handle both.
        if isinstance(raw_image, Image.Image):
            pil_img = raw_image
        else:
            pil_img = Image.open(BytesIO(raw_image["bytes"]))

        # Ensure a deterministic format – PNG is loss‑less and widely supported.
        filename = f"{idx:05d}.png"
        out_path = OUTPUT_DIR / filename
        pil_img.save(out_path, format="PNG")

        # Compute checksum using the shared utility.
        checksum = compute_file_checksum(out_path)
        manifest[filename] = checksum

    return manifest


def main() -> None:
    """
    Entry point for the script.

    * If ``checksums.json`` already exists **and** the number of image
      files matches ``NUM_ITEMS``, the function exits silently.
    * Otherwise the dataset is fetched, images are stored and a new
      manifest is written.
    """
    _ensure_output_dir()

    # Fast‑path: archive already present?
    existing_manifest = _load_existing_manifest()
    existing_images = list(OUTPUT_DIR.glob("*.png"))
    if len(existing_images) == NUM_ITEMS and existing_manifest:
        # Basic sanity check – verify that the recorded checksums match the
        # current files.  If they do not, raise so the user knows the archive
        # is corrupted.
        for img_path in existing_images:
            expected = existing_manifest.get(img_path.name)
            if expected is None:
                raise RuntimeError(
                    f"Missing checksum entry for {img_path.name} in manifest."
                )
            actual = compute_file_checksum(img_path)
            if actual != expected:
                raise RuntimeError(
                    f"Checksum mismatch for {img_path.name}: "
                    f"expected {expected}, got {actual}"
                )
        # Archive is valid – nothing to do.
        return

    # Archive missing or incomplete – (re)create it.
    manifest = _download_and_save()
    _save_manifest(manifest)


if __name__ == "__main__":
    # Running the module directly performs the one‑time fetch.
    main()
