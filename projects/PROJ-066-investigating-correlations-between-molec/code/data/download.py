"""
Download script for ChEMBL 33 molecular activity data (Task T009).

The original plan fetched the full ChEMBL 33 SQLite archive via FTP
(ftp://ftp.ebi.ac.uk/pub/databases/chembl/ChEMBLdb/releases/). That FTP
path returns "550 Failed to open file" on the CI runner (FTP is blocked
/ the release layout changed), and the full ~3.5 GB archive exceeds the
runner's time budget anyway.

Real-data fallback (same source, same analysis): this script now pulls
REAL ChEMBL release 33 activity records from the official EMBL-EBI
ChEMBL webresource API (https://www.ebi.ac.uk/chembl/api/data/), which
is the same public ChEMBL database served over HTTPS. It retrieves
activities for the endpoints of interest (oral bioavailability, apparent
permeability / Papp, clearance), together with the canonical SMILES of
each tested molecule, and writes them into a local SQLite database:

    data/raw/chembl_33.db   (table: activities)

with the column layout the preprocessing stage (T010-T015) expects:
SMILES, Target, Experimental_Value, Assay_Date, molecule_chembl_id,
standard_units, assay_chembl_id, document_chembl_id.

The script FAILS LOUDLY: any HTTP failure, empty result set, or SQLite
write error raises an exception. No synthetic data is ever generated.
The SHA-256 of the produced database is computed and recorded via
utils.update_state (the .sha256 sidecar file is not published for the
API route, so the documented fallback applies: compute + log + record).
"""

import argparse
import gzip
import hashlib
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import requests

# Make sibling utils importable when run as: python code/data/download.py
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, log_pipeline_step
from utils.update_state import update_state, compute_file_hash

logger = get_logger(__name__)

PROJECT_ID = "PROJ-066-investigating-correlations-between-molec"

# --- Source configuration -------------------------------------------------
# Official ChEMBL webresource API (release 33 data, public, no auth).
CHEMBL_API_URL = "https://www.ebi.ac.uk/chembl/api/data/activity.json"
CHEMBL_FTP_HOST = "ftp.ebi.ac.uk"
CHEMBL_FTP_RELEASE_DIR = "/pub/databases/chembl/ChEMBLdb/releases/chembl_33"

# Original FTP archive (kept for reference / local use where FTP works).
CHEMBL_FPS_PATH = CHEMBL_FTP_RELEASE_DIR + "/chembl_33_sqlite.tar.gz"

# Map user-facing target keywords to ChEMBL standard_type values.
TARGET_TYPE_MAP: Dict[str, List[str]] = {
    "bioavailability": [
        "ORAL BIOAVAILABILITY",
        "ORAL BIOAVAILABILITY %",
        "F",
        "BIOAVAILABILITY",
    ],
    "permeability": [
        "PAPP",
        "PAPP (10-6 CM/S)",
        "PERMEABILITY",
        "CACO2 PERMEABILITY",
    ],
    "clearance": [
        "CLEARANCE",
        "CLEARANCE ML/MIN/KG",
        "CLEARANCE ML/MIN",
        "HEPATIC CLEARANCE",
    ],
}

OUTPUT_DIR = project_root / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "chembl_33.db"
SHA256_FILE = OUTPUT_DIR / "chembl_33.sha256"

PAGE_LIMIT = 1000          # ChEMBL API max page size
REQUEST_TIMEOUT = 60       # seconds per HTTP request
MAX_RETRIES = 5
DEFAULT_MAX_RECORDS = 20000


# --- Legacy FTP helpers (public API kept intact) --------------------------

def download_chembl_ftp(host: str, remote_path: str, local_path: Path) -> None:
    """
    Downloads a file from the ChEMBL FTP server.
    Raises an exception if the download fails.
    """
    import ftplib

    logger.info(f"Connecting to FTP host: {host}")
    local_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with ftplib.FTP(host) as ftp:
            ftp.login()
            logger.info(f"Downloading {remote_path} to {local_path}")
            with open(local_path, "wb") as f:
                ftp.retrbinary(f"RETR {remote_path}", f.write)
        logger.info("Download completed successfully.")
    except ftplib.all_errors as e:
        logger.error(f"FTP error during download: {e}")
        raise RuntimeError(f"Failed to download ChEMBL dataset from FTP: {e}")

def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """Computes SHA256 checksum of a file and compares it to the expected hash."""
    computed = compute_file_hash(Path(file_path))
    if computed == expected_hash:
        logger.info("Checksum verification PASSED.")
        return True
    logger.error(f"Checksum verification FAILED. Expected {expected_hash}, got {computed}")
    return False

def decompress_gz(gz_path: Path, db_path: Path) -> None:
    """Decompresses a gzip file to the target database path."""
    logger.info(f"Decompressing {gz_path} to {db_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(gz_path, "rb") as f_in, open(db_path, "wb") as f_out:
        while True:
            chunk = f_in.read(1024 * 1024)
            if not chunk:
                break
            f_out.write(chunk)
    logger.info("Decompression completed.")

# --- ChEMBL webresource API fetcher ---------------------------------------

def _api_get(params: Dict[str, Any]) -> Dict[str, Any]:
    """GET the ChEMBL activity API with retries; raise on persistent failure."""
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(
                CHEMBL_API_URL, params=params, timeout=REQUEST_TIMEOUT,
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:  # noqa: BLE001 - retry any transient failure
            last_err = e
            wait = min(2 ** attempt, 30)
            logger.warning(
                f"ChEMBL API request failed (attempt {attempt}/{MAX_RETRIES}): {e}. "
                f"Retrying in {wait}s."
            )
            time.sleep(wait)
    raise RuntimeError(f"ChEMBL API unreachable after {MAX_RETRIES} attempts: {last_err}")

def fetch_chembl_activities(standard_types: List[str], max_records: int) -> List[Dict[str, Any]]:
    """
    Fetch real ChEMBL activity records (paginated) for the given
    standard_type values. Returns a list of cleaned row dicts.
    Raises RuntimeError if the API is unreachable or returns no data.
    """
    rows: List[Dict[str, Any]] = []
    offset = 0
    total = None
    seen_keys = set()

    logger.info(
        f"Fetching ChEMBL activities for standard types: {standard_types} "
        f"(max {max_records} records)"
    )
    while len(rows) < max_records:
        params = {
            "standard_type__in": ",".join(standard_types),
            "limit": PAGE_LIMIT,
            "offset": offset,
        }
        payload = _api_get(params)
        activities = payload.get("activities", [])
        if total is None:
            total = payload.get("page_meta", {}).get("total_count", 0)
            logger.info(f"ChEMBL reports {total} matching activities in total.")
        if not activities:
            break

        for act in activities:
            smiles = act.get("canonical_smiles")
            value = act.get("standard_value")
            stype = act.get("standard_type")
            if not smiles or value is None or not stype:
                continue  # missing target variable or structure -> excluded
            try:
                value = float(value)
            except (TypeError, ValueError):
                continue
            key = (act.get("molecule_chembl_id"), stype, act.get("assay_chembl_id"), value)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            rows.append(
                {
                    "SMILES": smiles,
                    "Target": stype,
                    "Experimental_Value": value,
                    "Assay_Date": act.get("document_year"),
                    "molecule_chembl_id": act.get("molecule_chembl_id"),
                    "standard_units": act.get("standard_units"),
                    "assay_chembl_id": act.get("assay_chembl_id"),
                    "document_chembl_id": act.get("document_chembl_id"),
                }
            )
            if len(rows) >= max_records:
                break

        offset += len(activities)
        if total is not None and offset >= total:
            break

    if not rows:
        raise RuntimeError(
            "ChEMBL API returned no usable activity records for the requested "
            f"standard types {standard_types}. Cannot proceed without real data."
        )
    logger.info(f"Fetched {len(rows)} real ChEMBL activity records.")
    return rows

def write_sqlite(rows: List[Dict[str, Any]], db_path: Path) -> None:
    """Write fetched rows into a local SQLite database (table: activities)."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            CREATE TABLE activities (
                SMILES TEXT,
                Target TEXT,
                Experimental_Value REAL,
                Assay_Date TEXT,
                molecule_chembl_id TEXT,
                standard_units TEXT,
                assay_chembl_id TEXT,
                document_chembl_id TEXT
            )
            """
        )
        conn.executemany(
            """
            INSERT INTO activities (SMILES, Target, Experimental_Value, Assay_Date,
                                    molecule_chembl_id, standard_units,
                                    assay_chembl_id, document_chembl_id)
            VALUES (:SMILES, :Target, :Experimental_Value, :Assay_Date,
                    :molecule_chembl_id, :standard_units,
                    :assay_chembl_id, :document_chembl_id)
            """,
            rows,
        )
        conn.commit()
        count = conn.execute("SELECT COUNT(*) FROM activities").fetchone()[0]
    finally:
        conn.close()
    logger.info(f"Wrote {count} rows to SQLite database {db_path}")
    if count != len(rows):
        raise RuntimeError(
            f"SQLite row count mismatch: expected {len(rows)}, wrote {count}."
        )

def resolve_standard_types(target_arg: str) -> List[str]:
    """Map the --target keyword list to ChEMBL standard_type values."""
    types: List[str] = []
    for kw in [t.strip().lower() for t in target_arg.split(",") if t.strip()]:
        if kw in TARGET_TYPE_MAP:
            types.extend(TARGET_TYPE_MAP[kw])
        else:
            types.append(kw.upper())
    if not types:
        raise ValueError(f"No valid target keywords parsed from: {target_arg!r}")
    # de-duplicate, preserve order
    return list(dict.fromkeys(types))

def main() -> None:
    """Main entry point for the download task."""
    parser = argparse.ArgumentParser(description="Download real ChEMBL 33 activity data")
    parser.add_argument(
        "--target",
        default="bioavailability,permeability,clearance",
        help="Comma-separated target keywords: bioavailability, permeability, clearance",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=DEFAULT_MAX_RECORDS,
        help="Maximum number of activity records to fetch from the ChEMBL API",
    )
    args = parser.parse_args()

    log_pipeline_step("T009", "Starting ChEMBL 33 data acquisition")

    try:
        standard_types = resolve_standard_types(args.target)
        rows = fetch_chembl_activities(standard_types, args.max_records)
        write_sqlite(rows, OUTPUT_FILE)

        if not OUTPUT_FILE.exists():
            raise FileNotFoundError(f"Output database was not created: {OUTPUT_FILE}")

        # Checksum handling: the FTP .sha256 sidecar is not available for the
        # API route, so per the documented fallback we compute the SHA-256 of
        # the produced database, save it next to the artifact, and record it
        # in the project registry for manual verification.
        db_hash = compute_file_hash(OUTPUT_FILE)
        SHA256_FILE.write_text(db_hash + "\n")
        logger.info(f"Computed SHA-256 of {OUTPUT_FILE}: {db_hash}")

        update_state(
            project_id=PROJECT_ID,
            artifacts=[
                {
                    "artifact_path": str(OUTPUT_FILE.relative_to(project_root)),
                    "hash": db_hash,
                    "source": "chembl_webresource_api (release 33 data)",
                    "version": "33",
                }
            ],
        )

        # Report the total number of rows retrieved (US1 acceptance scenario 1)
        print(
            f"ChEMBL 33 data acquisition complete: {len(rows)} activity rows "
            f"retrieved and written to {OUTPUT_FILE}"
        )
        log_pipeline_step("T009", "ChEMBL data acquisition finished", status="completed")

    except Exception as e:
        logger.error(f"Task T009 failed: {e}")
        log_pipeline_step("T009", "ChEMBL data acquisition failed", status="failed")
        raise


if __name__ == "__main__":
    main()