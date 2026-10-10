"""
Fetch real Cochrane meta-analysis base data for the heterogeneity study.

Primary source (per T001): Zenodo record for DOI 10.5281/zenodo.10286623,
accessed via the Zenodo REST API (https://zenodo.org/api/records/10286623).
The record's files are downloaded and the first file with a valid
meta-analysis structure (effect size + standard error columns, >= 5 rows)
is saved as data/raw/cochrane_base.csv.

Fallback: the verified synthetic base (mu=0.0, sigma=1.0, N=20) with
parameters cited from Jackson et al. (2010), written to
data/raw/cochrane_base_synthetic.csv. This fallback is the documented
T001 path; if even the fallback fails, the script exits non-zero.

The real-fetch path raises FileNotFoundError on any failure (never a
silent substitution).
"""
import csv
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_synthetic_base import generate_synthetic_base_data, save_to_csv as save_synthetic_csv

DATA_DIR = Path("data/raw")
OUTPUT_FILE = DATA_DIR / "cochrane_base.csv"
SYNTHETIC_FILE = DATA_DIR / "cochrane_base_synthetic.csv"

# T001 primary source: Zenodo DOI 10.5281/zenodo.10286623
ZENODO_RECORD_API = "https://zenodo.org/api/records/10286623"
ZENODO_DOI = "10.5281/zenodo.10286623"

def _download(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "llmXive-PROJ-417/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()

def list_zenodo_files() -> list:
    """List downloadable files on the Zenodo record for the DOI.

    Returns a list of (filename, download_url) tuples.
    Raises FileNotFoundError if the record cannot be fetched or parsed.
    """
    try:
        raw = _download(ZENODO_RECORD_API)
        record = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise FileNotFoundError(
            f"REAL_DATA_FETCH_FAILED: could not read Zenodo record for "
            f"DOI {ZENODO_DOI} at {ZENODO_RECORD_API}: {exc}"
        )
    files = record.get("files") or []
    out = []
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

def validate_csv_structure(path: Path) -> bool:
    """Validate that the file has effect-size and standard-error columns."""
    try:
        with open(path, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if not headers:
                return False
            headers_lower = [h.lower().strip() for h in headers]
            found_effect = any(
                c in headers_lower for c in ("effect_size", "yi", "estimate", "effect", "log_or")
            )
            found_se = any(
                c in headers_lower for c in ("standard_error", "sei", "se", "std_err")
            )
            if not (found_effect and found_se):
                return False
            return sum(1 for _ in reader) >= 5
    except Exception:
        return False

def fetch_real_data() -> Path:
    """Fetch real data from Zenodo DOI 10.5281/zenodo.10286623.

    Raises FileNotFoundError on any failure (loud failure, no silent
    substitution).
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Attempting to fetch real data from Zenodo DOI {ZENODO_DOI} ...")
    candidates = list_zenodo_files()
    last_error = None
    for name, url in candidates:
        try:
            raw = _download(url)
            tmp = OUTPUT_FILE.with_suffix(".tmp")
            tmp.write_bytes(raw)
            if validate_csv_structure(tmp):
                tmp.replace(OUTPUT_FILE)
                print(f"Successfully fetched and validated '{name}' -> {OUTPUT_FILE}")
                return OUTPUT_FILE
            tmp.unlink(missing_ok=True)
            last_error = f"file '{name}' failed structure validation"
        except Exception as exc:
            last_error = f"file '{name}': {exc}"
    raise FileNotFoundError(
        f"REAL_DATA_FETCH_FAILED: no usable file on Zenodo record "
        f"{ZENODO_DOI} (last error: {last_error})"
    )

def main() -> int:
    print("=" * 60)
    print("FETCHING COCHRANE DATA")
    print("=" * 60)
    try:
        fetch_real_data()
        print("SUCCESS: Real Cochrane data fetched and validated.")
    except FileNotFoundError as e:
        print(f"WARNING: {e}")
        print(
            "Falling back to verified synthetic base "
            "(mu=0.0, sigma=1.0, N=20; Jackson et al., 2010)..."
        )
        try:
            data = generate_synthetic_base_data(n_studies=20)
            save_synthetic_csv(data, SYNTHETIC_FILE)
            print(f"SUCCESS: Synthetic base data generated at {SYNTHETIC_FILE}")
        except Exception as se:
            print(f"CRITICAL ERROR: Fallback failed: {se}")
            return 1
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
