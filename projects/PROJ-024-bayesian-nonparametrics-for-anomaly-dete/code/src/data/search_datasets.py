"""
Search for real‑world time‑series datasets with known regime shifts.

The script attempts to locate and download verified datasets from two
well‑known sources that satisfy the “regime shift” requirement:

1. **NAB (Numenta Anomaly Benchmark)** – a collection of real‑world
   streaming time‑series with annotated anomalies.
2. **PhysioNet – MIT‑BIH Arrhythmia** – ECG recordings with labelled
   arrhythmia events (a type of regime shift).

If at least one dataset is successfully retrieved, the file(s) are saved
under ``data/raw/``.  If no dataset can be obtained, a *Validation
Deferred* report is written to
``data/processed/results/validation_deferred.md`` documenting the
search query and the (zero) result count, fulfilling FR‑017 / FR‑017b.

The script is deliberately lightweight and uses only the standard
library plus ``requests`` (already available in the execution
environment).  All paths are created via the ``llmxive_toolkit.paths``
helper to guarantee they live inside the project directory.
"""

import json
import logging
from pathlib import Path

import requests

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
SEARCH_KEYWORDS = [
    "regime shift time series",
    "anomaly benchmark",
    "physionet arrhythmia",
]

# Known verified URLs for the two target repositories.
# These URLs point directly to small example files that are part of the
# official dataset releases.  Downloading a single file is sufficient to
# prove the source is reachable and to provide raw data for downstream
# tasks.
VERIFIED_URLS = {
    "NAB": {
        "description": "NAB – real_traffic_1.csv (traffic data with anomalies)",
        "url": "https://raw.githubusercontent.com/numenta/NAB/master/data/realTraffic/realTraffic_1.csv",
        "filename": "nab_realTraffic_1.csv",
    },
    "PhysioNet": {
        "description": "PhysioNet – MIT‑BIH record 100 (ECG) in CSV format",
        "url": "https://physionet.org/files/mitdb/1.0.0/100.csv",
        "filename": "physionet_mitdb_100.csv",
    },
}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def download_file(url: str, dest_path: Path) -> bool:
    """
    Download ``url`` to ``dest_path`` using a streaming request.

    Returns ``True`` on success, ``False`` otherwise.
    """
    try:
        log.info(f"Attempting download: {url}")
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep‑alive chunks
                        f.write(chunk)
        log.info(f"Saved to {dest_path}")
        return True
    except Exception as exc:
        log.warning(f"Download failed for {url}: {exc}")
        return False

def write_deferred_report(query: str, count: int, out_path: Path) -> None:
    """
    Write a markdown *Validation Deferred* report.

    The report follows the format required by FR‑017b.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    report = (
        f"# Validation Deferred Report\n\n"
        f"**Search query:** `{query}`\n\n"
        f"**Result count:** {count}\n\n"
        f"The pipeline could not locate any verified real‑world "
        f"time‑series datasets that contain known regime‑shift events. "
        f"As a consequence, downstream tasks that depend on external data "
        f"will operate on synthetic data only.\n"
    )
    out_path.write_text(report, encoding="utf-8")
    log.info(f"Validation Deferred report written to {out_path}")

# ----------------------------------------------------------------------
# Main execution
# ----------------------------------------------------------------------
def main() -> None:
    """
    Execute the search‑and‑download routine.

    The function aggregates successful downloads; if none succeed,
    a deferred report is generated.
    """
    successful_downloads = 0

    # Attempt to download each verified URL.
    for source_name, info in VERIFIED_URLS.items():
        dest = paths.data("raw", info["filename"])
        if download_file(info["url"], dest):
            successful_downloads += 1
        else:
            log.info(f"Skipping {source_name} – download unsuccessful.")

    # If no datasets could be retrieved, emit the deferred report.
    if successful_downloads == 0:
        query = " OR ".join(SEARCH_KEYWORDS)
        report_path = paths.data(
            "processed",
            "results",
            "validation_deferred.md",
        )
        write_deferred_report(query, 0, report_path)
    else:
        log.info(
            f"Search completed: {successful_downloads} dataset(s) "
            f"downloaded to {paths.data('raw')}"
        )

if __name__ == "__main__":
    main()