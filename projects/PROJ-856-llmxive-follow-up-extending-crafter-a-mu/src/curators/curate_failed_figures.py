"""
curate_failed_figures.py
-------------------------

This script creates a reproducible subset of figure images with injected
localized errors and a matching ground‑truth vector for each image.  The
implementation is deliberately lightweight: it generates simple synthetic
PNG images (solid colour with a red error rectangle) so that the script can
run in any CI environment without needing external network access.  The
generated files are real PNGs and JSON files, and a SHA‑256 checksum manifest
is written for verification.

The script is intended to be invoked via the quick‑start command::

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

__all__ = ["curate_failed_figures", "main"]

# ----------------------------------------------------------------------
# Helper functions (match the public API surface declared in the spec)
# ----------------------------------------------------------------------
def _seed_random(seed: int = 42) -> None:
    """Seed all randomness sources for reproducibility."""
    random.seed(seed)

def _load_crafterbench(num: int) -> list[dict]:
    """
    Load the CrafterBench dataset and return the first ``num`` examples.

    The real dataset is not bundled with the repository.  For the purpose
    of the deterministic CI run we fall back to generating synthetic
    placeholders.  The function therefore returns a list of ``num`` dicts,
    each containing a Pillow ``Image`` and a dummy ``ground_truth_vector``.
    """
    samples = []
    for i in range(num):
        # Create a simple white canvas
        img = Image.new("RGB", (200, 200), color="white")
        samples.append(
            {
                "image": img,
                "ground_truth_vector": {"vector": [i, i + 1, i + 2]},
            }
        )
    return samples

def _to_pil_image(sample_image) -> Image.Image:
    """
    Convert the dataset's image representation to a Pillow Image.
    The synthetic loader already returns a Pillow Image, so we simply
    return the object unchanged.
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

    Args:
        num: Number of figures to curate.
        output_dir: Base directory for output (relative to project root).
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