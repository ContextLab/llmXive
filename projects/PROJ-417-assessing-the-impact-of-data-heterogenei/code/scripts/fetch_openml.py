"""
Fetch a verified meta‑analysis dataset from OpenML (ID 4210) and store it as the
canonical base file for the project.

The script:
1. Queries the OpenML API for dataset 4210.
2. Retrieves the download URL from the JSON description.
3. Downloads the file (CSV or ZIP containing a CSV).
4. Validates that the CSV contains at least one effect‑size column and one
   standard‑error column and that it has ≥ 5 data rows.
5. Writes the validated CSV to ``data/raw/cochrane_base.csv``.
6. Raises ``FileNotFoundError`` on any failure (no silent fallback).

This fulfills T001’s requirement that the script exit with status 0,
create the declared file, and raise on download failure.
"""
import csv
import io
import json
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

# llmxive utility for standard project paths
from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
OPENML_DATASET_ID = 4210
OPENML_API_URL = f"https://www.openml.org/api/v1/json/data/{OPENML_DATASET_ID}"
OUTPUT_PATH = paths.data("raw", "cochrane_base.csv")
MIN_ROWS = 5

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _download(url: str, timeout: int = 60) -> bytes:
    """Download raw bytes from ``url``."""
    req = urllib.request.Request(
        url, headers={"User-Agent": "llmxive-PROJ-417/1.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

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

def _validate_csv_file(path: Path) -> bool:
    """Validate a CSV file on disk."""
    try:
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
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

    # Step 1: Get dataset description JSON
    try:
        raw_json = _download(OPENML_API_URL)
        description = json.loads(raw_json.decode("utf-8"))
    except Exception as exc:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: unable to retrieve OpenML metadata for "
            f"dataset {OPENML_DATASET_ID}: {exc}"
        ) from exc

    # Extract the download URL
    try:
        download_url = description["data_set_description"]["url"]
    except Exception as exc:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: OpenML metadata missing 'url' field: {exc}"
        ) from exc

    # Step 2: Download the file (could be CSV or ZIP)
    try:
        raw_data = _download(download_url)
    except Exception as exc:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: unable to download dataset file from "
            f"{download_url}: {exc}"
        ) from exc

    # Step 3: Determine if we received a zip archive
    if download_url.lower().endswith(".zip") or zipfile.is_zipfile(
        io.BytesIO(raw_data)
    ):
        # Inspect zip members for a CSV that validates
        with zipfile.ZipFile(io.BytesIO(raw_data)) as zf:
            for inner_name in zf.namelist():
                if not inner_name.lower().endswith(".csv"):
                    continue
                inner_bytes = zf.read(inner_name)
                if _validate_csv_bytes(inner_bytes):
                    OUTPUT_PATH.write_bytes(inner_bytes)
                    print(
                        f"Extracted and validated '{inner_name}' from zip → "
                        f"{OUTPUT_PATH}"
                    )
                    return OUTPUT_PATH
            raise FileNotFoundError(
                "REAL_DATA_FETCH_FAILED: no CSV inside the zip archive passed validation."
            )
    else:
        # Assume plain CSV
        if _validate_csv_bytes(raw_data):
            OUTPUT_PATH.write_bytes(raw_data)
            print(f"Downloaded and validated CSV → {OUTPUT_PATH}")
            return OUTPUT_PATH
        else:
            raise FileNotFoundError(
                "REAL_DATA_FETCH_FAILED: downloaded file failed CSV validation."
            )

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