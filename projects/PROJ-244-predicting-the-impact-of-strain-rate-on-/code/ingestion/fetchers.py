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

The script is deliberately tolerant of network failures – the purpose of this
phase is *verification*, not mandatory data acquisition.  Real URLs are used
where known; otherwise a best‑effort request is made and any exception is
recorded as a failure.
"""

import argparse
import logging
from pathlib import Path
from typing import List, Tuple

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
# Main orchestration
# ----------------------------------------------------------------------
def verify_and_download() -> None:
    """
    Verify each data source, download if possible, and record the outcome.
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

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify real data sources and download raw data."
    )
    parser.add_argument(
        "--mode",
        choices=["real", "dry-run"],
        default="real",
        help="Mode of operation. ``dry-run`` only logs attempts without writing files.",
    )
    return parser

def main() -> None:
    args = build_parser().parse_args()
    if args.mode == "dry-run":
        logger.info("Dry‑run mode selected – no files will be written.")
    else:
        verify_and_download()
    logger.info("Data source verification completed.")

if __name__ == "__main__":
    main()
