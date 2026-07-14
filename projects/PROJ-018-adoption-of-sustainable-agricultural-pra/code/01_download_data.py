"""Data acquisition script.

Attempts to download real survey data; if unavailable, falls back to a
minimal synthetic dataset generated on‑the‑fly. The script writes the raw
CSV to ``data/raw/survey_data.csv`` and records provenance in
``data/metadata.yaml`` and ``modeling_log.yaml``.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import List

import requests

from config import (
    get_raw_data_path,
    get_config,
    load_config_from_yaml,
    set_random_seed,
    get_modeling_log_path,
)
from logging_config import log_operation, update_log_section

# ----------------------------------------------------------------------
class DataFetchError(RuntimeError):
    """Raised when external data fetching fails."""
    pass

# ----------------------------------------------------------------------
def _download_csv(url: str, output_path: Path) -> None:
    """Download a CSV from *url* and write it to *output_path*.

    Raises:
        DataFetchError: if the request fails or the content is not CSV.
    """
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        raise DataFetchError(f"Failed to download CSV from {url}: {exc}") from exc

    # Write the raw content to file (assume UTF‑8)
    output_path.write_bytes(resp.content)

# ----------------------------------------------------------------------
def fetch_real_data(output_path: Path) -> None:
    """Attempt to fetch a real survey dataset.

    The URL chosen is a small public CSV suitable for demonstration.
    In a production setting this would be the World Bank LSMS / FAO FIES
    endpoint.
    """
    # Example public CSV – replace with the real source when available.
    example_url = (
        "https://people.sc.fsu.edu/~jburkardt/data/csv/hw_200.csv"
    )
    _download_csv(example_url, output_path)

# ----------------------------------------------------------------------
def generate_fallback_synthetic_data(output_path: Path, n: int = 100) -> None:
    """Create a tiny synthetic dataset with the required columns."""
    random.seed(42)
    headers = [
        "age",
        "education",
        "farm_size",
        "credit",
        "membership",
        "extension",
        "collective_action",
        "knowledge_exchange",
        "practice_organic",
        "practice_conservation",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for _ in range(n):
            row = [
                random.randint(18, 70),               # age
                random.randint(0, 20),                # education (years)
                round(random.uniform(0.1, 10.0), 2),   # farm_size (ha)
                random.choice([0, 1]),                # credit access
                random.choice([0, 1]),                # membership
                random.choice([0, 1]),                # extension
                random.choice([0, 1]),                # collective_action
                random.choice([0, 1]),                # knowledge_exchange
                random.choice([0, 1]),                # practice_organic
                random.choice([0, 1]),                # practice_conservation
            ]
            writer.writerow(row)

# ----------------------------------------------------------------------
def _record_metadata(source: str, csv_path: Path) -> None:
    """Write provenance metadata to ``data/metadata.yaml``."""
    # Compute record count (exclude header)
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        record_count = sum(1 for _ in reader) - 1  # header row

    metadata = {
        "data_source": source,
        "fetch_timestamp": datetime.utcnow().isoformat(),
        "notes": (
            "Synthetic data used as fallback due to real data source "
            "inaccessibility (FR-001, FR-002)" if source == "synthetic_fallback"
            else "Real data successfully downloaded"
        ),
        "record_count": record_count,
    }

    metadata_path = Path("data") / "metadata.yaml"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2))

# ----------------------------------------------------------------------
@log_operation
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download survey data (synthetic fallback if needed)."
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Force use of synthetic data (bypasses real download).",
    )
    args = parser.parse_args()

    raw_dir = get_raw_data_path()
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "survey_data.csv"

    # ------------------------------------------------------------------
    # Seed handling – ensure reproducibility for the synthetic path.
    # ------------------------------------------------------------------
    cfg = get_config()
    seed = cfg.get("random_seed", 42)
    set_random_seed(seed)

    if args.synthetic:
        generate_fallback_synthetic_data(raw_path)
        source_label = "synthetic_fallback"
        update_log_section(
            "data_acquisition",
            {"source": source_label, "records": raw_path.stat().st_size},
        )
    else:
        try:
            fetch_real_data(raw_path)
            source_label = "real_download"
            update_log_section(
                "data_acquisition",
                {"source": source_label, "records": raw_path.stat().st_size},
            )
        except DataFetchError as exc:
            # Log the limitation and fall back to synthetic data.
            update_log_section(
                "data_acquisition",
                {
                    "source": "synthetic_fallback",
                    "reason": str(exc),
                    "records": 0,
                },
            )
            generate_fallback_synthetic_data(raw_path)

            source_label = "synthetic_fallback"

    # Write provenance metadata for downstream users.
    _record_metadata(source_label, raw_path)

    # Final log entry (the decorator already logged the call).
    print(f"Data written to {raw_path}", file=sys.stderr)
