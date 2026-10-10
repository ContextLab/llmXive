"""
Fetch real Cochrane meta-analysis base data for the heterogeneity study.

Primary source (per T001): Zenodo record for DOI 10.5281/zenodo.10286623,
accessed via the Zenodo REST API (https://zenodo.org/api/records/10286623).
The record's files are downloaded and the first file with a valid
meta-analysis structure (effect size + standard error columns, >= 5 rows)
is saved as data/raw/cochrane_base.csv.

If the fetch fails, this script MUST raise a FileNotFoundError.
The pipeline's fallback to a verified synthetic base is handled elsewhere
(e.g., via `code/main.py` or `code/scripts/generate_synthetic_base.py`).
No silent substitution of synthetic data occurs here.
"""
import csv
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
import zipfile
import io

# Ensure the script directory is on the import path for sibling modules
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

DATA_DIR = Path("data/raw")
OUTPUT_FILE = DATA_DIR / "cochrane_base.csv"

# Zenodo identifiers
ZENODO_RECORD_API = "https://zenodo.org/api/records/10286623"
ZENODO_DOI = "10.5281/zenodo.10286623"

def _download(url: str, timeout: int = 60) -> bytes:
    """Download raw bytes from a URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "llmXive-PROJ-417/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def list_zenodo_files() -> list[tuple[str, str]]:
    """
    Retrieve a list of (filename, download_url) tuples from the Zenodo record.

    Raises:
        FileNotFoundError: If the record cannot be fetched or parsed.
    """
    try:
        raw = _download(ZENODO_RECORD_API)
        record = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: could not read Zenodo record for "
            f"DOI {ZENODO_DOI} at {ZENODO_RECORD_API}: {exc}"
        ) from exc

    files = record.get("files") or []
    out: list[tuple[str, str]] = []
    for f in files:
        name = f.get("key") or f.get("filename")
        link = (f.get("links") or {}).get("self")
        if name and link:
            out.append((name, link))

    if not out:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: Zenodo record for DOI {ZENODO_DOI} "
            "exposes no downloadable files."
        )
    return out

def _validate_csv_bytes(content: bytes) -> bool:
    """
    Validate CSV content from bytes (e.g., extracted from a zip file).
    """
    try:
        # Decode using utf-8-sig to handle possible BOM
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        headers = reader.fieldnames
        if not headers:
            return False
        headers_lower = [h.lower().strip() for h in headers]

        # Accept common column names
        has_effect = any(
            col in headers_lower
            for col in ("effect_size", "yi", "estimate", "effect", "log_or")
        )
        has_se = any(
            col in headers_lower
            for col in ("standard_error", "sei", "se", "std_err")
        )
        if not (has_effect and has_se):
            return False

        row_count = sum(1 for _ in reader)
        return row_count >= 5
    except Exception:
        return False

def validate_csv_structure(path: Path) -> bool:
    """
    Verify that a CSV file on disk contains at least one effect‑size column and one
    standard‑error column, and that it has at least five data rows.
    """
    try:
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if not headers:
                return False
            headers_lower = [h.lower().strip() for h in headers]

            has_effect = any(
                col in headers_lower
                for col in ("effect_size", "yi", "estimate", "effect", "log_or")
            )
            has_se = any(
                col in headers_lower
                for col in ("standard_error", "sei", "se", "std_err")
            )
            if not (has_effect and has_se):
                return False

            row_count = sum(1 for _ in reader)
            return row_count >= 5
    except Exception:
        return False

def fetch_real_data() -> Path:
    """
    Attempt to download and validate a Cochrane dataset from Zenodo.

    Returns:
        Path: Path to the validated CSV file.

    Raises:
        FileNotFoundError: If no suitable file can be retrieved or validated.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Attempting to fetch real data from Zenodo DOI {ZENODO_DOI} ...")
    candidates = list_zenodo_files()
    last_error = None

    for name, url in candidates:
        try:
            raw = _download(url)

            # If the file is a zip archive, inspect its members
            if name.lower().endswith(".zip"):
                with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                    for inner_name in zf.namelist():
                        if not inner_name.lower().endswith(".csv"):
                            continue
                        inner_bytes = zf.read(inner_name)
                        if _validate_csv_bytes(inner_bytes):
                            OUTPUT_FILE.write_bytes(inner_bytes)
                            print(
                                f"Successfully extracted and validated '{inner_name}' "
                                f"from zip '{name}' → {OUTPUT_FILE}"
                            )
                            return OUTPUT_FILE
                        else:
                            last_error = (
                                f"inner file '{inner_name}' in zip '{name}' "
                                "failed validation"
                            )
                continue  # continue to next candidate if zip processed

            # Otherwise treat as plain CSV
            tmp_path = OUTPUT_FILE.with_suffix(".tmp")
            tmp_path.write_bytes(raw)

            if validate_csv_structure(tmp_path):
                tmp_path.replace(OUTPUT_FILE)
                print(f"Successfully fetched and validated '{name}' → {OUTPUT_FILE}")
                return OUTPUT_FILE

            tmp_path.unlink(missing_ok=True)
            last_error = f"file '{name}' failed structure validation"
        except Exception as exc:
            last_error = f"file '{name}': {exc}"

    raise FileNotFoundError(
        f"REAL_DATA_FETCH_FAILED: no usable file on Zenodo record "
        f"{ZENODO_DOI} (last error: {last_error})"
    )

def main() -> int:
    """
    Entry point for the script.

    Returns:
        int: Exit code (0 on success, non‑zero on failure).
    """
    print("=" * 60)
    print("FETCHING COCHRANE DATA")
    print("=" * 60)
    # Propagate any FileNotFoundError so the caller can handle it.
    fetch_real_data()
    print("SUCCESS: Real Cochrane data fetched and validated.")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())