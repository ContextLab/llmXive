import argparse
import json
import logging
import os
import random
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

from config import get_project_root, get_stimuli_dir, get_data_dir
from utils.logging import get_logger
from data.checksum import compute_file_checksum, save_checksum_manifest, verify_checksum

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions (existing from previous version)
# ----------------------------------------------------------------------
def fetch_real_dataset_image(
    source: str = "visual_genome",
    limit: int = 30,
    output_dir: Optional[str] = None,
    streaming: bool = True
) -> List[str]:
    """
    Fetch a sample of images from a real dataset (Visual Genome).

    Args:
        source: Dataset source identifier.
        limit: Number of images to fetch.
        output_dir: Directory to save images.
        streaming: Whether to stream the dataset.

    Returns:
        List of paths to downloaded images.
    """
    try:
        from datasets import load_dataset
        from PIL import Image
        import io
    except ImportError:
        logger.error("datasets or PIL not installed. Please install them.")
        raise ImportError("datasets and PIL are required for data fetching.")

    if output_dir is None:
        output_dir = get_stimuli_dir() / "raw_subset"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Fetching {limit} images from {source}...")

    # Load dataset
    if streaming:
        dataset = load_dataset(source, split="train", streaming=True)
    else:
        dataset = load_dataset(source, split="train")

    image_paths = []
    count = 0

    for item in dataset:
        if count >= limit:
            break

        # Visual Genome image structure varies; handle common cases
        img = None
        if 'image' in item:
            img = item['image']
        elif 'image_url' in item:
            # Download from URL
            import urllib.request
            try:
                with urllib.request.urlopen(item['image_url']) as response:
                    img = Image.open(io.BytesIO(response.read()))
            except Exception as e:
                logger.warning(f"Failed to download image {item.get('id', 'unknown')}: {e}")
                continue
        else:
            # Try to find image in nested structure
            for key, value in item.items():
                if isinstance(value, Image.Image):
                    img = value
                    break

        if img is None:
            continue

        # Save image
        img_id = item.get('id', count)
        img_path = output_dir / f"vg_{img_id}.png"

        # Avoid overwriting
        if img_path.exists():
            continue

        try:
            img.save(img_path, format='PNG')
            image_paths.append(str(img_path))
            count += 1
            logger.debug(f"Fetched image {count}: {img_path}")
        except Exception as e:
            logger.warning(f"Failed to save image {img_id}: {e}")

    logger.info(f"Fetched {len(image_paths)} images.")

    # Generate checksum manifest
    manifest_path = output_dir / "manifest.sha256"
    save_checksum_manifest(image_paths, manifest_path)

    return image_paths

def calculate_complexity_score(
    image_path: str
) -> float:
    """
    Calculate a baseline complexity score for an image.

    Uses pixel variance as a simple proxy for visual complexity.

    Args:
        image_path: Path to the image.

    Returns:
        Complexity score (0.0 to 1.0).
    """
    try:
        from PIL import Image
    except ImportError:
        logger.error("PIL not installed.")
        raise ImportError("PIL is required for complexity calculation.")

    img = Image.open(image_path)
    width, height = img.size
    area = width * height

    # Convert to grayscale and compute variance of pixel values
    gray = img.convert('L')
    pixels = np.array(gray).astype(np.float32).flatten()
    variance = np.var(pixels)

    # Normalise variance to [0,1] (max variance for 8‑bit grayscale is (255^2)/4)
    max_variance = (255 ** 2) / 4
    complexity = float(min(1.0, variance / max_variance))

    return complexity

def load_image_metadata(
    image_path: str
) -> Dict[str, Any]:
    """
    Load metadata for an image, including its complexity score.

    Args:
        image_path: Path to the image.

    Returns:
        Metadata dictionary.
    """
    try:
        from PIL import Image
    except ImportError:
        logger.error("PIL not installed.")
        raise ImportError("PIL is required for metadata loading.")

    img = Image.open(image_path)
    width, height = img.size

    return {
        "path": image_path,
        "width": width,
        "height": height,
        "format": img.format,
        "mode": img.mode,
        "complexity_score": calculate_complexity_score(image_path)
    }

# ----------------------------------------------------------------------
# New functionality for T001
# ----------------------------------------------------------------------
def _gather_prebundled_images() -> List[Path]:
    """
    Return a list of image file paths that exist in the pre‑bundled
    ``data/stimuli/raw_subset`` directory.
    """
    raw_dir = get_stimuli_dir() / "raw_subset"
    if not raw_dir.exists():
        logger.warning(f"Pre‑bundled directory not found: {raw_dir}")
        # If missing, fetch a small default sample (e.g., 10 images) from Visual Genome
        logger.info("Fetching a default pre‑bundled sample from Visual Genome...")
        fetched = fetch_real_dataset_image(
            source="visual_genome",
            limit=10,
            output_dir=str(raw_dir),
            streaming=True
        )
        if not fetched:
            raise FileNotFoundError(f"Unable to obtain any images for pre‑bundled set at {raw_dir}")
    image_paths = sorted([p for p in raw_dir.iterdir()
                          if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}])
    if not image_paths:
        raise FileNotFoundError(f"No image files found in {raw_dir}")
    logger.info(f"Found {len(image_paths)} pre‑bundled images.")
    return image_paths

def _compute_complexities(image_paths: List[Path]) -> List[Dict[str, Any]]:
    """
    Compute complexity metadata for each image path.

    Returns a list of dictionaries with at least ``path`` and
    ``complexity_score`` keys.
    """
    metadata_list = []
    for p in image_paths:
        try:
            meta = load_image_metadata(str(p))
            metadata_list.append(meta)
        except Exception as e:
            logger.warning(f"Failed to process {p}: {e}")
    return metadata_list

def _calculate_quantile_stats(metadata: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute Q1, Q2, Q3 and spread of the ``complexity_score`` values.
    """
    scores = np.array([m["complexity_score"] for m in metadata])
    q1, q2, q3 = np.quantile(scores, [0.25, 0.5, 0.75])
    spread = float(q3 - q1)
    return {"Q1": float(q1), "Q2": float(q2), "Q3": float(q3), "spread": spread}

def _select_representative_sample(
    metadata: List[Dict[str, Any]],
    count: int,
    rng: random.Random
) -> List[Dict[str, Any]]:
    """
    Select ``count`` images that span the complexity distribution.
    The simple strategy is to sort by complexity and then pick
    evenly‑spaced indices.
    """
    if count <= 0:
        raise ValueError("count must be a positive integer")

    sorted_meta = sorted(metadata, key=lambda m: m["complexity_score"])
    total = len(sorted_meta)
    if count > total:
        logger.warning(f"Requested {count} images but only {total} available; using all.")
        return sorted_meta

    # Evenly spaced selection
    indices = [int(round(i * (total - 1) / (count - 1))) for i in range(count)]
    selected = [sorted_meta[i] for i in indices]
    return selected

def _write_complexity_stats(stats: Dict[str, float], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Complexity statistics written to {out_path}")

def _write_variable_fit_check(selected: List[Dict[str, Any]], out_path: Path) -> None:
    """
    Verify that each selected image metadata contains the required fields.
    """
    required = {"complexity_score"}
    missing_entries = []
    for meta in selected:
        missing = required - meta.keys()
        if missing:
            missing_entries.append((meta.get("path", "<unknown>"), missing))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        if not missing_entries:
            f.write("All required variables present.\n")
            logger.info("Variable fit check passed.")
        else:
            f.write("Missing variables detected:\n")
            for path, miss in missing_entries:
                f.write(f"{path}: {', '.join(miss)}\n")
            logger.error("Variable fit check failed.")
    # No return value needed

def _write_selection_marker(marker_path: Path) -> None:
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.touch()
    logger.info(f"Selection marker created at {marker_path}")

def _parse_int_arg(value: str, default: int) -> int:
    """
    Helper to convert an argument that may be a placeholder like '<sample_size>'
    into an integer. Returns ``default`` if conversion fails.
    """
    try:
        return int(value)
    except ValueError:
        logger.warning(f"Argument '{value}' is not a valid integer; using default {default}.")
        return default

def main():
    """CLI entry point for data loading and selection (Task T001)."""
    parser = argparse.ArgumentParser(description="Load and process stimulus images")
    parser.add_argument('--source', type=str, default="visual_genome",
                        help='Dataset source ("visual_genome" or "prebundled")')
    # Accept string to allow placeholders like '<sample_size>'
    parser.add_argument('--count', type=str, default="30",
                        help='Number of images to select for the study')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducible selection')
    parser.add_argument('--output', type=str,
                        help='Output directory for fetched images (used only for visual_genome)')
    parser.add_argument('--validate', action='store_true',
                        help='Validate an existing bundle instead of selecting')
    parser.add_argument('--complexity-min', type=float, default=0.0,
                        help='Minimum complexity score (unused in current T001 implementation)')
    parser.add_argument('--complexity-max', type=float, default=1.0,
                        help='Maximum complexity score (unused in current T001 implementation)')
    # Additional flags to support the quickstart's visual_genome command
    parser.add_argument('--limit', type=str,
                        help='Upper limit on number of images to fetch (alternative to --count)')
    parser.add_argument('--stream', action='store_true',
                        help='Stream the dataset instead of downloading all at once')

    args = parser.parse_args()

    rng = random.Random(args.seed)

    if args.validate:
        # Existing validation path (unchanged from original script)
        bundle_dir = args.output or get_stimuli_dir() / "raw_subset"
        success = validate_data_bundle(str(bundle_dir))
        sys.exit(0 if success else 1)

    # ------------------------------------------------------------------
    # Load images according to source
    # ------------------------------------------------------------------
    if args.source == "prebundled":
        image_paths = _gather_prebundled_images()
    elif args.source == "visual_genome":
        # Determine how many images to fetch
        count_val = args.limit if args.limit is not None else args.count
        limit_int = _parse_int_arg(count_val, default=30)
        image_paths = fetch_real_dataset_image(
            source="visual_genome",
            limit=limit_int,
            output_dir=args.output,
            streaming=args.stream
        )
    else:
        logger.error(f"Unknown source '{args.source}'. Use 'prebundled' or 'visual_genome'.")
        sys.exit(1)

    if not image_paths:
        logger.error("No images available for processing.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Compute complexity scores for all available images
    # ------------------------------------------------------------------
    metadata = _compute_complexities(image_paths)

    # ------------------------------------------------------------------
    # Compute quantile statistics and verify spread requirement (≥0.3)
    # ------------------------------------------------------------------
    stats = _calculate_quantile_stats(metadata)
    if stats["spread"] < 0.3:
        logger.error(f"Complexity spread {stats['spread']:.3f} is below the required 0.3.")
        sys.exit(1)

    # Write complexity statistics
    stats_path = get_project_root() / "data" / "processed" / "complexity_stats.json"
    _write_complexity_stats(stats, stats_path)

    # ------------------------------------------------------------------
    # Select a representative sample respecting the requested count
    # ------------------------------------------------------------------
    count_int = _parse_int_arg(args.count, default=30)
    selected = _select_representative_sample(metadata, count_int, rng)

    # Write variable‑fit check
    var_check_path = get_project_root() / "data" / "processed" / "variable_fit_check.txt"
    _write_variable_fit_check(selected, var_check_path)

    # Create selection‑complete marker
    marker_path = get_stimuli_dir() / "selection_complete.txt"
    _write_selection_marker(marker_path)

    # (Optional) write a manifest of the selected images – helpful for downstream steps
    selected_manifest = get_stimuli_dir() / "selected_images.json"
    selected_manifest.parent.mkdir(parents=True, exist_ok=True)
    with selected_manifest.open("w") as f:
        json.dump([m["path"] for m in selected], f, indent=2)
    logger.info(f"Selected image list written to {selected_manifest}")

    logger.info("Data loading and selection completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())