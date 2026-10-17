"""
curators/curate_failed_figures.py
---------------------------------

This module implements the data‑curation step for the cognitive‑load study.
It downloads a reproducible 50‑figure subset from the *CrafterBench* dataset,
injects a single localized visual error into each figure, writes the modified
PNG files to ``data/figures/``, stores the corresponding ground‑truth layout
vectors as JSON files in ``data/ground_truth/``, and finally creates a checksum
manifest ``data/checksums.txt``.
"""

import argparse
import hashlib
import io
import json
import random
from pathlib import Path

import cv2
import numpy as np
from datasets import load_dataset
from PIL import Image

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _seed_random(seed: int = 42) -> None:
    """Seed all randomness sources for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def _load_crafterbench(num: int) -> list[dict]:
    """
    Load the CrafterBench dataset and return the first ``num`` examples.

    The expected fields for each example are:
    - ``image``: either a PIL.Image, a NumPy array, or raw bytes that can be
      interpreted as an image.
    - ``ground_truth_vector``: a JSON‑serialisable structure representing the
      layout vector for the figure.

    Raises:
        RuntimeError: if the dataset cannot be loaded.
    """
    try:
        # The exact HF hub identifier for CrafterBench is assumed to be
        # ``crafterbench``. Adjust if the real identifier differs.
        ds = load_dataset("crafterbench", split="test", streaming=False)
    except Exception as exc:
        raise RuntimeError("Failed to load CrafterBench dataset") from exc

    # Ensure we have enough samples
    if len(ds) < num:
        raise RuntimeError(f"Requested {num} figures but dataset contains only {len(ds)} samples")

    # Take a deterministic slice
    return ds.select(range(num))

def _to_pil_image(sample_image) -> Image.Image:
    """Convert the dataset's image representation to a Pillow Image."""
    if isinstance(sample_image, Image.Image):
        return sample_image
    if isinstance(sample_image, np.ndarray):
        # Convert from BGR (OpenCV) or RGB array to PIL
        if sample_image.shape[-1] == 3:
            return Image.fromarray(sample_image)
    if isinstance(sample_image, (bytes, bytearray)):
        return Image.open(io.BytesIO(sample_image))
    # Fallback – let Pillow try to open it directly
    raise TypeError("Unsupported image format in dataset sample")

def _inject_error(pil_img: Image.Image, error_id: int) -> Image.Image:
    """
    Inject a single localized visual error into the image.

    The error is a red 20×20 rectangle placed at a deterministic location
    based on ``error_id`` (so that runs are reproducible).

    Returns a new Pillow Image with the error applied.
    """
    # Convert to OpenCV format (BGR)
    cv_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    h, w, _ = cv_img.shape
    # Deterministic top‑left corner based on the id
    x = (error_id * 13) % (w - 30)
    y = (error_id * 17) % (h - 30)

    # Draw a solid red rectangle (BGR: 0,0,255)
    cv2.rectangle(cv_img, (x, y), (x + 20, y + 20), (0, 0, 255), thickness=-1)

    # Convert back to Pillow (RGB)
    pil_err = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
    return pil_err

def _write_png(image: Image.Image, out_path: Path) -> None:
    """Write a Pillow image as PNG."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, format="PNG")

def _write_json(data: dict, out_path: Path) -> None:
    """Write a dictionary as pretty‑printed JSON."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _checksum_file(file_path: Path) -> str:
    """Return the SHA‑256 checksum of ``file_path`` as a hex string."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def curate_failed_figures(num: int = 50, output_dir: str = "data") -> None:
    """
    Main routine for the curation script.

    Args:
        num: Number of figures to curate.
        output_dir: Base directory for output (relative to project root).
    """
    _seed_random()

    figures_dir = paths.data("figures")
    gt_dir = paths.data("ground_truth")
    checksum_path = paths.data("checksums.txt")

    log.info(f"Creating output directories under {figures_dir} and {gt_dir}")

    # Load data
    log.info(f"Loading {num} samples from CrafterBench")
    samples = _load_crafterbench(num)

    checksum_entries = []

    for idx, sample in enumerate(samples):
        # Extract image and ground‑truth vector
        raw_image = sample.get("image")
        if raw_image is None:
            raise RuntimeError(f"Sample {idx} missing 'image' field")
        pil_img = _to_pil_image(raw_image)

        gt_vector = sample.get("ground_truth_vector")
        if gt_vector is None:
            raise RuntimeError(f"Sample {idx} missing 'ground_truth_vector' field")

        # Inject error
        pil_err = _inject_error(pil_img, idx)

        # File names
        fig_name = f"figure_{idx:04d}.png"
        gt_name = f"figure_{idx:04d}.json"

        fig_path = figures_dir / fig_name
        gt_path = gt_dir / gt_name

        # Write files
        _write_png(pil_err, fig_path)
        _write_json({"ground_truth_vector": gt_vector}, gt_path)

        # Record checksum
        checksum = _checksum_file(fig_path)
        checksum_entries.append(f"{fig_name} {checksum}")

        log.debug(f"Curated {fig_name}")

    # Write checksum manifest
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with checksum_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(checksum_entries) + "\n")

    log.info(f"Curated {num} figures. Checksums written to {checksum_path}")

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Curate a reproducible subset of CrafterBench figures with injected errors."
    )
    parser.add_argument(
        "--num",
        type=int,
        default=50,
        help="Number of figures to curate (default: 50).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data",
        help="Base output directory (default: 'data').",
    )
    return parser

def main() -> None:
    args = _build_arg_parser().parse_args()
    curate_failed_figures(num=args.num, output_dir=args.output_dir)

if __name__ == "__main__":
    main()
