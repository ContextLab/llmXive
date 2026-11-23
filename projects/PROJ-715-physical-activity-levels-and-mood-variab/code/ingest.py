import os
import sys
import logging
import hashlib
import json
import re
import requests
import shutil
import zipfile
import pandas as pd
from pathlib import Path

from config import get_path, init_logger, update_state_artifact_hash

logger = init_logger(__name__)

# OSF Primary Source (from config provenance)
OSF_URL = "https://osf.io/download/5b1a9f1b9ad5a10018669804/"
OSF_DOI = "10.17605/OSF.IO/5B1A9"

# Canonical Dartmouth StudentLife distribution (the primary publisher
# of the dataset; used as a real fallback when OSF is unreachable).
DARTMOUTH_URL = "http://studentlife.cs.dartmouth.edu/dataset/StudentLife_Dataset.zip"

# Real candidate sources, tried in order. There is NO synthetic
# fallback: if all real sources fail, we raise RuntimeError.
SOURCES = [
    ("OSF (DOI %s)" % OSF_DOI, OSF_URL),
    ("Dartmouth StudentLife canonical", DARTMOUTH_URL),
]

# Keys in EMA JSON records that carry an affect/mood rating.
MOOD_KEY_CANDIDATES = [
    "mood", "happy", "happyornot", "sad", "affect", "valence",
    "pam", "picture_index", "picture_id",
]
TIMESTAMP_KEY_CANDIDATES = ["resp_time", "timestamp", "time", "date"]

UID_RE = re.compile(r"(u\d+)", re.IGNORECASE)


def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(1 << 20), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_file(url: str, output_path: str) -> bool:
    """Download a file from a URL with progress logging."""
    try:
        logger.info(f"Downloading from {url}...")
        response = requests.get(url, stream=True, timeout=(30, 120),
                                allow_redirects=True)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0

        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and downloaded % (100 << 20) < (1 << 20):
                        percent = (downloaded / total_size) * 100
                        logger.info(
                            f"Progress: {downloaded / (1 << 20):.0f} MiB "
                            f"({percent:.1f}%)")
        logger.info(f"Download complete: {output_path} "
                    f"({downloaded / (1 << 20):.1f} MiB)")
        return True
    except requests.RequestException as e:
        logger.error(f"Download failed: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return False


def _is_zip_valid(zip_path: str) -> bool:
    """Check the file is a valid, non-corrupted ZIP archive."""
    if not os.path.exists(zip_path) or os.path.getsize(zip_path) < 1024:
        return False
    if not zipfile.is_zipfile(zip_path):
        return False
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                logger.error(f"Corrupted ZIP member: {bad}")
                return False
        return True
    except zipfile.BadZipFile:
        return False


def _extract_uid(member_name: str):
    m = UID_RE.search(member_name)
    return m.group(1).lower() if m else None


def _parse_ema_member(zf: zipfile.ZipFile, member: str, rows: list):
    """Parse one EMA JSON member into long-format rows."""
    try:
        with zf.open(member) as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning(f"Could not parse JSON {member}: {e}")
        return
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return
    uid = _extract_uid(member)
    for rec in data:
        if not isinstance(rec, dict):
            continue
        ts = None
        for key in TIMESTAMP_KEY_CANDIDATES:
            if key in rec and rec[key] not in (None, ""):
                ts = rec[key]
                break
        mood = None
        for key in MOOD_KEY_CANDIDATES:
            if key in rec and rec[key] not in (None, ""):
                try:
                    mood = float(rec[key])
                except (TypeError, ValueError):
                    continue
                break
        if ts is None or mood is None:
            continue
        rows.append({
            "participant_id": uid,
            "timestamp": ts,
            "step_count": None,
            "mood": mood,
            "source_file": member,
        })


def _parse_step_member(zf: zipfile.ZipFile, member: str, rows: list):
    """Parse one step/pedometer CSV member into long-format rows."""
    try:
        with zf.open(member) as f:
            df = pd.read_csv(f)
    except Exception as e:
        logger.warning(f"Could not read CSV {member}: {e}")
        return
    if df.empty:
        return
    cols = {c.lower(): c for c in df.columns}
    ts_col = None
    for key in TIMESTAMP_KEY_CANDIDATES:
        if key in cols:
            ts_col = cols[key]
            break
    step_col = None
    for c in df.columns:
        lc = c.lower()
        if "step" in lc:
            step_col = c
            break
    if ts_col is None or step_col is None:
        return
    uid = _extract_uid(member)
    for _, r in df[[ts_col, step_col]].iterrows():
        try:
            steps = float(r[step_col])
        except (TypeError, ValueError):
            continue
        if steps != steps:  # NaN
            continue
        rows.append({
            "participant_id": uid,
            "timestamp": r[ts_col],
            "step_count": steps,
            "mood": None,
            "source_file": member,
        })


def extract_and_convert_zip(zip_path: str, output_parquet_path: str):
    """
    Extract the relevant EMA (mood) and step/pedometer data from the
    StudentLife ZIP and convert it to a long-format bronze Parquet file
    with columns: participant_id, timestamp, step_count, mood,
    source_file.

    Only EMA JSON files and step/pedometer CSVs are extracted (the
    heavy accelerometer/audio sensor logs are skipped), so the full
    multi-GB archive never has to be materialised on disk or in RAM.
    """
    logger.info(f"Converting {zip_path} to {output_parquet_path}")

    rows = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = zf.namelist()
        n_ema = n_steps = 0
        for member in members:
            if member.endswith("/"):
                continue
            lname = member.lower()
            if lname.endswith(".json") and ("ema" in lname.split("/")):
                _parse_ema_member(zf, member, rows)
                n_ema += 1
            elif lname.endswith(".csv") and (
                    "pedometer" in lname or "step" in lname):
                _parse_step_member(zf, member, rows)
                n_steps += 1
        logger.info(f"Parsed {n_ema} EMA JSON files and "
                    f"{n_steps} step CSV files -> {len(rows)} raw rows")

    if not rows:
        raise RuntimeError(
            "No EMA mood records or step records could be parsed from "
            "the downloaded archive. The archive structure does not "
            "match the expected StudentLife layout; refusing to "
            "fabricate data.")

    bronze = pd.DataFrame(rows)

    # Normalise timestamps (StudentLife uses unix epoch seconds).
    ts = pd.to_numeric(bronze["timestamp"], errors="coerce")
    # Heuristic: values > 1e12 are milliseconds.
    ts = ts.where(ts < 1e12, ts / 1000.0)
    bronze["timestamp"] = pd.to_datetime(ts, unit="s", errors="coerce")
    bronze = bronze.dropna(subset=["timestamp"])

    # participant_id from path may be missing for some members;
    # drop those rows rather than inventing an id.
    bronze = bronze.dropna(subset=["participant_id"])
    bronze["participant_id"] = bronze["participant_id"].astype(str)

    if bronze.empty:
        raise RuntimeError(
            "All parsed records had unparseable timestamps or missing "
            "participant ids; refusing to write an empty bronze file.")

    bronze = bronze.reset_index(drop=True)
    bronze.to_parquet(output_parquet_path, index=False)
    logger.info(f"Successfully wrote {output_parquet_path} "
                f"({bronze.shape[0]} rows)")


def download_and_verify():
    """
    Robust dataset download (T007):
    1. Try each REAL source in order (OSF, then the canonical
       Dartmouth distribution).
    2. Validate the downloaded ZIP (non-trivial size, valid ZIP,
       CRC check).
    3. Convert to data/raw/bronze.parquet.
    4. Record the SHA-256 of the parquet in the project state file
       under artifact_hashes.data_raw_bronze.
    Fails loudly with RuntimeError if any step fails. There is NO
    synthetic-data fallback.
    """
    raw_dir = get_path("data", "raw")
    state_path = get_path(
        "state", "projects",
        "PROJ-715-physical-activity-levels-and-mood-variab.yaml")

    os.makedirs(raw_dir, exist_ok=True)

    zip_path = os.path.join(raw_dir, "studentlife_raw.zip")
    parquet_path = os.path.join(raw_dir, "bronze.parquet")

    for stale in (zip_path, parquet_path):
        if os.path.exists(stale):
            os.remove(stale)

    failures = []
    success = False
    for name, url in SOURCES:
        if not download_file(url, zip_path):
            failures.append(f"{name} ({url}): download failed")
            continue
        if not _is_zip_valid(zip_path):
            failures.append(f"{name} ({url}): downloaded file is not a "
                            "valid ZIP archive (possibly an error page "
                            "or truncated transfer)")
            if os.path.exists(zip_path):
                os.remove(zip_path)
            continue
        success = True
        logger.info(f"Successfully obtained dataset from: {name}")
        break

    if not success:
        raise RuntimeError(
            "Failed to download the StudentLife dataset from any real "
            "source. Attempted sources and errors:\n  - " +
            "\n  - ".join(failures) +
            "\nNo synthetic fallback is permitted; fix the network "
            "access or the source URLs in code/config.py and re-run.")

    # Convert to Parquet (raises RuntimeError on structural failure).
    try:
        extract_and_convert_zip(zip_path, parquet_path)
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Data conversion failed: {e}")

    # Verify the Parquet is readable and non-empty.
    try:
        df_check = pd.read_parquet(parquet_path)
        if df_check.empty:
            raise ValueError("Generated Parquet file is empty.")
        logger.info(f"Verified Parquet: {df_check.shape}")
    except Exception as e:
        raise RuntimeError(f"Parquet verification failed: {e}")

    # Record the checksum of the immutable bronze artifact.
    final_checksum = compute_sha256(parquet_path)
    update_state_artifact_hash(state_path, "data_raw_bronze",
                               final_checksum)
    logger.info(f"State updated with checksum: {final_checksum}")

    # Clean up the temporary zip.
    if os.path.exists(zip_path):
        os.remove(zip_path)

    logger.info("Dataset download and verification complete.")


def main():
    download_and_verify()


if __name__ == "__main__":
    main()