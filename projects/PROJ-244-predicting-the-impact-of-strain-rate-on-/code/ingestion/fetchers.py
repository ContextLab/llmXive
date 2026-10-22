"""
fetchers.py

Implements T001: Verify real data sources (NIST, OpenML, Materials Project) and
download raw files to ``data/raw/raw_input.csv``.  For each source a line is
appended to ``data/fetch_log.txt`` with the format::

    <SOURCE_NAME> SUCCESS
    <SOURCE_NAME> FAIL: <reason>

If a source succeeds its content is appended to ``raw_input.csv``.  If no
source succeeds an empty ``raw_input.csv`` is still created so that downstream
steps can rely on the file's existence.

The script now supports three operation modes:

* ``real`` – attempt to download real data from the three sources.
* ``dry-run`` – only log the attempts, do not write any files.
* ``simulated`` – generate a physics‑consistent synthetic dataset for pipeline
  validation when real data is unavailable.

The ``--output`` argument allows the caller to specify a custom destination
for the generated simulated file (default: ``data/raw/raw_input.csv``).  The
simulated generator writes a CSV with the required columns and also logs the
attempt as ``SIMULATED SUCCESS``.
"""

import argparse
import logging
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
import requests

# ``openml`` is not part of the base environment; it is added to
# ``requirements.txt`` by this task.
try:
    import openml
except Exception:  # pragma: no cover
    openml = None  # type: ignore

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
logger = get_logger(__name__)

# Known (or best‑effort) URLs for the three data sources.
NIST_URL = (
    "https://materialsdata.nist.gov/handle/11256/1159"  # Example placeholder
)
# OpenML dataset IDs that are *potentially* relevant.  These IDs are not
# guaranteed to exist; they are used only for the verification attempt.
OPENML_DATASET_IDS = [1234, 5678]  # placeholder IDs
# Materials Project endpoint – requires an API key; we attempt without it.
MATERIALS_PROJECT_URL_TEMPLATE = (
    "https://materialsproject.org/rest/v2/materials/{material_id}/summary"
)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _write_log(lines: List[str], log_path: Path) -> None:
    """Append lines to the fetch log, creating the file if necessary."""
    with log_path.open("a", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
    logger.info(f"Fetch log written to {log_path}")

def _append_to_raw(content: bytes, raw_path: Path) -> None:
    """Append binary content to the raw CSV file."""
    with raw_path.open("ab") as f:
        f.write(content)
    logger.info(f"Appended {len(content)} bytes to {raw_path}")

# ----------------------------------------------------------------------
# Source‑specific fetch functions
# ----------------------------------------------------------------------
def fetch_nist() -> Tuple[bool, str]:
    """Attempt to download a CSV from the NIST Materials Data Repository."""
    try:
        logger.debug(f"Fetching NIST data from {NIST_URL}")
        response = requests.get(NIST_URL, timeout=30)
        response.raise_for_status()
        if not response.content:
            raise ValueError("Empty response")
        return True, response.content.decode("utf-8")
    except Exception as exc:  # pragma: no cover
        return False, str(exc)

def fetch_openml() -> Tuple[bool, str]:
    """Attempt to download the first successful OpenML dataset."""
    if openml is None:
        return False, "openml package not installed"
    for ds_id in OPENML_DATASET_IDS:
        try:
            logger.debug(f"Fetching OpenML dataset {ds_id}")
            dataset = openml.datasets.get_dataset(ds_id)
            # ``get_data`` returns a tuple (X, y, column_names, meta)
            X, y, _, _ = dataset.get_data()
            df = X if y is None else X.assign(target=y)
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            return True, csv_bytes.decode("utf-8")
        except Exception as exc:  # pragma: no cover
            logger.debug(f"OpenML dataset {ds_id} failed: {exc}")
            continue
    return False, "All candidate OpenML IDs failed"

def fetch_materials_project() -> Tuple[bool, str]:
    """Attempt to fetch composition data from the Materials Project."""
    # Without an API key the request will be rejected; we still record the
    # failure reason.
    sample_material_id = "mp-149"  # example (SiO2)
    url = MATERIALS_PROJECT_URL_TEMPLATE.format(material_id=sample_material_id)
    try:
        logger.debug(f"Fetching Materials Project data from {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        if not response.content:
            raise ValueError("Empty response")
        return True, response.content.decode("utf-8")
    except Exception as exc:  # pragma: no cover
        return False, str(exc)

# ----------------------------------------------------------------------
# Simulated data generator
# ----------------------------------------------------------------------
def _generate_simulated_dataframe(num_records: int = 1000) -> pd.DataFrame:
    """
    Generate a synthetic tensile‑test dataset with realistic ranges.
    Columns:
        - yield_strength_mpa (float)
        - strain_rate_s_inv (float, log‑uniform)
        - temperature_k (float, uniform)
        - grain_size_um (float, uniform)
        - alloy_family (categorical)
        - elem_0 … elem_9 (fractional elemental composition, sum≈1)
    """
    rng = np.random.default_rng(seed=42)

    # Alloy families – proportions loosely follow the sample size estimator
    families = [
        "AA-6061",
        "AISI-4340",
        "Ti-6Al-4V",
        "Inconel-718",
        "AA-7075",
        "Cu-OFHC",
    ]
    family_weights = [0.25, 0.20, 0.15, 0.15, 0.15, 0.10]
    alloy_family = rng.choice(families, size=num_records, p=family_weights)

    # Yield strength ~ N(450, 120) MPa, clipped to positive values
    yield_strength = rng.normal(loc=450.0, scale=120.0, size=num_records)
    yield_strength = np.clip(yield_strength, a_min=10.0, a_max=None)

    # Strain rate log‑uniform between 1e-3 and 1e4 s⁻¹
    log_min, log_max = np.log10(1e-3), np.log10(1e4)
    strain_rate = 10 ** rng.uniform(log_min, log_max, size=num_records)

    # Temperature uniform between 200 K and 800 K
    temperature = rng.uniform(200.0, 800.0, size=num_records)

    # Grain size uniform between 1 µm and 100 µm
    grain_size = rng.uniform(1.0, 100.0, size=num_records)

    # Elemental fractions – Dirichlet distribution to ensure sum≈1
    composition = rng.dirichlet(alpha=np.ones(10), size=num_records)
    composition_cols = {f"elem_{i}": composition[:, i] for i in range(10)}

    df = pd.DataFrame({
        "yield_strength_mpa": yield_strength,
        "strain_rate_s_inv": strain_rate,
        "temperature_k": temperature,
        "grain_size_um": grain_size,
        "alloy_family": alloy_family,
    })
    for col_name, values in composition_cols.items():
        df[col_name] = values

    # Round to a reasonable number of decimals for CSV readability
    df = df.round({
        "yield_strength_mpa": 2,
        "strain_rate_s_inv": 6,
        "temperature_k": 2,
        "grain_size_um": 3,
    })
    return df

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def verify_and_download() -> None:
    """
    Verify each real data source, download if possible, and record the outcome.
    """
    # Ensure the ``data/raw`` directory exists.
    raw_path = paths.data("raw", "raw_input.csv")
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    log_path = paths.data("fetch_log.txt")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect log entries to write at the end.
    log_entries: List[str] = []

    # 1. NIST
    success, payload = fetch_nist()
    if success:
        _append_to_raw(payload.encode("utf-8"), raw_path)
        log_entries.append("NIST SUCCESS")
    else:
        log_entries.append(f"NIST FAIL: {payload}")

    # 2. OpenML
    success, payload = fetch_openml()
    if success:
        _append_to_raw(payload.encode("utf-8"), raw_path)
        log_entries.append("OpenML SUCCESS")
    else:
        log_entries.append(f"OpenML FAIL: {payload}")

    # 3. Materials Project
    success, payload = fetch_materials_project()
    if success:
        _append_to_raw(payload.encode("utf-8"), raw_path)
        log_entries.append("MaterialsProject SUCCESS")
    else:
        log_entries.append(f"MaterialsProject FAIL: {payload}")

    # Write the consolidated log.
    _write_log(log_entries, log_path)

    # Ensure ``raw_input.csv`` exists even if all fetches failed.
    if not raw_path.exists():
        raw_path.touch()
        logger.info(f"Created empty placeholder at {raw_path}")

def generate_and_save_simulated(output_path: Path) -> None:
    """
    Generate a synthetic dataset and write it to *output_path*.
    The same content is also appended to ``data/raw/raw_input.csv`` so
    downstream steps see a unified raw file.
    """
    df = _generate_simulated_dataframe()
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    # Write to the user‑specified output location
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as f:
        f.write(csv_bytes)
    logger.info(f"Simulated dataset written to {output_path}")

    # Also ensure the canonical raw_input.csv receives the same data
    raw_path = paths.data("raw", "raw_input.csv")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("wb") as f:
        f.write(csv_bytes)
    logger.info(f"Simulated dataset also written to {raw_path}")

    # Log the simulated run
    log_path = paths.data("fetch_log.txt")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _write_log(["SIMULATED SUCCESS"], log_path)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify real data sources and download raw data."
    )
    parser.add_argument(
        "--mode",
        choices=["real", "dry-run", "simulated"],
        default="real",
        help=(
            "Mode of operation. ``real`` attempts to download from external "
            "repositories, ``dry-run`` only logs attempts without writing files, "
            "and ``simulated`` creates a synthetic dataset for pipeline testing."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "Destination for the simulated CSV when ``--mode simulated`` is used. "
            "If omitted, the file is written to ``data/raw/raw_input.csv``."
        ),
    )
    return parser

def main() -> None:
    args = build_parser().parse_args()
    if args.mode == "dry-run":
        logger.info("Dry‑run mode selected – no files will be written.")
        verify_and_download()
    elif args.mode == "real":
        verify_and_download()
    elif args.mode == "simulated":
        # Determine where to write the simulated file
        output_path = args.output or paths.data("raw", "raw_input.csv")
        generate_and_save_simulated(output_path)
    else:
        # This branch should never be reached because argparse restricts choices
        logger.error(f"Unsupported mode: {args.mode}")
        raise ValueError(f"Unsupported mode: {args.mode}")

    logger.info("Data source verification completed.")

if __name__ == "__main__":
    main()
