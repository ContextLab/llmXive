"""
Binary Indicator Transformation Module
-------------------------------------

This module implements the binary indicator transformation required for Task T003.
It provides a `make_binary` function that converts a categorical raster into a binary
indicator map for a specified class ID and a CLI entry point that generates binary
rasters for the forest (class 41) and urban (class 12) classes at all required
resolutions.

The generated files are written to the project ``data/derived`` directory:
    - data/derived/binary_forest_{res}m_co.tif
    - data/derived/binary_urban_{res}m_co.tif

The implementation uses ``rasterio`` for raster I/O and respects the source
nodata value. Output rasters are written with ``uint8`` dtype and nodata
preserved as ``0`` (background) where appropriate.
"""

import logging
from pathlib import Path
from typing import Union

import numpy as np
import rasterio
from rasterio.enums import Resampling

from llmxive_toolkit import paths, get_logger

# Initialize logger
log = get_logger(__name__)

def make_binary(
    raster_path: Union[str, Path],
    class_id: int,
    output_path: Union[str, Path],
) -> Path:
    """
    Transform a categorical raster into a binary indicator map.

    Parameters
    ----------
    raster_path : Union[str, Path]
        Path to the input categorical raster (e.g., NLCD 30 m raster).
    class_id : int
        The land‑cover class identifier that should be mapped to ``1``.
    output_path : Union[str, Path]
        Destination path for the binary raster. The parent directory will be
        created automatically via ``llmxive_toolkit.paths``.

    Returns
    -------
    Path
        Path to the written binary raster file.

    Notes
    -----
    * Pixels equal to ``class_id`` become ``1``.
    * All other valid pixels become ``0``.
    * Pixels that are ``nodata`` in the source retain ``nodata`` in the
      output (encoded as ``0`` for ``uint8`` rasters).
    * The output raster keeps the same CRS, transform, and resolution as the
      source raster.
    """
    raster_path = Path(raster_path)
    output_path = Path(output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Creating binary indicator for class %s from %s", class_id, raster_path)

    with rasterio.open(raster_path) as src:
        profile = src.profile.copy()
        # Force output dtype to uint8
        profile.update(dtype=rasterio.uint8, count=1, compress='deflate')

        # Preserve nodata handling: if source has nodata, keep it; otherwise set to 0
        src_nodata = src.nodata
        if src_nodata is None:
            # No nodata in source – we will use 0 as background in the binary raster
            output_nodata = 0
        else:
            # Preserve the original nodata value (converted to uint8 if possible)
            output_nodata = int(src_nodata) if isinstance(src_nodata, (int, np.integer)) else 0
        profile.update(nodata=output_nodata)

        # Read the full array (the rasters are expected to be manageable after resampling)
        data = src.read(1, masked=False)

        # Build binary mask
        binary = np.where(data == class_id, 1, 0).astype(rasterio.uint8)

        # Apply nodata mask if source had nodata
        if src_nodata is not None:
            nodata_mask = data == src_nodata
            binary = np.where(nodata_mask, output_nodata, binary)

        # Write the binary raster
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(binary, 1)

    log.info("Binary raster written to %s", output_path)
    return output_path

def _generate_all_binaries() -> None:
    """
    Generate binary rasters for the forest (class 41) and urban (class 12)
    classes at each resolution defined in the pipeline.

    Expected input rasters are located in ``data/derived`` with the naming
    pattern ``nlcd_{res}m_co.tif`` where ``res`` is one of
    ``[30, 60, 120, 240, 480]``.
    """
    resolutions = [30, 60, 120, 240, 480]
    class_map = {
        "forest": 41,  # NLCD class ID for forest
        "urban": 12,   # NLCD class ID for developed/urban
    }

    for res in resolutions:
        input_raster = paths.data("derived", f"nlcd_{res}m_co.tif")
        if not input_raster.is_file():
            log.warning(
                "Source raster %s does not exist – skipping binary generation for %dm.",
                input_raster,
                res,
            )
            continue

        for name, class_id in class_map.items():
            output_raster = paths.data(
                "derived", f"binary_{name}_{res}m_co.tif"
            )
            make_binary(input_raster, class_id, output_raster)

def main() -> None:
    """
    CLI entry point.

    Running this module as a script will generate all required binary
    indicator rasters.
    """
    _generate_all_binaries()
    log.info("All binary indicator rasters have been generated.")

if __name__ == "__main__":
    main()
