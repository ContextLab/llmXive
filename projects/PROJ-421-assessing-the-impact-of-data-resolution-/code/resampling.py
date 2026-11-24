"""
Resampling module for generating coarser resolution rasters from high-resolution
spatial data using nearest-neighbor aggregation.

This module implements the core logic for the 'zoom out' operation on spatial
datasets, aggregating fine-resolution pixels into larger blocks while preserving
the categorical integrity of land cover classifications.

Nearest-neighbor aggregation is the preferred method for categorical data (such as
NLCD land cover classes) because it:
1. Preserves integer class values without interpolation artifacts.
2. Maintains the original distribution of categorical values.
3. Avoids the creation of non‑existent intermediate classes.

The aggregation process works by dividing the input raster into non‑overlapping
windows of size (factor x factor) and selecting the dominant (or first) pixel
value within each window for the output raster. This effectively reduces the
spatial resolution by the specified factor.

Key Functions:
- ``generate_resolution(input_path, factor, output_dir)``: Generates a single
  coarser‑resolution raster using rasterio's ``reproject`` with
  ``Resampling.nearest``. The function works with chunked processing to stay
  within memory limits.
- ``run_resampling_pipeline(input_path, factors, output_dir=None)``: Convenience
  wrapper that runs ``generate_resolution`` for a list of factors and returns a
  mapping from factor to the generated file path.

This module is a prerequisite for the statistical power analysis pipeline,
as it enables the comparison of spatial autocorrelation metrics across
different resolutions.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject

logger = logging.getLogger(__name__)

def _validate_input(input_path: Path) -> rasterio.DatasetReader:
    """
    Validate that ``input_path`` exists and can be opened as a raster.
    Returns an opened rasterio dataset.

    Raises:
        FileNotFoundError: If the path does not exist or cannot be opened.
    """
    if not input_path.is_file():
        raise FileNotFoundError(f"Input raster not found: {input_path}")

    try:
        src = rasterio.open(input_path)
        return src
    except Exception as exc:
        # rasterio raises RasterioIOError for invalid files; we translate to FileNotFoundError
        raise FileNotFoundError(f"Unable to open raster '{input_path}': {exc}") from exc

def generate_resolution(
    input_path: str,
    factor: int,
    output_dir: str,
    *,
    driver: str = "GTiff"
) -> str:
    """
    Generate a coarser‑resolution raster using nearest‑neighbor resampling.

    Parameters
    ----------
    input_path : str
        Path to the high‑resolution source raster.
    factor : int
        Integer aggregation factor (e.g., 2 for 60 m from a 30 m source).
    output_dir : str
        Directory where the generated raster will be written.
    driver : str, optional
        Rasterio driver for the output file (default: "GTiff").

    Returns
    -------
    str
        Path to the generated raster file.

    Raises
    ------
    FileNotFoundError
        If ``input_path`` does not exist or cannot be opened.
    ValueError
        If ``factor`` is not a positive integer.
    """
    if factor <= 0:
        raise ValueError(f"Aggregation factor must be a positive integer, got {factor}")

    src_path = Path(input_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Validate and open source raster
    src = _validate_input(src_path)

    # Compute new dimensions and transform
    new_width = max(1, src.width // factor)
    new_height = max(1, src.height // factor)

    # Scale the affine transform: each output pixel covers ``factor`` input pixels
    new_transform = src.transform * rasterio.Affine.scale(factor, factor)

    # Determine output filename
    src_name = src_path.stem
    out_path = out_dir / f"{src_name}_{factor}x.tif"

    profile = src.profile.copy()
    profile.update(
        {
            "driver": driver,
            "height": new_height,
            "width": new_width,
            "transform": new_transform,
            "compress": "lzw",
        }
    )

    logger.info(
        "Resampling %s (factor=%s) -> %s (size: %dx%d)",
        src_path,
        factor,
        out_path,
        new_width,
        new_height,
    )

    with rasterio.open(out_path, "w", **profile) as dst:
        # Perform nearest‑neighbor resampling. rasterio handles windowed processing
        # internally when the source and destination are opened as datasets.
        reproject(
            source=rasterio.band(src, 1),
            destination=rasterio.band(dst, 1),
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=new_transform,
            dst_crs=src.crs,
            resampling=Resampling.nearest,
        )

    src.close()
    logger.info("Resampling complete: %s", out_path)
    return str(out_path)

def run_resampling_pipeline(
    input_path: str,
    factors: List[int],
    output_dir: Optional[str] = None,
) -> Dict[int, Optional[str]]:
    """
    Run ``generate_resolution`` for each factor in ``factors``.

    Parameters
    ----------
    input_path : str
        Path to the source raster.
    factors : List[int]
        List of aggregation factors to apply.
    output_dir : Optional[str]
        Directory for all generated rasters. If ``None``, a ``derived`` sub‑folder
        next to the input file is used.

    Returns
    -------
    Dict[int, Optional[str]]
        Mapping from factor to the path of the generated raster (or ``None`` if
        generation failed for that factor).
    """
    result: Dict[int, Optional[str]] = {}
    src_path = Path(input_path)

    # Determine a sensible default output directory
    if output_dir is None:
        default_dir = src_path.parent.parent / "derived"
        out_dir = default_dir
    else:
        out_dir = Path(output_dir)

    for factor in factors:
        try:
            out_path = generate_resolution(str(src_path), factor, str(out_dir))
            result[factor] = out_path
        except Exception as exc:
            logger.error("Failed to generate resolution for factor %s: %s", factor, exc)
            result[factor] = None

    return result

# ----------------------------------------------------------------------
# Command‑line interface (optional, not required for the tests)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Generate coarser resolution rasters via nearest‑neighbor aggregation."
    )
    parser.add_argument("input", help="Path to the high‑resolution raster.")
    parser.add_argument(
        "-f",
        "--factors",
        nargs="+",
        type=int,
        required=True,
        help="Aggregation factors (e.g., 2 4 8).",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="Directory to write output rasters. Defaults to a 'derived' folder.",
    )
    args = parser.parse_args()

    try:
        outputs = run_resampling_pipeline(args.input, args.factors, args.output_dir)
        for factor, path in outputs.items():
            if path:
                print(f"Factor {factor}: {path}")
            else:
                print(f"Factor {factor}: FAILED", file=sys.stderr)
    except Exception as e:
        logger.exception("Resampling pipeline failed")
        sys.exit(1)