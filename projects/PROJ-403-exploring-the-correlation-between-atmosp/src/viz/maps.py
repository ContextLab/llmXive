"""
src/viz/maps.py
----------------

Visualization utilities for the Atmospheric River – Z500 correlation project.

This module provides a single public function ``generate_correlation_map`` that
reads a NetCDF file produced by the analysis phase (``corr_fdr_{band}_{season}.nc``),
masks out grid cells whose Benjamini‑Hochberg adjusted p‑value exceeds the
significance threshold (default 0.05), and writes a PNG map to the ``figures/``
folder.

The implementation uses the project's ``llmxive_toolkit.paths`` helpers to
construct input and output paths, ensuring that the function works with the
standard project layout without the caller having to specify absolute paths.

**Enhancements for T028**
* Adds a colour‑bar legend with a clear label.
* Adds comprehensive metadata (title) to the saved PNG file.
* Uses a top‑level figure title that includes band and season information.

**Enhancements for T029**
* After the PNG is written, the file is renamed to include a SHA‑256 content
  hash suffix, following the pattern::
  
      corr_map_{band}_{season}_{hash}.png

  This guarantees content‑addressable filenames and enables downstream
  reproducibility checks.  The function returns the final ``Path`` object
  pointing at the hashed file.
"""

from pathlib import Path
from typing import Optional
import hashlib

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# Project‑wide path helpers (already provided by the platform)
from llmxive_toolkit import paths

__all__ = ["generate_correlation_map"]

def _apply_significance_mask(
    corr: xr.DataArray, pval: xr.DataArray, alpha: float = 0.05
) -> xr.DataArray:
    """
    Return a copy of ``corr`` where cells with ``pval`` > ``alpha`` are set
    to ``np.nan`` (transparent in the final plot).

    Parameters
    ----------
    corr : xr.DataArray
        Correlation coefficients.
    pval : xr.DataArray
        Adjusted p‑values (same shape as ``corr``).
    alpha : float, optional
        Significance threshold (default 0.05).

    Returns
    -------
    xr.DataArray
        Masked correlation array.
    """
    # ``pval <= alpha`` is the mask of significant cells.
    mask = pval <= alpha
    return corr.where(mask, other=np.nan)

def _compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 hash of the given file.

    Parameters
    ----------
    file_path : Path
        Path to the file whose hash should be calculated.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    sha256 = hashlib.sha256()
    # Read in chunks to avoid loading huge files into memory.
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def generate_correlation_map(
    band: str,
    season: str,
    *,
    input_path: Optional[Path | str] = None,
    output_path: Optional[Path | str] = None,
    alpha: float = 0.05,
    cmap: str = "RdBu_r",
) -> Path:
    """
    Create a PNG map visualising significant Pearson correlation
    coefficients for a given latitude ``band`` and ``season``.

    The function reads a NetCDF file that must contain two variables:
    ``correlation`` (the Pearson r values) and ``adjusted_p`` (the
    Benjamini‑Hochberg adjusted p‑values).  Cells whose adjusted p‑value
    exceeds ``alpha`` are masked (set to ``NaN``) so they appear
    transparent in the final figure.

    Parameters
    ----------
    band : str
        Latitude band identifier (e.g., ``"30-40N"``). Used for the
        default file name and plot title.
    season : str
        Seasonal identifier (e.g., ``"DJF"``). Used for the default file
        name and plot title.
    input_path : Path or str, optional
        Path to the NetCDF file. If omitted, the function looks for
        ``data/processed/corr_fdr_{band}_{season}.nc`` using the ``paths``
        helper.
    output_path : Path or str, optional
        Destination for the PNG file *before* hashing. If omitted, the
        function writes to ``figures/corr_map_{band}_{season}.png`` using
        the ``paths`` helper.
    alpha : float, optional
        Significance threshold (default 0.05).
    cmap : str, optional
        Matplotlib colormap (default ``"RdBu_r"``).

    Returns
    -------
    pathlib.Path
        Path to the written PNG file **with the SHA‑256 hash suffix**.
    """
    # Resolve input path – default location under data/processed
    if input_path is None:
        input_path = paths.data("processed", f"corr_fdr_{band}_{season}.nc")
    else:
        input_path = Path(input_path)

    if not input_path.is_file():
        raise FileNotFoundError(
            f"Correlation NetCDF file not found: {input_path}"
        )

    # Resolve output path – default location under figures/
    # This is the *temporary* path; after writing we will rename it to
    # include the content hash.
    if output_path is None:
        temp_output_path = paths.figures(f"corr_map_{band}_{season}.png")
    else:
        temp_output_path = Path(output_path)

    # Ensure the output directory exists (paths helper creates it)
    temp_output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load the dataset (lazy via dask; for small test files it will be eager)
    ds = xr.open_dataset(input_path)

    if "correlation" not in ds or "adjusted_p" not in ds:
        raise ValueError(
            f"The dataset at {input_path} must contain variables "
            "'correlation' and 'adjusted_p'."
        )

    corr = ds["correlation"]
    pval = ds["adjusted_p"]

    # Apply significance mask
    masked_corr = _apply_significance_mask(corr, pval, alpha=alpha)

    # Prepare the figure
    plt.figure(figsize=(8, 4))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.coastlines(resolution="110m")
    ax.add_feature(cfeature.BORDERS, linewidth=0.5)

    # Determine latitude/longitude coordinate names (common conventions)
    lat_name = "lat" if "lat" in masked_corr.dims else "latitude"
    lon_name = "lon" if "lon" in masked_corr.dims else "longitude"

    lats = masked_corr[lat_name]
    lons = masked_corr[lon_name]

    # Plot using pcolormesh; masked values become transparent
    mesh = ax.pcolormesh(
        lons,
        lats,
        masked_corr,
        cmap=cmap,
        transform=ccrs.PlateCarree(),
        shading="auto",
        vmin=-1,
        vmax=1,
    )

    # Colour bar (legend)
    cbar = plt.colorbar(mesh, orientation="horizontal", pad=0.05, shrink=0.8)
    cbar.set_label("Pearson correlation coefficient")

    # Title – includes band and season for clear metadata
    ax.set_title(f"Significant AR–Z500 Correlation\\nBand: {band}, Season: {season}")

    # Save figure with a transparent background so ocean/gap areas are transparent
    # Include PNG metadata that records the band and season – useful for downstream tools.
    metadata = {
        "Title": f"AR–Z500 correlation map (Band: {band}, Season: {season})",
        "Band": band,
        "Season": season,
    }
    plt.savefig(
        temp_output_path,
        dpi=150,
        bbox_inches="tight",
        transparent=True,
        metadata=metadata,
    )
    plt.close()

    # -----------------------------------------------------------------
    # T029 – Append SHA‑256 hash to the filename.
    # -----------------------------------------------------------------
    file_hash = _compute_sha256(temp_output_path)
    # Build the final filename with hash suffix
    final_name = f"corr_map_{band}_{season}_{file_hash}.png"
    final_path = temp_output_path.parent / final_name

    # Rename (move) the temporary file to the final hashed name.
    temp_output_path.replace(final_path)

    # Return the path to the hashed file so callers can record it if needed.
    return final_path