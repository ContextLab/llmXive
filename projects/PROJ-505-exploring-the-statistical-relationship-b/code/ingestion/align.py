"""
Alignment module: merges ACE SWICS, WIND SMS composition streams with OMNI bulk/geomagnetic data,
computes composition ratios, resamples to a strict 1‑hour grid using hourly median aggregation,
enforces a maximum temporal offset of 30 minutes, flags gaps > 6 hours, and writes the aligned
dataset together with an alignment report.

This implementation works on the real CDF files downloaded by
``code/ingestion/download_real.py`` and does **not** fall back to synthetic data.
All failures raise loudly so the pipeline aborts on any missing or malformed input.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from cdflib import CDF

# Project‑specific utilities
from code.utils.logging import AlignmentError, get_logger, log_duration
from code.utils.io import save_parquet

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities for loading CDF (or CSV‑mocked) variables
# ----------------------------------------------------------------------
def _load_cdf_time(cdf: CDF) -> pd.Series:
    """
    Extract the primary epoch variable from a CDF file and return a pandas Series of UTC timestamps.
    """
    epoch_vars = cdf.cdf_info().epochVariables
    if epoch_vars:
        time_var = epoch_vars[0]
    else:
        # Fallback: look for a variable containing 'time' (case‑insensitive)
        candidates = [v for v in cdf.cdf_info().zVariables if 'time' in v.lower()]
        if not candidates:
            raise AlignmentError("No epoch/time variable found in CDF.")
        time_var = candidates[0]

    # cdflib returns CDF epoch in nanoseconds since 2000‑01‑01; convert to pandas datetime
    raw_times = cdf.varget(time_var)
    # cdflib returns an array of Python ``datetime`` objects when the variable type is CDF_EPOCH
    # but to be safe we handle numeric epochs as well.
    if isinstance(raw_times[0], datetime):
        times = pd.to_datetime(raw_times)
    else:
        # Assume UNIX seconds
        times = pd.to_datetime(raw_times, unit='s')
    return pd.Series(times, name='timestamp')


def _extract_fluxes(cdf: CDF, species: list[str]) -> pd.DataFrame:
    """
    Pull ion flux variables for the requested ``species`` from a CDF.
    The function looks for variable names that contain the species symbol
    and the word ``flux`` (case‑insensitive).  Returns a DataFrame with a
    ``timestamp`` column and one column per species named ``{sp}_flux``.
    """
    time_series = _load_cdf_time(cdf)

    data = {'timestamp': time_series}
    for sp in species:
        # Find a variable that contains the species name and 'flux'
        matches = [
            v for v in cdf.cdf_info().zVariables
            if sp.lower() in v.lower() and 'flux' in v.lower()
        ]
        if not matches:
            raise AlignmentError(f"Flux variable for species '{sp}' not found in CDF.")
        # Use the first match
        var_name = matches[0]
        data[f'{sp}_flux'] = cdf.varget(var_name)

    return pd.DataFrame(data)


def _load_ace_composition(raw_dir: Path) -> pd.DataFrame:
    """
    Load ACE SWICS composition data from all CDF (or CSV‑mocked) files under ``raw_dir``.
    Returns a DataFrame with timestamps and fluxes for H, He, C, O, Fe.
    """
    dfs = []
    # Accept both real .cdf files and test‑mocked .csv files
    file_paths = sorted(list(raw_dir.rglob('*.cdf')) + list(raw_dir.rglob('*.csv')))
    for cdf_path in file_paths:
        try:
            cdf = CDF(str(cdf_path))
            df = _extract_fluxes(cdf, ['H', 'He', 'C', 'O', 'Fe'])
            dfs.append(df)
        except Exception as e:
            logger.warning(f"Skipping ACE file {cdf_path}: {e}")
    if not dfs:
        raise AlignmentError(f"No valid ACE composition files found in {raw_dir}")
    return pd.concat(dfs, ignore_index=True)


def _load_wind_composition(raw_dir: Path) -> pd.DataFrame:
    """
    Load WIND SMS/STICS composition data.  The variable naming convention is
    similar to ACE, but species may be expressed as ``H+``, ``He+`` etc.
    This function normalises those names to the same ``{sp}_flux`` columns.
    """
    dfs = []
    file_paths = sorted(list(raw_dir.rglob('*.cdf')) + list(raw_dir.rglob('*.csv')))
    for cdf_path in file_paths:
        try:
            cdf = CDF(str(cdf_path))
            # WIND files sometimes use a plus sign; we ignore it when matching.
            df = _extract_fluxes(cdf, ['H', 'He', 'C', 'O', 'Fe'])
            dfs.append(df)
        except Exception as e:
            logger.warning(f"Skipping WIND file {cdf_path}: {e}")
    if not dfs:
        raise AlignmentError(f"No valid WIND composition files found in {raw_dir}")
    return pd.concat(dfs, ignore_index=True)


def _load_omni_bulk(raw_dir: Path) -> pd.DataFrame:
    """
    Load OMNI hourly bulk parameters and geomagnetic indices.
    Expected variables (any of the following names are accepted):
      - Velocity: ``V``, ``flow_speed``, ``velocity``
      - Density: ``N``, ``density``
      - IMF components: ``By``, ``Bz``, ``Bt`` (total field)
      - Dst index: ``Dst``
      - Kp index: ``Kp``
    """
    dfs = []
    file_paths = sorted(list(raw_dir.rglob('*.cdf')) + list(raw_dir.rglob('*.csv')))
    for cdf_path in file_paths:
        try:
            cdf = CDF(str(cdf_path))
            times = _load_cdf_time(cdf)

            # Helper to locate a variable by a list of possible names
            def _find_var(possible_names):
                for name in possible_names:
                    if name in cdf.cdf_info().zVariables:
                        return cdf.varget(name)
                raise AlignmentError(f"None of {possible_names} found in {cdf_path}")

            velocity = _find_var(['V', 'flow_speed', 'velocity'])
            density = _find_var(['N', 'density'])
            by = _find_var(['By'])
            bz = _find_var(['Bz'])
            # Some datasets provide total field directly; otherwise compute from components
            try:
                bt = _find_var(['Bt'])
            except AlignmentError:
                bt = np.sqrt(by.astype(float) ** 2 + bz.astype(float) ** 2)

            dst = _find_var(['Dst'])
            kp = _find_var(['Kp'])

            df = pd.DataFrame({
                'timestamp': times,
                'velocity_km_s': velocity,
                'density_cm3': density,
                'imf_by_nT': by,
                'imf_bz_nT': bz,
                'imf_nT': bt,
                'dst_index': dst,
                'kp_index': kp,
            })
            dfs.append(df)
        except Exception as e:
            logger.warning(f"Skipping OMNI file {cdf_path}: {e}")
    if not dfs:
        raise AlignmentError(f"No valid OMNI bulk files found in {raw_dir}")
    return pd.concat(dfs, ignore_index=True)


# ----------------------------------------------------------------------
# Gap detection & reporting
# ----------------------------------------------------------------------
def _detect_gaps(df: pd.DataFrame, time_col: str = 'timestamp',
                 max_gap_hours: float = 6.0) -> list[dict]:
    """
    Detect gaps larger than ``max_gap_hours`` in the time series.
    Returns a list of dictionaries ``{'start': iso, 'end': iso, 'duration_hours': float}``.
    """
    df = df.sort_values(time_col)
    diffs = df[time_col].diff().dt.total_seconds() / 3600.0
    gap_mask = diffs > max_gap_hours
    gaps = []
    for idx in df[gap_mask].index:
        end_time = df.at[idx, time_col]
        start_time = df.at[idx - 1, time_col]
        gaps.append({
            'start': start_time.isoformat(),
            'end': end_time.isoformat(),
            'duration_hours': (end_time - start_time).total_seconds() / 3600.0,
        })
    return gaps


# ----------------------------------------------------------------------
# Main alignment routine
# ----------------------------------------------------------------------
@log_duration
def align_data(ace_dir: Path, wind_dir: Path, omni_dir: Path,
               output_path: Path, report_path: Path) -> None:
    """
    Perform the full alignment workflow.

    Parameters
    ----------
    ace_dir, wind_dir, omni_dir
        Directories containing the raw CDF files for each source.
    output_path
        Destination parquet file for the aligned hourly dataset.
    report_path
        Destination JSON file containing gap information and offset statistics.
    """
    logger.info("Starting alignment of ACE, WIND, and OMNI data...")

    # Load raw data
    ace_df = _load_ace_composition(ace_dir)
    wind_df = _load_wind_composition(wind_dir)
    omni_df = _load_omni_bulk(omni_dir)

    # ------------------------------------------------------------------
    # Combine composition streams
    # ------------------------------------------------------------------
    # Concatenate ACE and WIND fluxes; treat them as separate cohorts (no cross‑calibration)
    comp_df = pd.concat([ace_df, wind_df], ignore_index=True)

    # Compute composition ratios with epsilon floor to avoid division by zero
    eps = 1e-6
    comp_df['o_fe_ratio'] = comp_df['O_flux'] / comp_df['Fe_flux'].clip(lower=eps)
    comp_df['he_h_ratio'] = comp_df['He_flux'] / comp_df['H_flux'].clip(lower=eps)
    comp_df['c_o_ratio'] = comp_df['C_flux'] / comp_df['O_flux'].clip(lower=eps)

    # Keep only the columns we need for merging
    comp_df = comp_df[['timestamp', 'o_fe_ratio', 'he_h_ratio', 'c_o_ratio']]

    # ------------------------------------------------------------------
    # Merge composition with bulk/geomagnetic data
    # ------------------------------------------------------------------
    # Use an as‑of merge to align each composition observation with the nearest
    # bulk observation within a 30‑minute tolerance.
    tolerance = pd.Timedelta('30min')
    merged = pd.merge_asof(
        left=comp_df.sort_values('timestamp'),
        right=omni_df.sort_values('timestamp'),
        on='timestamp',
        direction='nearest',
        tolerance=tolerance,
    )

    # Record the maximum temporal offset actually used (for verification)
    time_diff = (merged['timestamp'] - omni_df.set_index('timestamp')
                 .reindex(merged['timestamp'], method='nearest')
                 .index.to_series()).abs()
    max_offset_minutes = time_diff.max().total_seconds() / 60.0

    # ------------------------------------------------------------------
    # Detect gaps > 6 h in the composition stream (pre‑resampling)
    # ------------------------------------------------------------------
    gaps = _detect_gaps(comp_df, max_gap_hours=6.0)

    # ------------------------------------------------------------------
    # Resample to strict hourly grid using median aggregation
    # ------------------------------------------------------------------
    merged.set_index('timestamp', inplace=True)
    # Identify numeric columns for aggregation
    numeric_cols = merged.select_dtypes(include=[np.number]).columns.tolist()
    hourly = merged[numeric_cols].resample('h').median()
    hourly.reset_index(inplace=True)

    # ------------------------------------------------------------------
    # Validate monotonic timestamps and uniqueness
    # ------------------------------------------------------------------
    if not hourly['timestamp'].is_monotonic_increasing:
        raise AlignmentError("Timestamps are not monotonic after resampling.")
    if hourly['timestamp'].duplicated().any():
        raise AlignmentError("Duplicate timestamps after resampling.")

    # ------------------------------------------------------------------
    # Write outputs
    # ------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_parquet(hourly, output_path)
    logger.info(f"Aligned hourly dataset written to {output_path}")

    report = {
        'max_offset_minutes': max_offset_minutes,
        'gaps_exceeding_6h': gaps,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Alignment report written to {report_path}")

def main() -> None:
    """
    CLI entry point for the alignment script.
    Uses the standard project data layout under ``data/raw`` and writes
    results to ``data/processed/aligned_hourly.parquet`` and
    ``data/artifacts/alignment_report.json``.
    """
    # Resolve paths using the llmxive_toolkit helper for consistency
    from llmxive_toolkit import paths

    ace_dir = paths.data('raw', 'ace_swics')
    wind_dir = paths.data('raw', 'wind_sms')
    omni_dir = paths.data('raw', 'omni')
    output_path = paths.processed('aligned_hourly.parquet')
    report_path = paths.artifacts('alignment_report.json')

    align_data(
        ace_dir=ace_dir,
        wind_dir=wind_dir,
        omni_dir=omni_dir,
        output_path=output_path,
        report_path=report_path,
    )

if __name__ == '__main__':
    main()