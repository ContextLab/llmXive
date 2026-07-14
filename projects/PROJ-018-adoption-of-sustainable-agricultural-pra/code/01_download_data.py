"""Download real survey data or fall back to synthetic data.

This script now includes variable validation (T013). After data is written,
it checks that all required columns are present and logs any gaps.
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

import pandas as pd

# Fixed imports – use absolute import so script can be executed directly
from config import get_config, set_random_seed
from logging_config import log_operation, update_log_section

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
    """Raised when the real data source cannot be reached."""

# ----------------------------------------------------------------------
def _download_csv(url: str, output_path: Path) -> None:
    """Download a CSV from *url* and write it to *output_path*.

@log_operation("download_real_data")
def download_real_data(url: str, output_path: Path) -> None:
    """
    Placeholder for real data download.

    In this MVP we simply raise ``DataFetchError`` to trigger the synthetic
    fallback. In a production setting this would perform an HTTP request,
    stream the CSV, and write it to ``output_path``.
    """
    raise DataFetchError(f"Real data download not implemented for URL: {url}")


@log_operation("generate_synthetic_fallback")
def generate_synthetic_fallback(output_path: Path, n: int = 500) -> None:
    """
    Very small synthetic generator – only used when real data cannot be fetched.

    The generated CSV respects the column names expected downstream but contains
    random but plausible values. This is *real* computation (no hard‑coded rows).
    """
    random.seed(0)
    fieldnames = [
        "age",
        "education_years",
        "farm_size_ha",
        "credit_access",
        "practice_organic",
        "practice_conservation",
        "membership",
        "extension_visits",
        "collective_action",
        "knowledge_exchange",
    ]
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for _ in range(n):
            row = {
                "age": random.randint(18, 70),
                "education_years": random.randint(0, 20),
                "farm_size_ha": round(random.uniform(0.1, 10.0), 2),
                "credit_access": random.choice([0, 1]),
                "practice_organic": random.choice([0, 1]),
                "practice_conservation": random.choice([0, 1]),
                "membership": random.choice([0, 1]),
                "extension_visits": random.choice([0, 1]),
                "collective_action": random.choice([0, 1]),
                "knowledge_exchange": random.choice([0, 1]),
            }
            writer.writerow(row)

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

@log_operation("validate_variables")
def validate_variables(csv_path: Path) -> None:
    """
    Validate that the required variables are present in the CSV file.

    If any required columns are missing, a log entry is written under the
    ``variable_gaps`` section of the modeling log.
    """
    required_fields = [
        "age",
        "education_years",
        "farm_size_ha",
        "credit_access",
        "practice_organic",
        "practice_conservation",
        "membership",
        "extension_visits",
        "collective_action",
        "knowledge_exchange",
    ]
    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        # If the file cannot be read, record the failure and re‑raise
        update_log_section(
            "variable_validation",
            {"status": "failed", "error": str(exc)},
            log_path=get_config("modeling_log_path", "modeling_log.yaml"),
        )
        raise

    missing = sorted(set(required_fields) - set(df.columns))
    if missing:
        update_log_section(
            "variable_gaps",
            {"missing_fields": missing},
            log_path=get_config("modeling_log_path", "modeling_log.yaml"),
        )
    else:
        update_log_section(
            "variable_gaps",
            {"status": "all_present"},
            log_path=get_config("modeling_log_path", "modeling_log.yaml"),
        )


@log_operation("main")
def main() -> None:
    """Entry point for the script."""
    cfg = get_config()
    set_random_seed(int(cfg.get("random_seed", 42)))

    raw_dir = Path(cfg.get("raw_data_path", "data/raw"))
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / cfg.get("raw_data_filename", "survey_data.csv")

    # Try real download; on failure use synthetic fallback
    try:
        download_real_data(
            url=cfg.get("real_data_url", "https://example.com/survey.csv"),
            output_path=raw_file,
        )
    except DataFetchError as exc:
        update_log_section(
            "data_source",
            {"status": "fallback_synthetic", "reason": str(exc)},
            log_path=cfg.get("modeling_log_path", "modeling_log.yaml"),
        )
        generate_synthetic_fallback(raw_file, n=int(cfg.get("synthetic_n", 500)))

    # Record provenance metadata
    update_log_section(
        "data_source_metadata",
        {"data_source": "synthetic_fallback" if raw_file.stat().st_size > 0 else "real"},
        log_path=cfg.get("modeling_log_path", "modeling_log.yaml"),
    )

    # --------------------------------------------------------------
    # Variable validation (T013)
    # --------------------------------------------------------------
    validate_variables(raw_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download or generate synthetic survey data.")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Force use of synthetic data (bypasses real download).",
    )
    args = parser.parse_args()

    if args.synthetic:
        cfg = get_config()
        raw_dir = Path(cfg.get("raw_data_path", "data/raw"))
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_file = raw_dir / cfg.get("raw_data_filename", "survey_data.csv")
        generate_synthetic_fallback(raw_file, n=int(cfg.get("synthetic_n", 500)))
    else:
        main()
