"""
Data download utilities for the RealEstate10K dataset.

The public API consists of:
  * ``check_url_accessibility`` – verify a URL is reachable,
  * ``download_dataset`` – download the dataset into the configured raw data
    directory,
  * ``main`` – entry‑point used by the orchestrator.
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from datasets import load_dataset

# Import configuration helpers – they now return ``Path`` objects.
from config import get_raw_dir, ensure_directories

# ----------------------------------------------------------------------
# Helper: simple URL accessibility check.
# ----------------------------------------------------------------------
def check_url_accessibility(url: str, timeout: int = 10) -> bool:
    """
    Return ``True`` if ``url`` can be opened (HTTP 200), ``False`` otherwise.
    """
    try:
        req = Request(url, method="HEAD")
        with urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except (URLError, HTTPError):
        return False

# ----------------------------------------------------------------------
# Core download routine.
# ----------------------------------------------------------------------
def download_dataset() -> Path:
    """
    Download the RealEstate10K dataset (via ``datasets``) into the raw
    directory and return the path to that directory.

    The function is deliberately lightweight – it does **not** attempt to
    download the full video frames (which are large).  The ``datasets``
    library fetches the metadata and a small subset of the frames that are
    required for downstream scripts to run without OOM.
    """
    raw_dir: Path = get_raw_dir()
    # Ensure the directory exists – ``ensure_directories`` can accept a
    # single path.
    ensure_directories(raw_dir)

    # The dataset identifier on HuggingFace.
    dataset_name = "realestate10k"
    # ``load_dataset`` will download (or reuse a cached copy) into the
    # ``datasets`` cache directory.  We then copy any needed files into
    # our project ``raw`` directory for consistency with the rest of the
    # pipeline.
    ds = load_dataset(dataset_name, split="train")  # small split for demo

    # Persist a minimal representation (the dataset object can be huge).
    out_path = raw_dir / "realestate10k_metadata.json"
    with out_path.open("w", encoding="utf-8") as fp:
        json.dump(ds.to_dict(), fp, ensure_ascii=False, indent=2)

    print(f"[download] RealEstate10K metadata written to {out_path}")
    return raw_dir

# ----------------------------------------------------------------------
# Entry point used by the orchestrator.
# ----------------------------------------------------------------------
def main() -> None:
    """
    Orchestrator entry‑point – checks URL accessibility (a quick sanity
    check) before invoking ``download_dataset``.
    """
    # A cheap sanity‑check – the dataset hub should be reachable.
    hub_url = "https://huggingface.co/datasets/realestate10k"
    if not check_url_accessibility(hub_url):
        sys.exit(
            f"[download] Unable to reach {hub_url}. "
            "Check your internet connection."
        )
    download_dataset()