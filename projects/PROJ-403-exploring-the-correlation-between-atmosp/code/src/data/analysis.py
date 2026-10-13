"""
src/data/analysis.py
---------------------

This module provides the core implementation for **Task T019** – computing Pearson
correlation coefficients and associated raw p‑values between Atmospheric River
(AR) frequency and 500 hPa geopotential height anomaly time‑series on a per‑grid‑cell
basis – **Task T020** – applying the Benjamini‑Hochberg False Discovery Rate
(FDR) correction – and **Task T022** – saving the final results (coefficient,
raw p‑value, BH‑FDR‑adjusted p‑value) to a NetCDF file named
``data/processed/corr_fdr_{band}_{season}.nc``.

In addition, this file now implements **Task T023a** – Spatial Validation:
computing spatial correlation coefficients between the significant AR‑Z500
pattern and canonical teleconnection templates (PNA/NAO) from NOAA CPC,
and writing the results to ``data/processed/validation_spatial_{band}_{season}.json``.

**New implementation**: **Task T023b** – Scalar Regression:
regress the AR‑Z500 fields against scalar PNA/NAO index time series from NOAA
CPC and write results to ``data/processed/validation_scalar_{band}_{season}.json``.

The functions are deliberately lightweight and have no external side‑effects
other than writing NetCDF/JSON output files.  They are intended to be called by the
higher‑level CLI orchestrator (`src.cli.run_analysis`) once the AR frequency and
Z500 anomaly datasets have been produced by the preprocessing steps
(`src.data.preprocess`).

The module also implements **Task T032** – regeneration of monthly AR frequency
counts for each AR‑detection threshold variation.  This is provided via the
function :func:`regenerate_ar_frequency_counts` and exposed as the CLI sub‑command
``regenerate_ar_freq``.

The implementation follows **Spec FR‑004** (Pearson correlation) and
**Spec FR‑005** (Benjamini‑Hochberg FDR).  Missing data are excluded from the
correlation computation and the FDR correction is applied across *all* grid
cells within a band‑season, as required by the spec.

Usage examples
--------------

Compute Pearson correlation (Task T019)::

    from src.data.analysis import compute_pearson_correlation
    compute_pearson_correlation(
        ar_freq_path="data/processed/ar_freq_band30-40N.nc",
        z_anom_path="data/processed/z_anom_band30-40N.nc",
        output_path="data/processed/corr_raw_band30-40N.nc",
    )

Apply Benjamini‑Hochberg FDR correction (Task T020)::

    from src.data.analysis import apply_bh_fdr_correction
    apply_bh_fdr_correction(
        raw_corr_path="data/processed/corr_raw_band30-40N.nc",
        output_path="data/processed/corr_fdr_band30-40N.nc",
    )

Run the full pipeline for a specific band and season (Task T022)::

    from src.data.analysis import run_correlation_fdr_pipeline
    run_correlation_fdr_pipeline(
        ar_freq_path="data/processed/ar_freq_30-40N_DJF.nc",
        z_anom_path="data/processed/z_anom_30-40N_DJF.nc",
        band="30-40N",
        season="DJF",
    )

Perform spatial validation (Task T023a)::

    from src.data.analysis import spatial_validation
    spatial_validation(
        corr_path="data/processed/corr_fdr_30-40N_DJF.nc",
        band="30-40N",
        season="DJF",
        output_path="data/processed/validation_spatial_30-40N_DJF.json",
    )

Perform scalar regression validation (Task T023b)::

    from src.data.analysis import scalar_validation
    scalar_validation(
        ar_freq_path="data/processed/ar_freq_30-40N_DJF.nc",
        z_anom_path="data/processed/z_anom_30-40N_DJF.nc",
        band="30-40N",
        season="DJF",
        output_path="data/processed/validation_scalar_30-40N_DJF.json",
    )

Regenerate AR frequency counts for threshold variations (Task T032)::

    from src.data.analysis import regenerate_ar_frequency_counts
    regenerate_ar_frequency_counts(
        ivt_path="data/processed/ivt_monthly.nc",
        band="30-40N",
        thresholds=[240.0, 250.0, 260.0],
        output_dir="data/processed",
    )

The module also provides a small ``__main__`` entry point that can be used for
ad‑hoc testing via ``python -m src.data.analysis <raw_corr_nc> <out_nc>``.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Optional, Tuple, List

import numpy as np
import pandas as pd
import requests
import xarray as xr
from scipy import stats
from statsmodels.stats.multitest import multipletests

from src.utils.logger import get_logger
from llmxive_toolkit import paths

# Import preprocessing utilities for sensitivity analysis
from src.data.preprocess import (
    load_chunked_netcdf,
    detect_ar_events,
    aggregate_monthly_frequency,
    save_processed_dataset,
)

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
log: logging.Logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities (shared between T019 and T020)
# ----------------------------------------------------------------------
def _load_dataset(path: Path, variable: str) -> xr.DataArray:
    """
    Load a NetCDF file and return the requested variable as a DataArray.

    Parameters
    ----------
    path: Path
        Path to the NetCDF file.
    variable: str
        Name of the variable to extract.

    Returns
    -------
    xr.DataArray
        The variable data with dimensions (time, lat, lon).

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    KeyError
        If ``variable`` is not present in the dataset.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")
    ds = xr.open_dataset(path)
    if variable not in ds:
        raise KeyError(f"Variable '{variable}' not found in {path}")
    da = ds[variable]
    # Ensure dimensions are named as expected
    expected_dims = {"time", "lat", "lon"}
    if not expected_dims.issubset(set(da.dims)):
        raise ValueError(
            f"Variable '{variable}' must have dimensions {expected_dims}, got {da.dims}"
        )
    return da

def _align_dataarrays(
    ar: xr.DataArray, z: xr.DataArray
) -> Tuple[xr.DataArray, xr.DataArray]:
    """
    Align two DataArrays on the ``time`` dimension, dropping any time steps that
    are missing from either array. Latitude and longitude coordinates are assumed
    to be identical (they are checked for equality).

    Parameters
    ----------
    ar, z: xr.DataArray
        Input arrays with dimensions (time, lat, lon).

    Returns
    -------
    tuple of aligned DataArrays (ar_aligned, z_aligned).
    """
    # Align on time; join='inner' drops mismatched times
    ar_aligned, z_aligned = xr.align(ar, z, join="inner")
    # Verify spatial coordinates match
    if not np.allclose(ar_aligned["lat"], z_aligned["lat"]) or not np.allclose(
        ar_aligned["lon"], z_aligned["lon"]
    ):
        raise ValueError(
            "Latitude/longitude coordinates do not match between datasets."
        )
    return ar_aligned, z_aligned

def _pearson_per_gridcell(
    ar_vals: np.ndarray, z_vals: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute Pearson correlation coefficient and raw p‑value for each grid cell.

    Parameters
    ----------
    ar_vals, z_vals : np.ndarray
        Arrays of shape (time, nlat, nlon). Missing values should be represented
        as ``np.nan``.

    Returns
    -------
    coeff : np.ndarray
        Correlation coefficients with shape (nlat, nlon).
    pval : np.ndarray
        Corresponding two‑tailed p‑values with shape (nlat, nlon).
    """
    nlat, nlon = ar_vals.shape[1], ar_vals.shape[2]
    coeff = np.full((nlat, nlon), np.nan, dtype=np.float32)
    pval = np.full((nlat, nlon), np.nan, dtype=np.float32)

    for i in range(nlat):
        for j in range(nlon):
            x = ar_vals[:, i, j]
            y = z_vals[:, i, j]
            mask = np.isfinite(x) & np.isfinite(y)
            if mask.sum() < 2:
                # Not enough data to compute a correlation
                continue
            r, p = stats.pearsonr(x[mask], y[mask])
            coeff[i, j] = r
            pval[i, j] = p
    return coeff, pval

# ----------------------------------------------------------------------
# Task T019 – Pearson correlation
# ----------------------------------------------------------------------
def compute_pearson_correlation(
    ar_freq_path: str,
    z_anom_path: str,
    output_path: str,
    ar_variable: str = "ar_frequency",
    z_variable: str = "z_anomaly",
    coeff_name: str = "pearson_r",
    pval_name: str = "p_value",
) -> None:
    """
    Compute Pearson correlation coefficients and raw p‑values between AR
    frequency and Z500 anomalies for every grid cell and write the results to a
    NetCDF file.

    The function follows **Spec FR‑004** exactly:
    * Pearson correlation (not Spearman).
    * No multiple‑testing correction – that is handled by a later task
      (T020).

    Parameters
    ----------
    ar_freq_path : str
        Path to the NetCDF file containing AR frequency counts.
    z_anom_path : str
        Path to the NetCDF file containing Z500 anomalies.
    output_path : str
        Destination NetCDF file that will store two variables:
        ``coeff_name`` (Pearson r) and ``pval_name`` (raw two‑tailed p‑value).
    ar_variable, z_variable : str, optional
        Variable names to read from the respective NetCDF files.
    coeff_name, pval_name : str, optional
        Names for the output variables in the result file.

    Returns
    -------
    None
        The result is written to ``output_path``.  The function raises
        informative exceptions if inputs are invalid.
    """
    log.info("Loading AR frequency dataset from %s", ar_freq_path)
    ar_da = _load_dataset(Path(ar_freq_path), ar_variable)

    log.info("Loading Z500 anomaly dataset from %s", z_anom_path)
    z_da = _load_dataset(Path(z_anom_path), z_variable)

    log.info("Aligning datasets on the time dimension")
    ar_aligned, z_aligned = _align_dataarrays(ar_da, z_da)

    log.info("Converting DataArrays to NumPy for vectorised computation")
    ar_vals = ar_aligned.values.astype(np.float32)
    z_vals = z_aligned.values.astype(np.float32)

    log.info(
        "Computing Pearson correlation per grid cell (time steps = %d)",
        ar_vals.shape[0],
    )
    coeff, pval = _pearson_per_gridcell(ar_vals, z_vals)

    # Build the output Dataset preserving coordinate metadata
    ds_out = xr.Dataset(
        {
            coeff_name: (("lat", "lon"), coeff, {"description": "Pearson correlation coefficient"}),
            pval_name: (("lat", "lon"), pval, {"description": "Two‑tailed p‑value"}),
        },
        coords={
            "lat": ar_aligned["lat"],
            "lon": ar_aligned["lon"],
        },
    )
    ds_out.attrs["source_ar"] = ar_freq_path
    ds_out.attrs["source_z_anom"] = z_anom_path
    ds_out.attrs["method"] = "pearson_correlation"
    ds_out.attrs["generated_by"] = __name__

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log.info("Writing correlation results to %s", out_path)
    ds_out.to_netcdf(out_path, format="NETCDF4")
    log.info("Pearson correlation computation completed successfully.")

# ----------------------------------------------------------------------
# Task T020 – Benjamini‑Hochberg FDR correction
# ----------------------------------------------------------------------
def apply_bh_fdr_correction(
    raw_corr_path: str,
    output_path: str,
    pval_name: str = "p_value",
    adj_pval_name: str = "p_adj_fdr",
    significance_name: str = "significant",
    alpha: float = 0.05,
) -> None:
    """
    Apply the Benjamini‑Hochberg False Discovery Rate (FDR) procedure to the
    raw p‑values produced by :func:`compute_pearson_correlation`.

    The function reads a NetCDF file that contains at least a variable with the
    raw p‑values (default name ``p_value``).  It computes FDR‑adjusted p‑values
    using ``statsmodels.stats.multitest.multipletests`` with the ``fdr_bh``
    method, adds the adjusted p‑values and a boolean significance mask to a new
    NetCDF file, and writes the result to ``output_path``.

    Parameters
    ----------
    raw_corr_path : str
        Path to the NetCDF file containing the raw correlation results
        (must include the p‑value variable).
    output_path : str
        Destination NetCDF file that will store the adjusted p‑values and a
        significance flag.
    pval_name : str, optional
        Variable name of the raw p‑values in ``raw_corr_path``.
    adj_pval_name : str, optional
        Variable name for the FDR‑adjusted p‑values in the output file.
    significance_name : str, optional
        Variable name for a boolean mask indicating significance
        (adjusted p‑value < ``alpha``).
    alpha : float, optional
        Desired false‑discovery rate (default 0.05).

    Returns
    -------
    None
        The function writes the corrected dataset to ``output_path``.
    """
    log.info("Loading raw correlation dataset from %s", raw_corr_path)
    raw_path = Path(raw_corr_path)
    if not raw_path.is_file():
        raise FileNotFoundError(f"Raw correlation file not found: {raw_path}")

    ds_raw = xr.open_dataset(raw_path)
    if pval_name not in ds_raw:
        raise KeyError(f"P‑value variable '{pval_name}' not found in {raw_path}")

    pvals = ds_raw[pval_name].values.astype(np.float64)
    # Flatten, drop NaNs (they remain NaN after correction)
    flat_pvals = pvals.ravel()
    valid_mask = np.isfinite(flat_pvals)

    if not np.any(valid_mask):
        raise ValueError("No valid p‑values found to correct.")

    # Apply Benjamini‑Hochberg FDR correction on the valid entries
    log.info("Applying Benjamini‑Hochberg FDR correction (alpha=%.3f)", alpha)
    corrected = np.full_like(flat_pvals, np.nan)
    # multipletests returns (reject, pvals_corrected, _, _)
    reject, pvals_corrected, _, _ = multipletests(
        flat_pvals[valid_mask], alpha=alpha, method="fdr_bh"
    )
    corrected[valid_mask] = pvals_corrected

    # Reshape to original grid shape
    adj_pvals = corrected.reshape(pvals.shape)

    # Significance mask (True where adjusted p < alpha)
    significance = np.full_like(adj_pvals, False, dtype=bool)
    significance[valid_mask] = reject

    # Build output dataset – keep original coordinates and any existing
    # coefficient variable(s) for completeness.
    ds_out = ds_raw.copy()
    ds_out[adj_pval_name] = (("lat", "lon"), adj_pvals, {"description": "Benjamini‑Hochberg adjusted p‑value"})
    ds_out[significance_name] = (("lat", "lon"), significance, {"description": f"Significance mask (adjusted p < {alpha})"})

    ds_out.attrs["fdr_method"] = "fdr_bh"
    ds_out.attrs["fdr_alpha"] = alpha
    ds_out.attrs["generated_by"] = __name__

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log.info("Writing FDR‑corrected results to %s", out_path)
    ds_out.to_netcdf(out_path, format="NETCDF4")
    log.info("Benjamini‑Hochberg FDR correction completed successfully.")

# ----------------------------------------------------------------------
# Task T022 – Full pipeline: compute correlation and save BH‑FDR results
# ----------------------------------------------------------------------
def run_correlation_fdr_pipeline(
    ar_freq_path: str,
    z_anom_path: str,
    band: str,
    season: str,
    output_dir: str = "data/processed",
    ar_variable: str = "ar_frequency",
    z_variable: str = "z_anomaly",
    coeff_name: str = "pearson_r",
    pval_name: str = "p_value",
    adj_pval_name: str = "p_adj_fdr",
    significance_name: str = "significant",
    alpha: float = 0.05,
) -> None:
    """
    End‑to‑end pipeline for a specific latitudinal band and season.

    1. Compute Pearson correlation (raw) between AR frequency and Z500
       anomalies.
    2. Apply Benjamini‑Hochberg FDR correction.
    3. Write the final NetCDF file named
       ``corr_fdr_{band}_{season}.nc`` containing:
         * ``coeff_name`` – Pearson correlation coefficient
         * ``pval_name`` – raw two‑tailed p‑value
         * ``adj_pval_name`` – BH‑FDR adjusted p‑value
         * ``significance_name`` – boolean mask (adjusted p < ``alpha``)

    Parameters
    ----------
    ar_freq_path, z_anom_path : str
        Paths to the pre‑processed AR frequency and Z500 anomaly NetCDF files.
    band : str
        Latitude band identifier (e.g., ``"30-40N"``).
    season : str
        Season identifier (e.g., ``"DJF"``, ``"MAM"``, ``"JJA"``, ``"SON"``).
    output_dir : str, optional
        Directory where the final ``corr_fdr_*.nc`` file will be written.
    ar_variable, z_variable, coeff_name, pval_name, adj_pval_name,
    significance_name, alpha : optional
        Passed through to the underlying helper functions.

    Returns
    -------
    None
        The final NetCDF file is written to ``output_dir``.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    raw_corr_path = output_path / f"corr_raw_{band}_{season}.nc"
    final_corr_path = output_path / f"corr_fdr_{band}_{season}.nc"

    log.info(
        "Running full correlation‑FDR pipeline for band=%s, season=%s",
        band,
        season,
    )
    # Step 1: Pearson correlation
    compute_pearson_correlation(
        ar_freq_path=ar_freq_path,
        z_anom_path=z_anom_path,
        output_path=str(raw_corr_path),
        ar_variable=ar_variable,
        z_variable=z_variable,
        coeff_name=coeff_name,
        pval_name=pval_name,
    )

    # Step 2: BH‑FDR correction, writing final file
    apply_bh_fdr_correction(
        raw_corr_path=str(raw_corr_path),
        output_path=str(final_corr_path),
        pval_name=pval_name,
        adj_pval_name=adj_pval_name,
        significance_name=significance_name,
        alpha=alpha,
    )
    log.info(
        "Pipeline completed: final results saved to %s",
        final_corr_path,
    )

# ----------------------------------------------------------------------
# Task T023a – Spatial Validation against teleconnection templates
# ----------------------------------------------------------------------
_TELECONNECTION_URLS = {
    "PNA": "https://www.cpc.ncep.noaa.gov/data/teleconnections/pna.txt",
    "NAO": "https://www.cpc.ncep.noaa.gov/data/teleconnections/nao.txt",
}

def _download_template(name: str) -> xr.DataArray:
    """
    Download a teleconnection spatial pattern (PNA or NAO) from NOAA CPC
    and return it as an ``xr.DataArray`` with dimensions (lat, lon).

    Parameters
    ----------
    name : str
        Either ``\"PNA\"`` or ``\"NAO\"`` (case‑insensitive).

    Returns
    -------
    xr.DataArray
        Spatial pattern aligned on a regular lat/lon grid.

    Raises
    ------
    ValueError
        If ``name`` is not recognised.
    RuntimeError
        If the HTTP request fails or the file cannot be parsed.
    """
    key = name.upper()
    if key not in _TELECONNECTION_URLS:
        raise ValueError(f"Unsupported teleconnection template: {name}")

    url = _TELECONNECTION_URLS[key]
    log.info("Downloading %s template from %s", key, url)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    # Parse the whitespace‑separated text file. Expected format:
    #   lat lon value
    lines = [
        line for line in resp.text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    records = []
    for line in lines:
        parts = line.split()
        if len(parts) != 3:
            continue  # skip malformed lines
        try:
            lat, lon, val = map(float, parts)
            records.append((lat, lon, val))
        except ValueError:
            continue

    if not records:
        raise RuntimeError(f"No valid data found in template file {url}")

    df = pd.DataFrame(records, columns=["lat", "lon", "value"])
    # Pivot to a 2‑D grid (lat x lon)
    df_grid = df.pivot(index="lat", columns="lon", values="value")
    lat_vals = df_grid.index.values
    lon_vals = df_grid.columns.values
    da = xr.DataArray(
        df_grid.values,
        dims=("lat", "lon"),
        coords={"lat": lat_vals, "lon": lon_vals},
        name=key,
    )
    return da

def spatial_validation(
    corr_path: str,
    band: str,
    season: str,
    output_path: str,
    coeff_name: str = "pearson_r",
    significance_name: str = "significant",
) -> None:
    """
    Compute spatial correlation between the significant AR‑Z500 correlation
    pattern and canonical teleconnection templates (PNA and NAO).

    The function:
    1. Loads the FDR‑corrected correlation NetCDF file.
    2. Masks the Pearson correlation coefficients using the ``significant``
       boolean variable (adjusted p‑value < 0.05).
    3. Downloads the PNA and NAO spatial patterns from NOAA CPC.
    4. Aligns the masked pattern with each template (inner join on lat/lon).
    5. Computes a Pearson correlation coefficient and two‑tailed p‑value
       between the two spatial fields.
    6. Writes a JSON file containing the results for each template.

    Parameters
    ----------
    corr_path : str
        Path to the FDR‑corrected NetCDF file (output of Task T022).
    band : str
        Latitude band identifier (e.g., ``\"30-40N\"``).
    season : str
        Season identifier (e.g., ``\"DJF\"``).
    output_path : str
        Destination JSON file.  Parent directories are created automatically.
    coeff_name : str, optional
        Name of the Pearson correlation coefficient variable in ``corr_path``.
    significance_name : str, optional
        Name of the boolean significance mask variable in ``corr_path``.

    Returns
    -------
    None
        The JSON file is written to ``output_path``.
    """
    log.info("Loading FDR‑corrected correlation dataset from %s", corr_path)
    ds = xr.open_dataset(corr_path)
    if coeff_name not in ds or significance_name not in ds:
        raise KeyError(f"Dataset must contain variables '{coeff_name}' and '{significance_name}'")

    # Apply the significance mask
    pattern = ds[coeff_name].where(ds[significance_name])
    results = {}

    for tmpl_name in ("PNA", "NAO"):
        tmpl_da = _download_template(tmpl_name)

        # Align the two fields on common lat/lon points
        pattern_aligned, tmpl_aligned = xr.align(pattern, tmpl_da, join="inner")
        x = pattern_aligned.values.ravel()
        y = tmpl_aligned.values.ravel()
        mask = np.isfinite(x) & np.isfinite(y)

        if mask.sum() < 2:
            corr_val = np.nan
            p_val = np.nan
        else:
            corr_val, p_val = stats.pearsonr(x[mask], y[mask])

        results[tmpl_name] = {
            "spatial_corr": float(corr_val),
            "p_value": float(p_val),
        }
        log.info(
            "Spatial validation against %s: r=%.4f, p=%.4g",
            tmpl_name,
            corr_val,
            p_val,
        )

    output_dict = {
        "band": band,
        "season": season,
        "validation": results,
    }

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as fp:
        json.dump(output_dict, fp, indent=2)
    log.info("Spatial validation results written to %s", out_path)

# ----------------------------------------------------------------------
# Task T023b – Scalar Regression against PNA/NAO indices
# ----------------------------------------------------------------------
_SCALAR_INDEX_URLS = {
    "PNA": "https://www.cpc.ncep.noaa.gov/data/indices/pna.txt",
    "NAO": "https://www.cpc.ncep.noaa.gov/data/indices/nao.txt",
}

def _download_scalar_index(name: str) -> pd.Series:
    """
    Download a scalar teleconnection index (PNA or NAO) from NOAA CPC and
    return it as a pandas Series indexed by ``datetime64[ns]`` (monthly).

    Parameters
    ----------
    name : str
        Either ``\"PNA\"`` or ``\"NAO\"`` (case‑insensitive).

    Returns
    -------
    pd.Series
        Monthly index values with a ``DatetimeIndex``. Missing values are
        represented as ``np.nan``.

    Raises
    ------
    ValueError
        If ``name`` is not recognised.
    RuntimeError
        If the HTTP request fails or the file cannot be parsed.
    """
    key = name.upper()
    if key not in _SCALAR_INDEX_URLS:
        raise ValueError(f"Unsupported scalar index: {name}")

    url = _SCALAR_INDEX_URLS[key]
    log.info("Downloading scalar index %s from %s", key, url)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    # Expected format: year month value (whitespace separated), possibly with header/comments.
    lines = [
        line for line in resp.text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    dates = []
    values = []
    for line in lines:
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            year = int(parts[0])
            month = int(parts[1])
            val = float(parts[2])
            dates.append(pd.Timestamp(year=year, month=month, day=1))
            values.append(val)
        except ValueError:
            continue

    if not dates:
        raise RuntimeError(f"No valid data found in scalar index file {url}")

    series = pd.Series(data=values, index=pd.DatetimeIndex(dates), name=key)
    series = series.sort_index()
    return series

def scalar_validation(
    ar_freq_path: str,
    z_anom_path: str,
    band: str,
    season: str,
    output_path: str,
    ar_variable: str = "ar_frequency",
    z_variable: str = "z_anomaly",
    index_names: Tuple[str, ...] = ("PNA", "NAO"),
) -> None:
    """
    Regress the AR‑Z500 fields against scalar teleconnection indices (PNA, NAO).

    For each index the function:
    1. Loads the AR frequency and Z500 anomaly datasets.
    2. Computes the spatial mean time series for AR frequency and Z anomaly.
    3. Downloads the scalar index time series from NOAA CPC.
    4. Aligns the index with the AR/Z time series (inner join on months).
    5. Computes Pearson correlation coefficients and two‑tailed p‑values
       between the index and the spatially‑averaged AR frequency series,
       and between the index and the spatially‑averaged Z anomaly series.
    6. Stores the results in a JSON file with the following structure::

           {
               "band": "<band>",
               "season": "<season>",
               "scalar_validation": {
                   "PNA": {
                       "ar_corr": <float>,
                       "ar_p": <float>,
                       "z_corr": <float>,
                       "z_p": <float>
                   },
                   "NAO": { ... }
               }
           }

    Parameters
    ----------
    ar_freq_path : str
        Path to the NetCDF file containing AR frequency counts.
    z_anom_path : str
        Path to the NetCDF file containing Z500 anomalies.
    band : str
        Latitude band identifier (e.g., ``"30-40N\"``).
    season : str
        Season identifier (e.g., ``\"DJF\"``).
    output_path : str
        Destination JSON file.  Parent directories are created automatically.
    ar_variable, z_variable : str, optional
        Variable names to read from the respective NetCDF files.
    index_names : tuple of str, optional
        Names of scalar indices to validate against (default PNA and NAO).

    Returns
    -------
    None
        The JSON file is written to ``output_path``.
    """
    # Load AR frequency and Z anomaly datasets
    log.info("Loading AR frequency dataset from %s", ar_freq_path)
    ar_da = _load_dataset(Path(ar_freq_path), ar_variable)
    log.info("Loading Z500 anomaly dataset from %s", z_anom_path)
    z_da = _load_dataset(Path(z_anom_path), z_variable)

    # Align on time dimension
    log.info("Aligning AR and Z datasets on time")
    ar_aligned, z_aligned = _align_dataarrays(ar_da, z_da)

    # Compute spatial mean time series (average over lat/lon)
    log.info("Computing spatial mean time series for AR frequency")
    ar_series = ar_aligned.mean(dim=("lat", "lon")).values
    log.info("Computing spatial mean time series for Z anomaly")
    z_series = z_aligned.mean(dim=("lat", "lon")).values

    # Convert to pandas Series with datetime index
    time_coords = pd.to_datetime(ar_aligned["time"].values)
    ar_ts = pd.Series(ar_series, index=time_coords, name="ar_frequency")
    z_ts = pd.Series(z_series, index=time_coords, name="z_anomaly")

    results = {}

    for idx_name in index_names:
        idx_series = _download_scalar_index(idx_name)

        # Align the index with the AR/Z time series (inner join)
        combined = pd.concat([ar_ts, z_ts, idx_series], axis=1, join="inner")
        if combined.empty:
            log.warning("No overlapping time steps between data and index %s", idx_name)
            results[idx_name] = {
                "ar_corr": np.nan,
                "ar_p": np.nan,
                "z_corr": np.nan,
                "z_p": np.nan,
            }
            continue

        # Correlation between index and AR frequency
        ar_corr, ar_p = stats.pearsonr(combined["ar_frequency"], combined[idx_name])
        # Correlation between index and Z anomaly
        z_corr, z_p = stats.pearsonr(combined["z_anomaly"], combined[idx_name])

        results[idx_name] = {
            "ar_corr": float(ar_corr),
            "ar_p": float(ar_p),
            "z_corr": float(z_corr),
            "z_p": float(z_p),
        }
        log.info(
            "Scalar validation %s: AR r=%.4f (p=%.3g), Z r=%.4f (p=%.3g)",
            idx_name,
            ar_corr,
            ar_p,
            z_corr,
            z_p,
        )

    output_dict = {
        "band": band,
        "season": season,
        "scalar_validation": results,
    }

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as fp:
        json.dump(output_dict, fp, indent=2)
    log.info("Scalar validation results written to %s", out_path)

# ----------------------------------------------------------------------
# Task T031 – Sensitivity Analysis Wrapper (already implemented)
# ----------------------------------------------------------------------
def run_sensitivity_analysis(
    ivt_path: str,
    z_anom_path: str,
    band: str,
    season: str,
    output_dir: str = "data/processed",
    baseline_threshold: float = 250.0,
    delta_vals: Tuple[float, ...] = (-10.0, -5.0, 0.0, 5.0, 10.0),
    ar_variable: str = "ar_frequency",
    z_variable: str = "z_anomaly",
    ivt_variable: str = "integrated_water_vapor_transport",
    **pipeline_kwargs,
) -> None:
    """
    Wrapper to perform a sensitivity sweep over AR detection thresholds.

    For each threshold defined as ``baseline_threshold + delta`` (where ``delta``
    is taken from ``delta_vals``), this function:

    1. Loads the IVT data.
    2. Detects AR events using the parameterised threshold.
    3. Aggregates monthly AR frequency counts and writes them to
       ``ar_freq_{band}_{threshold}.nc``.
    4. Runs the full correlation + BH‑FDR pipeline (Task T019‑T022) using the
       generated AR frequency file and the provided Z500 anomaly file.
    5. Renames the final correlation output to include the threshold value,
       e.g., ``corr_fdr_{band}_{season}_{threshold}.nc``.

    Parameters
    ----------
    ivt_path : str
        Path to the NetCDF file containing the IVT variable.
    z_anom_path : str
        Path to the NetCDF file containing Z500 anomalies.
    band : str
        Latitude band identifier (e.g., ``"30-40N\"``).
    season : str
        Season identifier (e.g., ``\"DJF\"``).
    output_dir : str, optional
        Directory where all intermediate and final artefacts are written.
    baseline_threshold : float, optional
        Baseline IVT threshold (kg m⁻¹ s⁻¹) used in the original analysis.
    delta_vals : tuple of float, optional
        Relative adjustments to apply to the baseline (default ±10, ±5, and 0).
    ar_variable, z_variable, ivt_variable : str, optional
        Variable names used in the NetCDF files.
    pipeline_kwargs : dict
        Additional keyword arguments forwarded to ``run_correlation_fdr_pipeline``
        (e.g., ``alpha`` for FDR).

    Returns
    -------
    None
        All artefacts are written to ``output_dir``.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Load IVT dataset once (shared across thresholds)
    log.info("Loading IVT dataset from %s", ivt_path)
    ivt_ds = load_chunked_netcdf(ivt_path)
    if ivt_variable not in ivt_ds:
        raise KeyError(f"IVT variable '{ivt_variable}' not found in {ivt_path}")

    ivt_da = ivt_ds[ivt_variable]

    for delta in delta_vals:
        threshold = baseline_threshold + delta
        thresh_str = f"{threshold:.1f}".replace(".", "p")
        log.info("Running sensitivity iteration for threshold = %.1f kg m⁻¹ s⁻¹", threshold)

        # Detect AR events with the current threshold
        ar_events = detect_ar_events(ivt_da, threshold=threshold)

        # Aggregate monthly frequency counts
        ar_freq = aggregate_monthly_frequency(ar_events)

        # Build dataset for AR frequency
        ds_ar = xr.Dataset(
            {
                ar_variable: (("time", "lat", "lon"), ar_freq, {"description": "Monthly AR frequency"}),
            },
            coords={
                "time": ivt_ds["time"],
                "lat": ivt_ds["lat"],
                "lon": ivt_ds["lon"],
            },
        )

        ar_freq_path = out_path / f"ar_freq_{band}_{thresh_str}.nc"
        log.info("Saving AR frequency to %s", ar_freq_path)
        save_processed_dataset(ds_ar, str(ar_freq_path))

        # Run correlation/FDR pipeline
        run_correlation_fdr_pipeline(
            ar_freq_path=str(ar_freq_path),
            z_anom_path=z_anom_path,
            band=band,
            season=season,
            output_dir=output_dir,
            ar_variable=ar_variable,
            z_variable=z_variable,
            **pipeline_kwargs,
        )

        # Rename the final correlation file to include threshold
        final_corr = out_path / f"corr_fdr_{band}_{season}.nc"
        if final_corr.is_file():
            new_name = out_path / f"corr_fdr_{band}_{season}_{thresh_str}.nc"
            log.info("Renaming %s -> %s", final_corr, new_name)
            final_corr.rename(new_name)

# ----------------------------------------------------------------------
# Task T032 – Regenerate AR frequency counts for each threshold variation
# ----------------------------------------------------------------------
def regenerate_ar_frequency_counts(
    ivt_path: str,
    band: str,
    thresholds: List[float],
    output_dir: str = "data/processed",
    ivt_variable: str = "integrated_water_vapor_transport",
    ar_variable: str = "ar_frequency",
) -> None:
    """
    Generate AR monthly frequency count files for a list of explicit thresholds.

    For each threshold in ``thresholds`` the function:
    1. Loads the IVT dataset.
    2. Detects AR events using the given threshold.
    3. Aggregates the events into monthly frequency counts.
    4. Saves the result to ``data/processed/ar_freq_{band}_{threshold}.nc`` where
       ``{threshold}`` is formatted with one decimal place (e.g., ``260.0``).

    This task corresponds to **Task T032** in the project plan.

    Parameters
    ----------
    ivt_path : str
        Path to the NetCDF file containing the IVT variable.
    band : str
        Latitude band identifier (e.g., ``\"30-40N\"``). Used only for naming.
    thresholds : List[float]
        List of AR detection thresholds (kg m⁻¹ s⁻¹) for which to generate
        frequency counts.
    output_dir : str, optional
        Directory where the ``ar_freq_*.nc`` files will be written.
    ivt_variable : str, optional
        Name of the IVT variable inside the NetCDF file.
    ar_variable : str, optional
        Name of the output variable to store in the NetCDF file.

    Returns
    -------
    None
        Files are written to ``output_dir``.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Load IVT data once
    log.info("Loading IVT dataset from %s", ivt_path)
    ivt_ds = load_chunked_netcdf(ivt_path)
    if ivt_variable not in ivt_ds:
        raise KeyError(f"IVT variable '{ivt_variable}' not found in {ivt_path}")

    ivt_da = ivt_ds[ivt_variable]

    for thresh in thresholds:
        thresh_str = f"{thresh:.1f}"
        log.info("Generating AR frequency for threshold %.1f", thresh)

        # Detect AR events
        ar_events = detect_ar_events(ivt_da, threshold=thresh)

        # Aggregate to monthly frequency
        ar_freq = aggregate_monthly_frequency(ar_events)

        ds_ar = xr.Dataset(
            {
                ar_variable: (("time", "lat", "lon"), ar_freq, {"description": "Monthly AR frequency"}),
            },
            coords={
                "time": ivt_ds["time"],
                "lat": ivt_ds["lat"],
                "lon": ivt_ds["lon"],
            },
        )

        out_file = out_path / f"ar_freq_{band}_{thresh_str}.nc"
        log.info("Saving AR frequency file %s", out_file)
        save_processed_dataset(ds_ar, str(out_file))

# ----------------------------------------------------------------------
# Task T033 – Pearson correlation and BH‑FDR for each threshold variation
# ----------------------------------------------------------------------
def compute_threshold_correlations(
    ar_freq_dir: str,
    z_anom_path: str,
    band: str,
    season: str,
    thresholds: List[float],
    output_dir: str = "data/processed",
    ar_variable: str = "ar_frequency",
    z_variable: str = "z_anomaly",
    coeff_name: str = "pearson_r",
    pval_name: str = "p_value",
    adj_pval_name: str = "p_adj_fdr",
    significance_name: str = "significant",
    alpha: float = 0.05,
) -> None:
    """
    For each AR detection threshold supplied, compute the Pearson correlation
    between the corresponding AR frequency dataset and the Z500 anomaly dataset,
    then apply the Benjamini‑Hochberg FDR correction.

    The resulting NetCDF files are named::

        corr_fdr_{band}_{season}_{threshold}.nc

    where ``{threshold}`` is the threshold value formatted with one decimal place
    (e.g., ``260.0``) and ``.`` replaced by ``p`` to keep filenames filesystem‑safe.

    Parameters
    ----------
    ar_freq_dir : str
        Directory containing AR frequency NetCDF files. Files are expected to follow
        the naming pattern ``ar_freq_{band}_{threshold}.nc`` where ``threshold`` matches
        the values supplied in ``thresholds``.
    z_anom_path : str
        Path to the Z500 anomaly NetCDF file (common for all thresholds).
    band : str
        Latitude band identifier (e.g., ``"30-40N"``).
    season : str
        Season identifier (e.g., ``"DJF"``).
    thresholds : List[float]
        List of AR detection thresholds for which to run the correlation/FDR pipeline.
    output_dir : str, optional
        Directory where the final ``corr_fdr_*.nc`` files will be written.
    ar_variable, z_variable, coeff_name, pval_name, adj_pval_name,
    significance_name, alpha : optional
        Passed through to the underlying helper functions.

    Returns
    -------
    None
        All output files are written to ``output_dir``.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    for thresh in thresholds:
        thresh_str = f"{thresh:.1f}".replace(".", "p")
        ar_freq_file = Path(ar_freq_dir) / f"ar_freq_{band}_{thresh_str}.nc"
        if not ar_freq_file.is_file():
            raise FileNotFoundError(f"AR frequency file not found for threshold {thresh}: {ar_freq_file}")

        raw_corr_path = out_path / f"corr_raw_{band}_{season}_{thresh_str}.nc"
        final_corr_path = out_path / f"corr_fdr_{band}_{season}_{thresh_str}.nc"

        log.info(
            "Processing threshold %.1f (file %s)",
            thresh,
            ar_freq_file.name,
        )

        # Step 1: Pearson correlation
        compute_pearson_correlation(
            ar_freq_path=str(ar_freq_file),
            z_anom_path=z_anom_path,
            output_path=str(raw_corr_path),
            ar_variable=ar_variable,
            z_variable=z_variable,
            coeff_name=coeff_name,
            pval_name=pval_name,
        )

        # Step 2: BH‑FDR correction
        apply_bh_fdr_correction(
            raw_corr_path=str(raw_corr_path),
            output_path=str(final_corr_path),
            pval_name=pval_name,
            adj_pval_name=adj_pval_name,
            significance_name=significance_name,
            alpha=alpha,
        )
        log.info(
            "Threshold %.1f processing complete: %s",
            thresh,
            final_corr_path.name,
        )

# ----------------------------------------------------------------------
# Command‑line interface (optional, for manual execution)
# ----------------------------------------------------------------------
def _parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Utility for Pearson correlation, BH‑FDR correction, spatial and scalar validation."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Sub‑command for Pearson correlation (Task T019)
    corr_parser = subparsers.add_parser("correlate", help="Compute Pearson correlation.")
    corr_parser.add_argument("ar_freq", type=str, help="AR frequency NetCDF file.")
    corr_parser.add_argument("z_anom", type=str, help="Z500 anomaly NetCDF file.")
    corr_parser.add_argument("output", type=str, help="Output NetCDF file for raw correlation.")
    corr_parser.add_argument("--ar-var", default="ar_frequency", help="Variable name for AR frequency.")
    corr_parser.add_argument("--z-var", default="z_anomaly", help="Variable name for Z500 anomaly.")

    # Sub‑command for BH‑FDR correction (Task T020)
    fdr_parser = subparsers.add_parser("fdr", help="Apply Benjamini‑Hochberg FDR correction.")
    fdr_parser.add_argument("raw_corr", type=str, help="Raw correlation NetCDF file (output of 'correlate').")
    fdr_parser.add_argument("output", type=str, help="Output NetCDF file with adjusted p‑values.")
    fdr_parser.add_argument(
        "--pval-var", default="p_value", help="Variable name of raw p‑values in raw_corr."
    )
    fdr_parser.add_argument(
        "--alpha", type=float, default=0.05, help="Target FDR level (default 0.05)."
    )

    # Sub‑command for the full pipeline (Task T022)
    pipeline_parser = subparsers.add_parser(
        "pipeline", help="Run full correlation + BH‑FDR pipeline for a band/season."
    )
    pipeline_parser.add_argument("ar_freq", type=str, help="AR frequency NetCDF file.")
    pipeline_parser.add_argument("z_anom", type=str, help="Z500 anomaly NetCDF file.")
    pipeline_parser.add_argument("band", type=str, help="Latitude band identifier (e.g., 30-40N).")
    pipeline_parser.add_argument("season", type=str, help="Season identifier (DJF, MAM, JJA, SON).")
    pipeline_parser.add_argument(
        "--output-dir", default="data/processed", help="Directory for final NetCDF output."
    )
    pipeline_parser.add_argument("--alpha", type=float, default=0.05, help="FDR alpha level.")
    pipeline_parser.add_argument("--ar-var", default="ar_frequency", help="AR variable name.")
    pipeline_parser.add_argument("--z-var", default="z_anomaly", help="Z anomaly variable name.")

    # Sub‑command for spatial validation (Task T023a)
    validate_parser = subparsers.add_parser(
        "validate_spatial",
        help="Compute spatial correlation against PNA/NAO templates.",
    )
    validate_parser.add_argument("corr_path", type=str, help="FDR‑corrected correlation NetCDF file.")
    validate_parser.add_argument("band", type=str, help="Latitude band identifier.")
    validate_parser.add_argument("season", type=str, help="Season identifier.")
    validate_parser.add_argument(
        "output", type=str, help="Destination JSON file for validation results."
    )
    validate_parser.add_argument(
        "--coeff-var", default="pearson_r", help="Name of the correlation coefficient variable."
    )
    validate_parser.add_argument(
        "--sig-var", default="significant", help="Name of the significance mask variable."
    )

    # Sub‑command for scalar validation (Task T023b)
    scalar_parser = subparsers.add_parser(
        "validate_scalar",
        help="Regress AR‑Z500 fields against scalar PNA/NAO indices.",
    )
    scalar_parser.add_argument("ar_freq", type=str, help="AR frequency NetCDF file.")
    scalar_parser.add_argument("z_anom", type=str, help="Z500 anomaly NetCDF file.")
    scalar_parser.add_argument("band", type=str, help="Latitude band identifier.")
    scalar_parser.add_argument("season", type=str, help="Season identifier.")
    scalar_parser.add_argument(
        "output", type=str, help="Destination JSON file for scalar validation results."
    )
    scalar_parser.add_argument(
        "--ar-var", default="ar_frequency", help="Variable name for AR frequency."
    )
    scalar_parser.add_argument(
        "--z-var", default="z_anomaly", help="Variable name for Z anomaly."
    )
    scalar_parser.add_argument(
        "--indices", nargs="+", default=["PNA", "NAO"],
        help="Scalar index names to use (default PNA NAO)."
    )

    # Sub‑command for sensitivity analysis (Task T031)
    sens_parser = subparsers.add_parser(
        "sensitivity",
        help="Run sensitivity analysis over AR detection thresholds.",
    )
    sens_parser.add_argument("ivt_path", type=str, help="IVT NetCDF file.")
    sens_parser.add_argument("z_anom_path", type=str, help="Z500 anomaly NetCDF file.")
    sens_parser.add_argument("band", type=str, help="Latitude band identifier.")
    sens_parser.add_argument("season", type=str, help="Season identifier.")
    sens_parser.add_argument(
        "--output-dir", default="data/processed", help="Directory for all outputs."
    )
    sens_parser.add_argument(
        "--baseline", type=float, default=250.0, help="Baseline IVT threshold."
    )
    sens_parser.add_argument(
        "--deltas", nargs="+", type=float, default="-10 -5 0 5 10",
        help="Threshold adjustments (e.g., -10 -5 0 5 10)."
    )
    sens_parser.add_argument(
        "--ar-var", default="ar_frequency", help="AR frequency variable name."
    )
    sens_parser.add_argument(
        "--z-var", default="z_anomaly", help="Z anomaly variable name."
    )
    sens_parser.add_argument(
        "--ivt-var", default="integrated_water_vapor_transport", help="IVT variable name."
    )
    sens_parser.add_argument(
        "--alpha", type=float, default=0.05, help="FDR alpha level."
    )

    # Sub‑command for AR frequency regeneration (Task T032)
    regen_parser = subparsers.add_parser(
        "regenerate_ar_freq",
        help="Regenerate AR frequency counts for explicit threshold list (Task T032).",
    )
    regen_parser.add_argument("ivt_path", type=str, help="IVT NetCDF file.")
    regen_parser.add_argument("band", type=str, help="Latitude band identifier.")
    regen_parser.add_argument(
        "thresholds",
        nargs="+",
        type=float,
        help="List of thresholds (kg m⁻¹ s⁻¹) to generate frequency files for.",
    )
    regen_parser.add_argument(
        "--output-dir", default="data/processed", help="Directory for frequency NetCDF files."
    )
    regen_parser.add_argument(
        "--ivt-var", default="integrated_water_vapor_transport", help="IVT variable name."
    )
    regen_parser.add_argument(
        "--ar-var", default="ar_frequency", help="AR frequency variable name."
    )

    # Sub‑command for threshold‑wise correlation/FDR (Task T033)
    thresh_corr_parser = subparsers.add_parser(
        "threshold_corr",
        help="Compute Pearson correlation and BH‑FDR for each AR threshold.",
    )
    thresh_corr_parser.add_argument("ar_freq_dir", type=str, help="Directory containing AR frequency NetCDF files.")
    thresh_corr_parser.add_argument("z_anom_path", type=str, help="Z500 anomaly NetCDF file.")
    thresh_corr_parser.add_argument("band", type=str, help="Latitude band identifier.")
    thresh_corr_parser.add_argument("season", type=str, help="Season identifier.")
    thresh_corr_parser.add_argument(
        "thresholds",
        nargs="+",
        type=float,
        help="List of thresholds (kg m⁻¹ s⁻¹) to process.",
    )
    thresh_corr_parser.add_argument(
        "--output-dir", default="data/processed", help="Directory for correlation NetCDF outputs."
    )
    thresh_corr_parser.add_argument("--ar-var", default="ar_frequency", help="AR variable name.")
    thresh_corr_parser.add_argument("--z-var", default="z_anomaly", help="Z anomaly variable name.")
    thresh_corr_parser.add_argument("--alpha", type=float, default=0.05, help="FDR alpha level.")

    # Sub‑command for AR frequency regeneration (Task T032) – already added above

    return parser.parse_args()

def main() -> None:
    """
    Entry point for ``python -m src.data.analysis``.
    """
    args = _parse_cli()
    if args.command == "correlate":
        compute_pearson_correlation(
            ar_freq_path=args.ar_freq,
            z_anom_path=args.z_anom,
            output_path=args.output,
            ar_variable=args.ar_var,
            z_variable=args.z_var,
        )
    elif args.command == "fdr":
        apply_bh_fdr_correction(
            raw_corr_path=args.raw_corr,
            output_path=args.output,
            pval_name=args.pval_var,
            alpha=args.alpha,
        )
    elif args.command == "pipeline":
        run_correlation_fdr_pipeline(
            ar_freq_path=args.ar_freq,
            z_anom_path=args.z_anom,
            band=args.band,
            season=args.season,
            output_dir=args.output_dir,
            ar_variable=args.ar_var,
            z_variable=args.z_var,
            alpha=args.alpha,
        )
    elif args.command == "validate_spatial":
        spatial_validation(
            corr_path=args.corr_path,
            band=args.band,
            season=args.season,
            output_path=args.output,
            coeff_name=args.coeff_var,
            significance_name=args.sig_var,
        )
    elif args.command == "validate_scalar":
        scalar_validation(
            ar_freq_path=args.ar_freq,
            z_anom_path=args.z_anom,
            band=args.band,
            season=args.season,
            output_path=args.output,
            ar_variable=args.ar_var,
            z_variable=args.z_var,
            index_names=tuple(args.indices),
        )
    elif args.command == "sensitivity":
        # Parse deltas list (strings) into floats
        delta_vals = tuple(float(d) for d in args.deltas)
        run_sensitivity_analysis(
            ivt_path=args.ivt_path,
            z_anom_path=args.z_anom_path,
            band=args.band,
            season=args.season,
            output_dir=args.output_dir,
            baseline_threshold=args.baseline,
            delta_vals=delta_vals,
            ar_variable=args.ar_var,
            z_variable=args.z_var,
            ivt_variable=args.ivt_var,
            alpha=args.alpha,
        )
    elif args.command == "regenerate_ar_freq":
        # thresholds are already a list of floats from argparse
        regenerate_ar_frequency_counts(
            ivt_path=args.ivt_path,
            band=args.band,
            thresholds=args.thresholds,
            output_dir=args.output_dir,
            ivt_variable=args.ivt_var,
            ar_variable=args.ar_var,
        )
    elif args.command == "threshold_corr":
        compute_threshold_correlations(
            ar_freq_dir=args.ar_freq_dir,
            z_anom_path=args.z_anom_path,
            band=args.band,
            season=args.season,
            thresholds=args.thresholds,
            output_dir=args.output_dir,
            ar_variable=args.ar_var,
            z_variable=args.z_var,
            alpha=args.alpha,
        )
    else:
        raise RuntimeError(f"Unsupported command: {args.command}")

if __name__ == "__main__":
    main()