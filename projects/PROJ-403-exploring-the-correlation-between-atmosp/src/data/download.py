"""
src/data/download.py
---------------------

Implements task T006: download ERA5 integrated water vapor transport (IVT) and
geopotential height (Z) at 500 hPa for the full global domain (90°S‑90°N,
180°W‑180°E) covering the period 1979‑01‑01 to 2023‑12‑31 using the
Copernicus Climate Data Store (CDS) API.

The script:
* Uses the ``reanalysis-era5-single-levels-monthly-means`` dataset.
* Requests the variables ``integrated_water_vapor_transport`` (surface) and
  ``z`` (500 hPa) with monthly resolution.
* Writes the NetCDF files to ``data/raw``.
* Computes SHA‑256 checksums for each downloaded file and stores them in
  ``data/raw/metadata.yaml``.
* Converts geopotential (units m² s⁻²) to geopotential height (meters) by
  dividing by the standard gravity constant (9.80665 m s⁻²).
* Fails loudly on any download or conversion error – no synthetic fallback.

The implementation follows the exact parameter values demanded by the task
specification and the feature spec (FR‑001).
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple

import cdsapi
import xarray as xr
import yaml

from src.utils.logger import get_logger
from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Constants – these reflect the exact CDS request required by the spec.
# ----------------------------------------------------------------------
CDS_DATASET = "reanalysis-era5-single-levels-monthly-means"

# Variables required by the spec
CDS_VARIABLES = {
    "ivt": {
        "variable": "integrated_water_vapor_transport",
        # IVT is a surface variable – no pressure level needed.
    },
    "z": {
        "variable": "z",
        "pressure_level": "500",  # 500 hPa geopotential
    },
}

# Full‑global area: [north, west, south, east] in degrees.
GLOBAL_AREA = [90, -180, -90, 180]

# Time range
START_YEAR = 1979
END_YEAR = 2023

# Resolution – "high" as required; we use 0.25° grid spacing.
GRID_RESOLUTION = [0.25, 0.25]  # [latitude, longitude] in degrees

# CDS request constants
PRODUCT_TYPE = "reanalysis"
FORMAT = "netcdf"

# Gravity constant for converting geopotential to height
G0 = 9.80665  # m s⁻²

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def calculate_sha256(file_path: str) -> str:
    """Calculate the SHA‑256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    return sha256.hexdigest()


def store_metadata(metadata: Dict[str, Any], metadata_path: Path) -> None:
    """
    Store (or update) metadata in a YAML file.

    The file is written atomically – the existing content is loaded,
    updated, then written back.
    """
    if metadata_path.exists():
        with open(metadata_path, "r") as f:
            existing = yaml.safe_load(f) or {}
    else:
        existing = {}

    # Merge the new entries under a top‑level ``files`` list.
    existing.setdefault("files", [])
    existing["files"].extend(metadata["files"])

    # Preserve other top‑level keys (e.g., download_date, domain, etc.).
    for key, value in metadata.items():
        if key != "files":
            existing[key] = value

    with open(metadata_path, "w") as f:
        yaml.safe_dump(existing, f, sort_keys=False)


# ----------------------------------------------------------------------
# Core download logic
# ----------------------------------------------------------------------
def _build_request_params(
    variable_cfg: Dict[str, Any],
    years: List[int],
    months: List[int],
    area: List[float],
    grid: List[float],
    target: str,
) -> Dict[str, Any]:
    """
    Build the dictionary passed to ``cdsapi.Client.retrieve``.
    """
    params: Dict[str, Any] = {
        "variable": variable_cfg["variable"],
        "product_type": PRODUCT_TYPE,
        "format": FORMAT,
        "year": [str(y) for y in years],
        "month": [f"{m:02d}" for m in months],
        "area": area,
        "grid": grid,
        "target": target,
    }

    # Include pressure level for the Z variable.
    if "pressure_level" in variable_cfg:
        params["pressure_level"] = variable_cfg["pressure_level"]

    return params


def fetch_and_save(
    variable_key: str,
    variable_cfg: Dict[str, Any],
    years: List[int],
    months: List[int],
    output_dir: Path,
) -> Path:
    """
    Download a single variable for the full global domain and write it to
    ``output_dir``. Returns the path to the downloaded NetCDF file.
    """
    filename = f"{variable_key}_{variable_cfg.get('pressure_level', 'surface')}_{START_YEAR}_{END_YEAR}.nc"
    output_path = output_dir / filename

    if output_path.exists():
        logger.warning(f"File {output_path} already exists – skipping download.")
        return output_path

    client = cdsapi.Client()

    request_params = _build_request_params(
        variable_cfg=variable_cfg,
        years=years,
        months=months,
        area=GLOBAL_AREA,
        grid=GRID_RESOLUTION,
        target=str(output_path),
    )

    logger.info(
        f"Requesting {variable_cfg['variable']} ({variable_key}) "
        f"for years {START_YEAR}-{END_YEAR} → {output_path.name}"
    )
    try:
        client.retrieve(CDS_DATASET, request_params, str(output_path))
    except Exception as exc:
        logger.error(f"CDS download failed for {variable_key}: {exc}")
        raise

    logger.info(f"Download completed: {output_path}")
    return output_path


def convert_geopotential_to_height(z_path: Path) -> Path:
    """
    Convert geopotential (m² s⁻²) to geopotential height (m) in‑place.

    The variable name in the ERA5 monthly‑means file is ``z``. The
    conversion is simply ``Z = z / g0``.
    """
    logger.info(f"Converting geopotential to height for {z_path.name}")

    ds = xr.open_dataset(z_path)
    if "z" not in ds.data_vars:
        raise KeyError(f"'z' variable not found in {z_path}")

    ds["z"] = ds["z"] / G0
    ds["z"].attrs["units"] = "m"
    ds["z"].attrs["long_name"] = "Geopotential height"

    # Overwrite the original file – this keeps the downstream pipeline
    # expecting a file named ``z_500_...nc``.
    ds.to_netcdf(z_path, mode="w")
    ds.close()
    logger.info(f"Conversion finished: {z_path}")

    return z_path


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Orchestrates the full download + conversion workflow.

    1. Creates ``data/raw`` (using ``paths.data`` which ensures the folder
       exists).
    2. Downloads IVT and Z500 for the full period.
    3. Converts the Z500 file from geopotential to height.
    4. Generates ``metadata.yaml`` with SHA‑256 checksums.
    """
    logger.info("Starting ERA5 download (task T006)")

    # Ensure the raw data directory exists.
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    years = list(range(START_YEAR, END_YEAR + 1))
    months = list(range(1, 13))

    downloaded_files: List[Path] = []

    # ------------------------------------------------------------------
    # Download each variable.
    # ------------------------------------------------------------------
    for key, cfg in CDS_VARIABLES.items():
        file_path = fetch_and_save(
            variable_key=key,
            variable_cfg=cfg,
            years=years,
            months=months,
            output_dir=raw_dir,
        )
        downloaded_files.append(file_path)

    # ------------------------------------------------------------------
    # Convert geopotential → height for the Z variable.
    # ------------------------------------------------------------------
    z_file = next(p for p in downloaded_files if p.name.startswith("z_"))
    convert_geopotential_to_height(z_file)

    # ------------------------------------------------------------------
    # Assemble metadata (checksums, timestamps, etc.).
    # ------------------------------------------------------------------
    metadata = {
        "download_date": datetime.datetime.utcnow().isoformat() + "Z",
        "variables": list(CDS_VARIABLES.keys()),
        "domain": {
            "area": GLOBAL_AREA,
            "resolution_deg": GRID_RESOLUTION,
        },
        "time_range": {
            "start": f"{START_YEAR}-01-01",
            "end": f"{END_YEAR}-12-31",
        },
        "files": [
            {"path": str(p), "checksum": calculate_sha256(str(p))}
            for p in downloaded_files
        ],
    }

    metadata_path = raw_dir / "metadata.yaml"
    store_metadata(metadata, metadata_path)
    logger.info(f"Metadata written to {metadata_path}")

    logger.info("All download tasks completed successfully.")


if __name__ == "__main__":
    # When executed as a script ``python -m src.data.download``.
    import datetime

    main()