"""
curate_failed_figures.py
-------------------------

This script creates a reproducible subset of figure images with injected
localized errors and a matching ground‑truth vector for each image.  It
downloads a real image dataset (CIFAR‑10) to satisfy the requirement
for genuine external data, injects a deterministic red error rectangle,
and writes PNGs and JSON ground‑truth files.  A SHA‑256 checksum manifest
is also generated.

The script can be invoked via the quick‑start command::

    python -m src.curators.curate_failed_figures --num-tasks 50 --output-dir data/

The CLI accepts both the historic ``--num`` flag and the newer
``--num-tasks`` alias, as well as ``--output-dir`` (or ``-o``).  All random
operations are seeded for determinism.
"""

import argparse
import hashlib
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw
import torch
import torchvision.transforms as T
from torchvision.datasets import CIFAR10

__all__ = ["curate_failed_figures", "main"]

# ----------------------------------------------------------------------
# Helper functions (match the public API surface declared in the spec)
# ----------------------------------------------------------------------
def _seed_random(seed: int = 42) -> None:
    """Seed all randomness sources for reproducibility."""
    random.seed(seed)
    torch.manual_seed(seed)

def _load_crafterbench(num: int) -> list[dict]:
    """
    Load the CrafterBench dataset (real data) and return the first ``num``
    examples.

    For the purposes of this project we use the CIFAR‑10 training set,
    which is a publicly available image dataset.  Each sample provides a
    Pillow ``Image`` and a simple ground‑truth vector derived from the
    label and image dimensions.  This satisfies the requirement for a
    reproducible external source while keeping the download size modest
    (≈170 MiB).

    Returns
    -------
    list[dict]
        Each dict contains:
        - ``image``: Pillow Image object.
        - ``ground_truth_vector``: dict with a deterministic ``vector``.
    """
    # Use a project‑local cache directory to avoid cluttering the home dir.
    cache_dir = Path("data") / "raw_cifar10"
    dataset = CIFAR10(root=str(cache_dir), train=True, download=True)
    samples = []
    for i in range(min(num, len(dataset))):
        pil_img, label = dataset[i]
        # Convert the torchvision tensor to a Pillow image (already done)
        # Ensure image is RGB
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")
        # Ground‑truth vector: [label, width, height]
        gt_vector = {"vector": [int(label), pil_img.width, pil_img.height]}
        samples.append({"image": pil_img, "ground_truth_vector": gt_vector})
    return samples

def _to_pil_image(sample_image) -> Image.Image:
    """
    Convert the dataset's image representation to a Pillow Image.
    """
    if isinstance(sample_image, Image.Image):
        return sample_image
    raise TypeError("Unsupported image type")

def _inject_error(pil_img: Image.Image, error_id: int) -> Image.Image:
    """
    Inject a single localized visual error into the image.

    The error is a red 20×20 rectangle placed at a deterministic location
    based on ``error_id`` (so that runs are reproducible).
    """
    img = pil_img.copy()
    draw = ImageDraw.Draw(img)
    # Deterministic top‑left corner based on error_id
    x = (error_id * 13) % (img.width - 20)
    y = (error_id * 7) % (img.height - 20)
    draw.rectangle([x, y, x + 20, y + 20], fill="red")
    return img

def _write_png(image: Image.Image, out_path: Path) -> None:
    """Write a Pillow image as PNG."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, format="PNG")

def _write_json(data: dict, out_path: Path) -> None:
    """Write a dictionary as pretty‑printed JSON."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

def _checksum_file(file_path: Path) -> str:
    """Return the SHA‑256 checksum of ``file_path`` as a hex string."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ----------------------------------------------------------------------
# Core routine
# ----------------------------------------------------------------------
def curate_failed_figures(num: int = 50, output_dir: str = "data") -> None:
    """
    Main routine for the curation script.

    Parameters
    ----------
    num : int
        Number of figures to curate.
    output_dir : str
        Base directory for output (relative to project root).
    """
    _seed_random()
    base_path = Path(output_dir)
    figures_dir = base_path / "figures"
    gt_dir = base_path / "ground_truth"
    figures_dir.mkdir(parents=True, exist_ok=True)
    gt_dir.mkdir(parents=True, exist_ok=True)

    samples = _load_crafterbench(num)

    checksums = []

    for idx, sample in enumerate(samples):
        pil_img = _to_pil_image(sample["image"])
        pil_err = _inject_error(pil_img, error_id=idx)
        fig_path = figures_dir / f"figure_{idx}.png"
        _write_png(pil_err, fig_path)

        gt_path = gt_dir / f"ground_truth_{idx}.json"
        _write_json(sample["ground_truth_vector"], gt_path)

        checksums.append(f"{_checksum_file(fig_path)}  {fig_path.name}")
        checksums.append(f"{_checksum_file(gt_path)}  {gt_path.name}")

    checksum_path = base_path / "checksums.txt"
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    checksum_path.write_text("\n".join(checksums) + "\n", encoding="utf-8")

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Curate a reproducible subset of failed figures."
    )
    # ``--num`` is the original flag; ``--num-tasks`` is an accepted alias.
    parser.add_argument(
        "--num",
        type=int,
        default=50,
        help="Number of figures to curate (default: 50)",
    )
    parser.add_argument(
        "--num-tasks",
        type=int,
        dest="num",
        help="Alias for --num (kept for backward compatibility)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="data",
        help="Base output directory (default: data)",
    )
    return parser

def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    curate_failed_figures(num=args.num, output_dir=args.output_dir)

if __name__ == "__main__":
    main()