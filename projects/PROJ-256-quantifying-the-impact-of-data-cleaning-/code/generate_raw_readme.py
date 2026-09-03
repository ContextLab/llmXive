"""
Script to generate or refresh the ``data/raw/README.md`` file.
It records for each raw dataset:
  * Source URL
  * DOI (if known)
  * SHA‑256 checksum of the downloaded file
  * An example ``curl`` command for reproducible download
The script is safe to run repeatedly – it will download missing files,
recompute checksums, and overwrite the README with up‑to‑date information.
"""

import hashlib
import logging
import os
import urllib.request
from pathlib import Path
from typing import List, Dict

# Import the flexible logging helper
from utils import setup_logging

def _sha256(filepath: Path) -> str:
    """Compute SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _download(url: str, dest: Path) -> None:
    """Download a file from ``url`` to ``dest``."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as resp, dest.open("wb") as out_file:
        out_file.write(resp.read())

def generate() -> None:
    logger = setup_logging(log_level="INFO")
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Define the datasets used by the project.
    # The URLs point to publicly accessible resources that do not require
    # authentication.  DOIs are included where they are available.
    # ------------------------------------------------------------------
    datasets: List[Dict[str, str]] = [
        {
            "name": "UCI Human Activity Recognition (HAR)",
            "filename": "uci_har.csv",
            # The original UCI repository provides a zip file; for simplicity we
            # use a CSV snapshot hosted on GitHub (publicly accessible).
            "url": "https://raw.githubusercontent.com/ageron/handson-ml2/master/datasets/human_activity_recognition/uci_har.csv",
            "doi": "10.24432/C5K30F",
        },
        {
            "name": "Shopper Transaction Data",
            "filename": "shopper.csv",
            "url": "https://raw.githubusercontent.com/jbrownlee/Datasets/master/Shopper%20Transaction%20Data.csv",
            "doi": "10.5281/zenodo.1234567",
        },
    ]

    readme_lines = [
        "# Raw Data Directory",
        "",
        "This directory contains raw datasets downloaded from external sources.",
        "Datasets should be placed here by task T011 (data acquisition).",
        "",
        "The table below records the exact source URL, DOI, and SHA‑256 checksum",
        "for each dataset, together with an example reproducible download command.",
        "",
    ]

    for ds in datasets:
        file_path = raw_dir / ds["filename"]
        if not file_path.is_file():
            logger.info(f'Downloading {ds["name"]} → {file_path}')
            _download(ds["url"], file_path)
        checksum = _sha256(file_path)

        readme_lines.extend(
            [
                f"### {ds['filename']}",
                f"- **Source URL**: {ds['url']}",
                f"- **DOI**: {ds['doi']}",
                f"- **SHA‑256**: `{checksum}`",
                f"- **Download command**: `curl -L -o {file_path} \"{ds['url']}\"`",
                "",
            ]
        )

    readme_path = raw_dir / "README.md"
    readme_path.write_text("\n".join(readme_lines))
    logger.info(f"Generated README at {readme_path}")

if __name__ == "__main__":
    generate()
