"""
curate_failed_figures.py
-------------------------

This script creates a reproducible subset of figure images with injected
localized errors and a matching ground‑truth vector for each image.  It
attempts to download a **verified** CrafterBench subset (exactly 50 failed
figures).  If the verified source is unavailable the script aborts with a
clear error message “verified source unavailable”, fulfilling FR‑001.

The CLI accepts the historic ``--num`` flag, the newer ``--num-tasks`` alias,
an optional ``--download`` flag for backward‑compatibility with older
quick‑start commands, ``--output-dir`` (or ``-o``), and ``--verify-only``
for deterministic synthetic generation used only in CI.

All random operations are seeded for determinism.
"""

import argparse
import hashlib
import json
import os
import random
import sys
import tempfile
import zipfile
from pathlib import Path

import requests
from PIL import Image, ImageDraw

__all__ = ["curate_failed_figures", "main"]

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# In a real deployment this URL should point to a verified, publicly‑
# accessible archive that contains exactly 50 failed figures from the
# CrafterBench dataset together with matching ground‑truth JSON files.
# For the purpose of this repository the URL is intentionally a placeholder;
# the script will abort with the required error message when the resource
# cannot be fetched.
VERIFIED_URL = "https://example.com/crafterbench_subset.zip"

# ----------------------------------------------------------------------
# Helper functions (match the public API surface declared in the spec)
# ----------------------------------------------------------------------
def _seed_random(seed: int = 42) -> None:
    """Seed all randomness sources for reproducibility."""
    random.seed(seed)

def _check_network(timeout: int = 5) -> bool:
    """
    Very small network probe to decide whether the internet is reachable.
    Returns True if a request succeeds, False otherwise.
    """
    try:
        # A lightweight request; any public site is fine.
        requests.get("https://www.google.com/generate_204", timeout=timeout)
        return True
    except Exception:
        return False

def _download_verified_dataset(destination: Path) -> Path:
    """
    Download the verified CrafterBench subset archive and return the path
    to the downloaded file.

    Parameters
    ----------
    destination: Path
        Directory where the downloaded file will be stored.

    Returns
    -------
    Path
        Path to the downloaded zip file.

    Raises
    ------
    RuntimeError
        If the download fails (non‑200 status or network error).
    """
    try:
        response = requests.get(VERIFIED_URL, stream=True, timeout=10)
        if response.status_code != 200:
            raise RuntimeError
    except Exception:
        raise RuntimeError("verified source unavailable")

    destination.mkdir(parents=True, exist_ok=True)
    zip_path = destination / "crafterbench_subset.zip"
    with zip_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return zip_path

def _extract_dataset(zip_path: Path, extract_to: Path) -> None:
    """
    Extract the downloaded zip archive.

    Parameters
    ----------
    zip_path: Path
        Path to the zip file.
    extract_to: Path
        Directory where the archive will be unpacked.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)

def _load_crafterbench(num: int) -> list[dict]:
    """
    Load the verified CrafterBench subset (real data) and return the first
    ``num`` examples.

    The function expects the extracted dataset to contain paired files:
    ``figure_<idx>.png`` and ``ground_truth_<idx>.json`` where ``idx`` starts
    at 0.  The JSON file must contain a ``vector`` field.

    Returns
    -------
    list[dict]
        Each dict contains:
        - ``image``: Pillow Image object.
        - ``ground_truth_vector``: dict with a deterministic ``vector``.
    """
    # Step 1 – ensure we have network connectivity; otherwise abort early.
    if not _check_network():
        sys.stderr.write("verified source unavailable\\n")
        sys.exit(1)

    # Step 2 – download the verified archive to a temporary location.
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        try:
            zip_path = _download_verified_dataset(tmp_path)
        except RuntimeError as e:
            sys.stderr.write(str(e) + "\\n")
            sys.exit(1)

        # Step 3 – extract the archive.
        extract_dir = tmp_path / "extracted"
        _extract_dataset(zip_path, extract_dir)

        # Step 4 – collect figure / ground‑truth pairs.
        figures = sorted(extract_dir.glob("figure_*.png"))
        gts = sorted(extract_dir.glob("ground_truth_*.json"))

        if len(figures) < num or len(gts) < num:
            sys.stderr.write(
                "verified source unavailable (insufficient items)\\n"
            )
            sys.exit(1)

        samples = []
        for idx in range(num):
            fig_path = figures[idx]
            gt_path = gts[idx]

            # Load image.
            img = Image.open(fig_path).convert("RGB")

            # Load ground‑truth vector.
            with gt_path.open("r", encoding="utf-8") as f:
                gt_data = json.load(f)

            samples.append({"image": img, "ground_truth_vector": gt_data})
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
# Synthetic data generation (used when ``--verify-only`` is set)
# ----------------------------------------------------------------------
def _generate_synthetic(num: int, output_dir: str) -> None:
    """
    Generate a deterministic synthetic dataset without external network
    access.  Images are simple white canvases with a red error rectangle;
    ground‑truth vectors follow the pattern ``[idx, width, height]``.
    """
    base_path = Path(output_dir)
    figures_dir = base_path / "figures"
    gt_dir = base_path / "ground_truth"
    figures_dir.mkdir(parents=True, exist_ok=True)
    gt_dir.mkdir(parents=True, exist_ok=True)

    checksums = []

    for idx in range(num):
        # Create a plain white image (32×32, matching CIFAR‑10 size)
        img = Image.new("RGB", (32, 32), color="white")
        img_err = _inject_error(img, error_id=idx)

        fig_path = figures_dir / f"figure_{idx}.png"
        _write_png(img_err, fig_path)

        gt_path = gt_dir / f"ground_truth_{idx}.json"
        gt_vector = {"vector": [idx, 32, 32]}
        _write_json(gt_vector, gt_path)

        checksums.append(f"{_checksum_file(fig_path)}  {fig_path.name}")
        checksums.append(f"{_checksum_file(gt_path)}  {gt_path.name}")

    checksum_path = base_path / "checksums.txt"
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    checksum_path.write_text("\n".join(checksums) + "\n", encoding="utf-8")

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
    parser.add_argument(
        "--verify-only",
        action="store_true",
        default=False,
        help="Generate deterministic synthetic data without downloading external datasets",
    )
    # Compatibility flag used by older quick‑start scripts.
    parser.add_argument(
        "--download",
        action="store_true",
        default=False,
        help=argparse.SUPPRESS,
    )
    return parser

def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    # ``--verify-only`` takes precedence – generate synthetic data.
    if args.verify_only:
        _generate_synthetic(num=args.num, output_dir=args.output_dir)
        return

    # ``--download`` is accepted for backward compatibility but has no
    # effect beyond signalling intent.  The real download is performed
    # inside ``_load_crafterbench``.
    # The flag is kept to avoid argparse errors when old quick‑start
    # commands are used.
    _ = args.download  # unused, retained for compatibility

    # Before attempting a potentially long download, quickly check for network.
    if not _check_network():
        sys.stderr.write("verified source unavailable\\n")
        sys.exit(1)

    # Attempt to load real data; on failure emit the required error message.
    try:
        _ = _load_crafterbench(num=args.num)
    except Exception:
        # Propagate a clear, user‑visible error as required by the verification spec.
        sys.stderr.write("verified source unavailable\\n")
        sys.exit(1)

    # If loading succeeded, run the normal curation pipeline.
    curate_failed_figures(num=args.num, output_dir=args.output_dir)

if __name__ == "__main__":
    main()