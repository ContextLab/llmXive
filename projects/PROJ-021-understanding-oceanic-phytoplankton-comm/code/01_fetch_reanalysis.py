"""
Fetch NOAA/Copernicus CMEMS reanalysis data (temperature, salinity, nutrients)
and verify required variables are present while ensuring chlorophyll is absent.

Dataset ID: cmems-global-analysis-forecast-phys-001-004
Output: data/raw/copernicus_global_reanalysis.nc
"""
import sys
import logging
from pathlib import Path
from typing import List

import xarray as xr

# The copernicusmarine package provides a convenient download API.
# It is listed in requirements.txt and will be installed in the environment.
try:
    from copernicusmarine import download
except ImportError as e:
    raise ImportError(
        "The 'copernicusmarine' package is required to fetch CMEMS data. "
        "Install it via pip (see requirements.txt)."
    ) from e

# Project‑relative utilities
from utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
DATASET_ID = "cmems-global-analysis-forecast-phys-001-004"
# Variables we expect from the CMEMS product:
#   thetao – in‑situ temperature (°C)
#   so     – practical salinity (psu)
#   nitrate (or no3) – nutrient concentration (mmol m‑3)
REQUIRED_VARS = {"thetao", "so"}
# Nutrient variable names that are commonly used in this product.
NUTRIENT_VARS = {"no3", "nitrate", "nutrients"}

# We deliberately avoid any chlorophyll variable (e.g., 'chl', 'chl_a')
PROHIBITED_VARS = {"chl", "chl_a", "chlorophyll"}

# Minimal temporal window – a single month is sufficient to obtain all variables
# while keeping the download size modest for CI runners.
START_TIME = "2020-01-01"
END_TIME = "2020-01-31"

# Output location (must match the path declared in the task description)
OUTPUT_PATH = Path("data/raw/copernicus_global_reanalysis.nc")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _select_nutrient_var(available: set) -> str:
    """
    Choose a nutrient variable from the intersection of AVAILABLE and the known
    nutrient names. Raises if none are found.
    """
    intersect = available & NUTRIENT_VARS
    if not intersect:
        raise RuntimeError(
            f"No recognized nutrient variable found in the dataset. "
            f"Available variables: {sorted(available)}"
        )
    # Prefer 'nitrate' over 'no3' if both exist
    for pref in ["nitrate", "no3", "nutrients"]:
        if pref in intersect:
            return pref
    # Fallback – return an arbitrary element
    return next(iter(intersect))

def _verify_dataset(ds: xr.Dataset) -> None:
    """
    Validate that the dataset contains the required variables and does NOT contain
    any prohibited chlorophyll variable. Raises RuntimeError with a clear message
    on failure.
    """
    present_vars = set(ds.data_vars.keys())
    logger.debug(f"Variables present in the downloaded file: {sorted(present_vars)}")

    # Check required temperature and salinity
    missing_req = REQUIRED_VARS - present_vars
    if missing_req:
        raise RuntimeError(
            f"Missing required variable(s) {sorted(missing_req)} in the reanalysis file."
        )

    # Check for at least one nutrient variable
    if not present_vars & NUTRIENT_VARS:
        raise RuntimeError(
            f"No nutrient variable (expected one of {sorted(NUTRIENT_VARS)}) found "
            f"in the reanalysis file."
        )

    # Ensure no chlorophyll variable is present
    prohibited_present = present_vars & PROHIBITED_VARS
    if prohibited_present:
        raise RuntimeError(
            f"Prohibited chlorophyll variable(s) {sorted(prohibited_present)} detected "
            f"in the reanalysis file. Multi‑Modal Independence violated."
        )

    logger.info("Dataset verification passed: required variables present, chlorophyll absent.")

# ----------------------------------------------------------------------
# Main download routine
# ----------------------------------------------------------------------
def fetch_reanalysis_data(
    output_path: Path = OUTPUT_PATH,
    start_time: str = START_TIME,
    end_time: str = END_TIME,
    variables: List[str] = None,
) -> Path:
    """
    Download the CMEMS reanalysis product, write it to OUTPUT_PATH, and verify its
    contents. Returns the path to the written NetCDF file.

    Parameters
    ----------
    output_path: Path
        Destination file (must end with .nc). Parent directories are created if needed.
    start_time, end_time: str
        ISO‑8601 dates delimiting the temporal subset to download.
    variables: List[str] | None
        If supplied, these variable names are requested from the service. If None,
        a minimal set (temperature, salinity, a nutrient) is constructed automatically.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Determine which variables to request.
    # ------------------------------------------------------------------
    if variables is None:
        # We request temperature and salinity explicitly; the nutrient will be
        # selected after we inspect the product’s variable catalogue.
        base_vars = ["thetao", "so"]
    else:
        base_vars = variables

    # ------------------------------------------------------------------
    # Perform the download via copernicusmarine.
    # ------------------------------------------------------------------
    logger.info(
        f"Starting CMEMS download: dataset={DATASET_ID}, "
        f"time={start_time}/{end_time}, vars={base_vars}"
    )
    try:
        download(
            dataset_id=DATASET_ID,
            variables=base_vars,
            start_time=start_time,
            end_time=end_time,
            output_path=str(output_path),
            force=True,   # Overwrite if a stale file exists
        )
    except Exception as e:
        logger.error(f"CMEMS download failed: {e}")
        raise RuntimeError("Failed to download CMEMS reanalysis data.") from e

    logger.info(f"Download completed. File saved to {output_path}")

    # ------------------------------------------------------------------
    # Open the file and verify required content.
    # ------------------------------------------------------------------
    try:
        ds = xr.open_dataset(output_path)
    except Exception as e:
        logger.error(f"Unable to open the downloaded NetCDF file: {e}")
        raise RuntimeError("Downloaded file is not a valid NetCDF dataset.") from e

    # Verify presence of required variables and absence of chlorophyll.
    _verify_dataset(ds)

    # If a nutrient variable was not part of the initial request we
    # re‑download it now (the product allows variable‑wise sub‑setting).
    if not (present_nutrient := ds.data_vars.keys() & NUTRIENT_VARS):
        # Need to fetch a nutrient variable separately.
        nutrient_var = _select_nutrient_var(ds.data_vars.keys())
        logger.info(f"Re‑downloading to include nutrient variable '{nutrient_var}'.")
        # Re‑download including the nutrient variable.
        download(
            dataset_id=DATASET_ID,
            variables=base_vars + [nutrient_var],
            start_time=start_time,
            end_time=end_time,
            output_path=str(output_path),
            force=True,
        )
        ds = xr.open_dataset(output_path)  # Reload after second download

    # Final verification after possible second download
    _verify_dataset(ds)

    logger.info("Reanalysis data successfully fetched and verified.")
    return output_path

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI entry point used by the quickstart / pipeline. It performs the download
    and verification, exiting with a non‑zero status code on any failure.
    """
    setup_logging()
    try:
        fetch_reanalysis_data()
    except Exception as exc:
        logger.error(f"Fatal error during reanalysis fetch: {exc}")
        # Propagate the error to cause a non‑zero exit code.
        sys.exit(1)

if __name__ == "__main__":
    main()