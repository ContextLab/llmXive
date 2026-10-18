"""
Fetch a verified meta‑analysis dataset from OpenML (ID 4210) and store it as the
canonical base file for the project.

The script:
1. Uses scikit‑learn's ``fetch_openml`` utility to download the dataset.
2. Validates that the CSV contains at least one effect‑size column and one
   standard‑error column and that it has ≥ 5 data rows.
3. Writes the validated CSV to ``data/raw/cochrane_base.csv``.
4. Raises ``FileNotFoundError`` on any failure (no silent fallback).

This fulfills T001’s requirement that the script exit with status 0,
create the declared file, and raise on download failure.
"""
import csv
import io
import json
import sys
from pathlib import Path

# scikit‑learn is part of the base environment (no extra dependency needed)
from sklearn.datasets import fetch_openml

# llmxive utility for standard project paths
from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
OPENML_DATASET_ID = 4210
OUTPUT_PATH = paths.data("raw", "cochrane_base.csv")
MIN_ROWS = 5

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _list_effect_se_columns(headers: list[str]) -> tuple[bool, bool]:
    """Return flags indicating presence of effect‑size and SE columns."""
    lowered = [h.lower().strip() for h in headers]
    has_effect = any(
        col in lowered
        for col in ("effect_size", "yi", "estimate", "effect", "log_or")
    )
    has_se = any(
        col in lowered
        for col in ("standard_error", "sei", "se", "std_err")
    )
    return has_effect, has_se

def _validate_csv_bytes(content: bytes) -> bool:
    """Validate CSV content (as bytes) for required structure."""
    try:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        headers = reader.fieldnames
        if not headers:
            return False
        has_effect, has_se = _list_effect_se_columns(headers)
        if not (has_effect and has_se):
            return False
        row_count = sum(1 for _ in reader)
        return row_count >= MIN_ROWS
    except Exception:
        return False

# ----------------------------------------------------------------------
# Main fetching logic
# ----------------------------------------------------------------------
def fetch_openml_dataset() -> Path:
    """
    Download and validate the OpenML dataset, returning the path to the
    verified CSV file.

    Raises:
        FileNotFoundError: If the dataset cannot be retrieved or fails
                           validation.
    """
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"Fetching OpenML dataset ID {OPENML_DATASET_ID} ...")

    # Use scikit‑learn's fetch_openml which handles the OpenML API internally
    try:
        dataset = fetch_openml(data_id=OPENML_DATASET_ID, as_frame=True, parser="auto")
    except Exception as exc:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: unable to download dataset ID {OPENML_DATASET_ID}: {exc}"
        ) from exc

    # ``dataset`` may be a Bunch; the DataFrame is in ``data`` attribute
    df = getattr(dataset, "frame", None) or getattr(dataset, "data", None)
    if df is None:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: fetched object does not contain a DataFrame."
        )

    # Convert DataFrame to CSV bytes for validation
    csv_bytes = df.to_csv(index=False).encode("utf-8")

    if not _validate_csv_bytes(csv_bytes):
        raise FileNotFoundError(
            "REAL_DATA_FETCH_FAILED: downloaded file failed CSV validation."
        )

    # Write validated CSV to the canonical location
    OUTPUT_PATH.write_bytes(csv_bytes)
    print(f"Downloaded and validated CSV → {OUTPUT_PATH}")
    return OUTPUT_PATH

def main() -> int:
    """
    CLI entry point.

    Returns:
        int: Exit code (0 on success, non‑zero on failure).
    """
    print("=" * 60)
    print("FETCHING OPENML DATASET")
    print("=" * 60)
    try:
        fetch_openml_dataset()
        print("SUCCESS: Base dataset written to", OUTPUT_PATH)
        print("=" * 60)
        return 0
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())