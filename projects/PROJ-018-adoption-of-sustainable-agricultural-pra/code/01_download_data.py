"""Data download script with synthetic fallback and variable validation.

This script attempts to fetch real survey data; if unavailable, it creates a small
synthetic dataset that matches the required schema. After data creation, it validates
that all required columns are present and logs any gaps.
"""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

import pandas as pd

from .config import get_config, set_random_seed
from .logging_config import log_operation, update_log_section

# Define required columns for the survey
REQUIRED_COLUMNS = [
    "age",
    "education",
    "farm_size",
    "credit",
    "adoption",
    "engagement_membership",
    "engagement_extension",
    "engagement_collective_action",
    "engagement_knowledge_exchange",
]


class DataFetchError(RuntimeError):
    """Raised when real data cannot be fetched."""


@log_operation("download_data")
def download_real_data(output_path: Path) -> bool:
    """
    Placeholder for real data fetch. Returns False to indicate failure,
    triggering synthetic fallback.
    """
    # In a real implementation this would contact an API.
    return False


@log_operation("generate_synthetic_fallback")
def generate_synthetic_fallback(output_path: Path) -> None:
    """Create a tiny synthetic dataset with deterministic values."""
    random.seed(0)  # deterministic for reproducibility
    rows = []
    for i in range(10):
        rows.append(
            {
                "age": random.randint(18, 70),
                "education": random.choice(["none", "primary", "secondary", "tertiary"]),
                "farm_size": round(random.uniform(0.1, 10.0), 2),
                "credit": random.choice([0, 1]),
                "adoption": random.choice([0, 1]),
                "engagement_membership": random.choice([0, 1]),
                "engagement_extension": random.choice([0, 1]),
                "engagement_collective_action": random.choice([0, 1]),
                "engagement_knowledge_exchange": random.choice([0, 1]),
            }
        )
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    # Log provenance
    update_log_section(
        "data_source_metadata",
        {"source": "synthetic_fallback", "record_count": len(rows)},
        log_path=str(get_config("modeling_log_path", "modeling_log.yaml")),
    )


def _validate_columns(df: pd.DataFrame) -> list[str]:
    """Return a list of missing required columns."""
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    return missing


@log_operation("validate_and_log_gaps")
def _log_column_gaps(missing_columns: list[str]) -> None:
    """Log any missing column gaps to the modeling log."""
    if missing_columns:
        update_log_section(
            "variable_gaps",
            {"missing_columns": missing_columns},
            log_path=str(get_config("modeling_log_path", "modeling_log.yaml")),
        )


@log_operation("main_download")
def main() -> None:
    parser = argparse.ArgumentParser(description="Download survey data or generate synthetic fallback.")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Force synthetic data generation even if real download succeeds.",
    )
    args = parser.parse_args()

    # Ensure reproducibility
    set_random_seed(int(get_config("random_seed", 42)))

    raw_dir = Path(get_config("raw_data_path", "data/raw"))
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_path = raw_dir / get_config("raw_data_filename", "survey_data.csv")

    success = False
    if not args.synthetic:
        try:
            success = download_real_data(output_path)
        except Exception as exc:
            raise DataFetchError(f"Failed to fetch real data: {exc}") from exc

    if not success:
        generate_synthetic_fallback(output_path)

    # Load and validate columns
    df = pd.read_csv(output_path)
    missing = _validate_columns(df)
    _log_column_gaps(missing)

    if missing:
        print(f"Warning: missing required columns: {missing}")
    else:
        print("All required columns are present.")

    print(f"Data written to {output_path}")


if __name__ == "__main__":
    main()