"""
Data parsing module.
Parses raw CSV files extracted from arXiv tarballs into intermediate
:class:`HarmonizedDataset` objects.

The parser:
1. Detects columns for separation, force, and uncertainty using heuristics.
2. Converts raw units (micrometers, dynes) to SI (meters, Newtons).
3. Constructs a diagonal covariance matrix from the reported uncertainties.
4. Returns a list of :class:`HarmonizedDataset` instances, one per
   experimental run or calibration file.

The resulting objects are later consumed by ``code/data/harmonize.py``.
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

from llmxive_toolkit import paths
from config import get_logger
from data.models import HarmonizedDataset

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

def _identify_columns(df: pd.DataFrame) -> Dict[str, str]:
    """
    Identify the column names for separation, force and uncertainty.

    Returns a mapping with keys ``separation``, ``force`` and ``uncertainty``.
    If a column cannot be identified, its value will be ``None``.
    """
    cols_lower = {c.lower(): c for c in df.columns}

    # Separation column heuristics
    sep_patterns = [
        r'separation', r'distance', r'gap', r'r[_\s]*um', r'r[_\s]*\mu\s*m',
        r'separation[_\s]*um', r'distance[_\s]*um'
    ]
    sep_col = _search_column(cols_lower, sep_patterns)

    # Force column heuristics
    force_patterns = [
        r'force', r'f[_\s]*n', r'force[_\s]*n', r'force[_\s]*dyne',
        r'force[_\s]*cgs'
    ]
    force_col = _search_column(cols_lower, force_patterns)

    # Uncertainty column heuristics
    unc_patterns = [
        r'uncertainty', r'error', r'sigma', r'unc', r'err',
        r'uncertainty[_\s]*dyne', r'uncertainty[_\s]*n'
    ]
    unc_col = _search_column(cols_lower, unc_patterns)

    return {
        'separation': sep_col,
        'force': force_col,
        'uncertainty': unc_col
    }

def _search_column(cols_lower: Dict[str, str], patterns: List[str]) -> Optional[str]:
    """
    Return the first column name that matches any of the supplied regex
    patterns (case‑insensitive). If none match, return ``None``.
    """
    for pat in patterns:
        regex = re.compile(pat, re.IGNORECASE)
        for low_name, orig_name in cols_lower.items():
            if regex.search(low_name):
                return orig_name
    return None

def _convert_to_si(
    separation: pd.Series,
    force: pd.Series,
    uncertainty: pd.Series
) -> Dict[str, np.ndarray]:
    """
    Convert raw units to SI.

    * separation: assumed to be in micrometers → meters (1 µm = 1e‑6 m)
    * force: assumed to be in dynes → Newtons (1 dyne = 1e‑5 N)
    * uncertainty: same unit as force → Newtons

    Returns a dict with keys ``separation_m``, ``force_n`` and
    ``uncertainty_n`` (all ``np.ndarray``).
    """
    separation_m = separation.to_numpy(dtype=float) * 1e-6
    force_n = force.to_numpy(dtype=float) * 1e-5
    uncertainty_n = uncertainty.to_numpy(dtype=float) * 1e-5
    return {
        'separation_m': separation_m,
        'force_n': force_n,
        'uncertainty_n': uncertainty_n
    }

def _build_covariance(uncertainty_n: np.ndarray) -> np.ndarray:
    """
    Build a diagonal covariance matrix from the 1‑σ uncertainties.
    """
    variances = uncertainty_n ** 2
    return np.diag(variances)

# ----------------------------------------------------------------------
# Core parsing logic
# ----------------------------------------------------------------------

def parse_raw_data(file_path: Path) -> Optional[HarmonizedDataset]:
    """
    Parse a single raw CSV file and return a :class:`HarmonizedDataset`.

    The function is tolerant of missing columns – if a required column
    cannot be identified the file is skipped and ``None`` is returned.
    """
    logger.debug(f"Attempting to parse raw file: {file_path}")
    try:
        df = pd.read_csv(file_path)
    except Exception as exc:
        logger.error(f"Failed to read CSV {file_path}: {exc}")
        return None

    col_map = _identify_columns(df)
    if not all(col_map.values()):
        logger.warning(
            f"Could not identify required columns in {file_path}. "
            f"Found mapping: {col_map}"
        )
        return None

    # Extract the relevant Series
    sep_series = df[col_map['separation']]
    force_series = df[col_map['force']]
    unc_series = df[col_map['uncertainty']] if col_map['uncertainty'] else pd.Series(np.nan, index=df.index)

    # Convert to SI units
    si_vals = _convert_to_si(sep_series, force_series, unc_series)

    # Build covariance (diagonal) – if uncertainties are NaN we fall back to zeros
    if np.isnan(si_vals['uncertainty_n']).all():
        cov = np.zeros((len(si_vals['separation_m']), len(si_vals['separation_m'])))
    else:
        cov = _build_covariance(si_vals['uncertainty_n'])

    # Metadata – we keep the original file stem as an identifier
    metadata: Dict[str, Any] = {
        'source_file': str(file_path),
        'experiment_id': file_path.stem
    }

    dataset = HarmonizedDataset(
        separation_m=si_vals['separation_m'],
        force_n=si_vals['force_n'],
        covariance_matrix=cov,
        metadata=metadata
    )
    logger.info(f"Parsed dataset from {file_path} with {len(si_vals['separation_m'])} points.")
    return dataset

# ----------------------------------------------------------------------
# ArXiv‑specific wrappers
# ----------------------------------------------------------------------

def _collect_csv_files(raw_dir: Path, arxiv_id_fragment: str) -> List[Path]:
    """
    Return a list of CSV files under ``raw_dir`` that belong to a given
    arXiv identifier. The function looks for the identifier fragment in the
    file path (e.g. ``2106`` for arXiv:2106.08611) and also includes any
    calibration files that match the calibration regex.
    """
    csv_files: List[Path] = []
    # Walk the directory recursively
    for p in raw_dir.rglob("*.csv"):
        if arxiv_id_fragment in p.name or arxiv_id_fragment in str(p):
            csv_files.append(p)
    # Add explicit calibration files (even if they do not contain the id)
    calib_regex = re.compile(r'calibration.*\.(csv|dat)$', re.IGNORECASE)
    for p in raw_dir.rglob("*"):
        if calib_regex.search(p.name):
            csv_files.append(p)
    return csv_files

def parse_arxiv_2106_08611(raw_dir: Path) -> List[HarmonizedDataset]:
    """
    Parse all relevant CSVs from the arXiv:2106.08611 supplementary
    material.
    """
    logger.debug(f"Parsing arXiv:2106.08611 files in {raw_dir}")
    csv_files = _collect_csv_files(raw_dir, "2106")
    datasets: List[HarmonizedDataset] = []
    for f in csv_files:
        ds = parse_raw_data(f)
        if ds is not None:
            datasets.append(ds)
    logger.info(f"Parsed {len(datasets)} datasets from arXiv:2106.08611")
    return datasets

def parse_arxiv_2305_06325(raw_dir: Path) -> List[HarmonizedDataset]:
    """
    Parse all relevant CSVs from the arXiv:2305.06325 supplementary
    material.
    """
    logger.debug(f"Parsing arXiv:2305.06325 files in {raw_dir}")
    csv_files = _collect_csv_files(raw_dir, "2305")
    datasets: List[HarmonizedDataset] = []
    for f in csv_files:
        ds = parse_raw_data(f)
        if ds is not None:
            datasets.append(ds)
    logger.info(f"Parsed {len(datasets)} datasets from arXiv:2305.06325")
    return datasets

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------

def main() -> int:
    """
    CLI entry point used by the pipeline runner.

    It parses the extracted raw data directory and writes a JSON summary
    (list of metadata entries) to ``data/processed/parsing_summary.json``.
    Downstream steps (e.g. ``harmonize.py``) will re‑load the individual
    ``HarmonizedDataset`` objects from their original CSVs, so the JSON
    file is only a lightweight provenance record.
    """
    raw_dir = paths.data("raw", "extracted")
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        return 1

    logger.info(f"Starting parsing of raw data in {raw_dir}")
    datasets_2106 = parse_arxiv_2106_08611(raw_dir)
    datasets_2305 = parse_arxiv_2305_06325(raw_dir)

    all_datasets = datasets_2106 + datasets_2305
    if not all_datasets:
        logger.warning("No datasets were parsed – check the raw data extraction step.")
        return 1

    # Write a minimal summary JSON (metadata only) for provenance.
    summary_path = paths.data("processed", "parsing_summary.json")
    summary = [
        {
            "experiment_id": ds.metadata.get("experiment_id"),
            "source_file": ds.metadata.get("source_file")
        }
        for ds in all_datasets
    ]
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as fp:
        json.dump(summary, fp, indent=2)
    logger.info(f"Wrote parsing summary with {len(summary)} entries to {summary_path}")
    return 0

if __name__ == "__main__":
    exit(main())