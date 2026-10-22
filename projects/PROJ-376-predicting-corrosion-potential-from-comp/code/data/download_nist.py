"""
Download NIST Corrosion Database (NIST-IR-8200) records.

This script fetches data from the NIST-IR-8200 repository using a URL
defined in the project's verified‑datasets configuration. It implements
exponential back‑off retry logic, writes diagnostic logs, creates the
expected output directories, and produces a JSON summary file.

If the download cannot be performed or the resulting dataset contains
fewer than the required number of records (500), a ``DataInsufficientError``
is raised, causing a non‑zero exit status as required by the task
specification.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

import requests

# Project‑local imports – note the relative package path
from code.utils.config import get_config, get_data_path, get_log_path
from code.utils.exceptions import DataInsufficientError
from code.utils.logging import get_logger

# -------------------------------------------------------------
# Configuration constants (aligned with the spec)
# -------------------------------------------------------------
MAX_RETRIES = 5               # total attempts
INITIAL_BACKOFF = 1.0         # seconds
MAX_BACKOFF = 60.0            # seconds
TIMEOUT = 30                  # request timeout (seconds)

# -------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------
def load_verified_dataset_config() -> Dict[str, Any]:
    """
    Load the verified‑datasets registry configuration.

    Returns:
        dict: Configuration dictionary containing (at least) the NIST URL.
    """
    cfg = get_config()
    # The configuration manager returns a ``ProjectConfig`` dataclass;
    # we convert it to a plain dict for easier traversal.
    return cfg.to_dict()


def get_nist_url(config: Dict[str, Any]) -> Optional[str]:
    """
    Extract the NIST‑IR‑8200 download URL from the configuration.

    The URL may be stored under several possible keys – the function
    checks each in turn and returns the first non‑empty string it finds.

    Args:
        config: Project configuration dictionary.

    Returns:
        The URL string if found, otherwise ``None``.
    """
    possible_keys = [
        "verified_datasets.nist_ir_8200.url",
        "data_sources.nist_ir_8200.url",
        "nist_ir_8200.url",
    ]

    for key in possible_keys:
        try:
            parts = key.split(".")
            value = config
            for part in parts:
                value = value[part]
            if isinstance(value, str) and value.strip():
                return value.strip()
        except (KeyError, TypeError):
            continue

    # Legacy fallback
    if "nist_url" in config and isinstance(config["nist_url"], str):
        return config["nist_url"].strip()

    return None


def download_with_retry(url: str, output_path: Path) -> bool:
    """
    Download a file using exponential back‑off retry logic.

    Args:
        url: The URL to download.
        output_path: Destination path for the downloaded file.

    Returns:
        ``True`` if the download succeeded, ``False`` otherwise.

    Raises:
        DataInsufficientError: If the server returns 404 or the maximum
            number of retries is exceeded.
    """
    attempt = 0
    backoff = INITIAL_BACKOFF

    while attempt < MAX_RETRIES:
        try:
            logger.info(f"Attempt {attempt + 1}/{MAX_RETRIES} – GET {url}")
            response = requests.get(url, timeout=TIMEOUT, stream=True)

            if response.status_code == 404:
                logger.error(f"Resource not found (404) at {url}")
                raise DataInsufficientError(
                    f"NIST‑IR‑8200 data not found at URL: {url}"
                )

            response.raise_for_status()

            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Stream to disk
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"Download succeeded → {output_path}")
            return True

        except requests.exceptions.RequestException as exc:
            attempt += 1
            if attempt >= MAX_RETRIES:
                logger.error(
                    f"Maximum retries ({MAX_RETRIES}) exhausted. Last error: {exc}"
                )
                raise DataInsufficientError(
                    f"Failed to download NIST data after {MAX_RETRIES} attempts."
                )
            logger.warning(
                f"Download attempt {attempt} failed ({exc}). Retrying in {backoff:.1f}s..."
            )
            time.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)

    return False  # Should never be reached


def count_records_in_zip(zip_path: Path) -> int:
    """
    Very lightweight record counter for a ZIP archive.

    The NIST dataset is expected to contain CSV files. Instead of fully
    extracting the archive (which could be large), we stream the first
    CSV entry and count its lines (excluding the header). If the archive
    does not contain a CSV or cannot be read, the function returns ``0``.

    Args:
        zip_path: Path to the downloaded ZIP file.

    Returns:
        Approximate number of data rows.
    """
    import zipfile
    import io

    if not zip_path.is_file():
        return 0

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Find the first CSV file inside the archive
            csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                return 0
            first_csv = csv_names[0]
            with zf.open(first_csv) as f:
                # Decode as UTF‑8, count lines
                line_count = sum(1 for _ in io.TextIOWrapper(f, encoding="utf-8"))
                # Subtract header line
                return max(line_count - 1, 0)
    except Exception as exc:
        logger.warning(f"Could not count records in {zip_path}: {exc}")
        return 0


def write_summary(record_count: int, alloy_count: int, summary_path: Path) -> None:
    """
    Write a JSON summary file required by the task specification.

    The summary contains:
    - ``record_count``: total number of corrosion records found.
    - ``alloy_designation_count``: number of distinct alloy designations.

    Args:
        record_count: Total record count.
        alloy_count: Distinct alloy count.
        summary_path: Destination JSON file.
    """
    summary = {
        "record_count": record_count,
        "alloy_designation_count": alloy_count,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Download summary written to {summary_path}")


def main() -> None:
    """
    Entry point for the NIST download script.

    The function:
    1. Loads the project configuration.
    2. Retrieves the NIST download URL.
    3. Creates the required ``data/raw/nist`` and
       ``data/raw/materials_project`` directories.
    4. Downloads the NIST archive with retry logic.
    5. (Optionally) counts records inside the archive.
    6. Writes ``download_summary.json``.
    7. Raises ``DataInsufficientError`` if the record count is below the
       minimum threshold (500 records) – this satisfies the “non‑zero
       exit on insufficient data” requirement.
    """
    global logger
    logger = get_logger(__name__)

    logger.info("=== Starting NIST‑IR‑8200 download ===")

    # -----------------------------------------------------------------
    # 1️⃣ Load configuration
    # -----------------------------------------------------------------
    try:
        config = load_verified_dataset_config()
    except Exception as exc:
        logger.error(f"Failed to load configuration: {exc}")
        raise DataInsufficientError("Project configuration could not be loaded.") from exc

    # -----------------------------------------------------------------
    # 2️⃣ Resolve URL
    # -----------------------------------------------------------------
    nist_url = get_nist_url(config)
    if not nist_url:
        logger.error("NIST‑IR‑8200 URL missing from configuration.")
        raise DataInsufficientError(
            "NIST‑IR‑8200 URL is missing from configuration; cannot download data."
        )
    logger.info(f"NIST download URL resolved: {nist_url}")

    # -----------------------------------------------------------------
    # 3️⃣ Prepare output directories
    # -----------------------------------------------------------------
    raw_root = get_data_path() / "raw"
    nist_dir = raw_root / "nist"
    mp_dir = raw_root / "materials_project"

    for d in (nist_dir, mp_dir):
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured output directory exists: {d}")

    # -----------------------------------------------------------------
    # 4️⃣ Download NIST archive
    # -----------------------------------------------------------------
    zip_path = nist_dir / "nist_ir_8200_data.zip"
    try:
        success = download_with_retry(nist_url, zip_path)
        if not success:
            raise DataInsufficientError("Download reported failure without exception.")
    except DataInsufficientError:
        # Propagate after ensuring a minimal summary is written
        write_summary(0, 0, get_log_path("download_summary.json"))
        raise

    # -----------------------------------------------------------------
    # 5️⃣ Basic record counting (lightweight – no full extraction)
    # -----------------------------------------------------------------
    record_count = count_records_in_zip(zip_path)

    # -----------------------------------------------------------------
    # 6️⃣ Alloy designation count – placeholder (real implementation would
    #     parse the CSV). We set to 0 when we cannot determine it.
    # -----------------------------------------------------------------
    alloy_count = 0
    if record_count > 0:
        # Attempt a quick parse of the first CSV to infer distinct alloy IDs
        import zipfile
        import csv

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
                if csv_names:
                    with zf.open(csv_names[0]) as f:
                        reader = csv.DictReader(
                            (line.decode("utf-8") for line in f)
                        )
                        alloys = set()
                        for row in reader:
                            # The spec does not fix a column name; we look for common
                            # identifiers. If none are present we keep the count at 0.
                            for col in ("alloy_designation", "specific_alloy_designation", "alloy"):
                                if col in row and row[col]:
                                    alloys.add(row[col].strip())
                                    break
                        alloy_count = len(alloys)
        except Exception as exc:
            logger.warning(f"Could not determine alloy count: {exc}")

    # -----------------------------------------------------------------
    # 7️⃣ Write summary JSON
    # -----------------------------------------------------------------
    summary_path = get_log_path("download_summary.json")
    write_summary(record_count, alloy_count, summary_path)

    # -----------------------------------------------------------------
    # 8️⃣ Validate record threshold
    # -----------------------------------------------------------------
    MIN_RECORDS = 500
    if record_count < MIN_RECORDS:
        logger.error(
            f"Insufficient records: {record_count} (minimum required: {MIN_RECORDS})"
        )
        raise DataInsufficientError(
            f"NIST dataset contains only {record_count} records, fewer than the required {MIN_RECORDS}."
        )

    logger.info("=== NIST download completed successfully ===")

if __name__ == "__main__":
    main()
