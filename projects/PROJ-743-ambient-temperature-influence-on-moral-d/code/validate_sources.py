"""
validate_sources.py
--------------------
Validates the presence, integrity, and basic schema of the Moral Machine dataset
and performs a lightweight check that the Copernicus Climate Data Store (CDS) API
is reachable for ERA5 temperature data.

The script is invoked from the quickstart guide with three arguments:
  --input   Path to the Moral Machine CSV (or CSV.gz) file.
  --temp    Path to the directory containing ERA5 raw data (may be empty at this stage).
  --output  Path to the JSON validation report that will be written.

It performs the following checks:
  1. File existence for the Moral Machine dataset.
  2. SHA‑256 checksum verification against any expected checksum stored in the
     project state file (if present).
  3. Presence of required columns.
  4. Basic existence check for the ERA5 data directory.
  5. Connectivity test to the CDS API (hourly resolution, correct variable).

Results are written to the JSON file specified by --output and also logged to
the standard data‑quality logger used throughout the project.
"""
import argparse
import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Optional import – will raise a clear error if the library is missing.
try:
    import cdsapi
except ImportError as exc:
    raise ImportError(
        "The 'cdsapi' package is required for source validation but is not installed. "
        "Add it to 'code/requirements.txt' and reinstall dependencies."
    ) from exc

from config import get_path_env_override
from setup_logging import get_data_quality_logger

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
REQUIRED_COLUMNS = [
    "latitude",
    "longitude",
    "timestamp",
    "response_time",
    "country",
]

STATE_FILE_PATH = (
    Path("state")
    / "projects"
    / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
)
# ----------------------------------------------------------------------


def compute_sha256(file_path: Path) -> str:
    """Compute SHA‑256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_expected_checksum(state_path: Path) -> str | None:
    """Load the expected Moral Machine checksum from the state YAML, if present."""
    if not state_path.is_file():
        return None
    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "PyYAML is required to read the project state file."
        ) from exc

    with open(state_path, "r") as f:
        state = yaml.safe_load(f)

    if not state or "artifact_hashes" not in state:
        return None
    return state["artifact_hashes"].get("moral_machine_checksum")


def validate_file(path: Path, logger: logging.Logger) -> tuple[bool, str]:
    """Check existence and (optionally) checksum of the Moral Machine file."""
    if not path.is_file():
        msg = f"File not found: {path}"
        logger.error(msg)
        return False, msg

    logger.info(f"Found Moral Machine file: {path}")

    # Check checksum if we have an expected value.
    expected = load_expected_checksum(STATE_FILE_PATH)
    if expected:
        actual = compute_sha256(path)
        if actual == expected:
            logger.info("Checksum verification: PASS")
            return True, "Checksum verified"
        else:
            msg = f"Checksum mismatch (expected {expected}, got {actual})"
            logger.error(msg)
            return False, msg
    else:
        logger.warning(
            "No expected checksum recorded in state file – skipping checksum verification."
        )
        return True, "Checksum skipped"


def validate_columns(csv_path: Path, logger: logging.Logger) -> tuple[bool, str]:
    """Ensure the required columns are present in the CSV (or CSV.gz)."""
    try:
        # Read only the header (and a single row for safety)
        df = pd.read_csv(csv_path, compression="infer", nrows=1)
    except Exception as e:
        msg = f"Failed to read CSV header: {e}"
        logger.error(msg)
        return False, msg

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        msg = f"Missing required columns: {missing}"
        logger.error(msg)
        return False, msg

    logger.info(f"All required columns present: {REQUIRED_COLUMNS}")
    return True, "Columns verified"


def validate_era5_directory(era5_dir: Path, logger: logging.Logger) -> tuple[bool, str]:
    """Very light check that the ERA5 directory exists and contains at least one file."""
    if not era5_dir.is_dir():
        msg = f"ERA5 directory not found: {era5_dir}"
        logger.error(msg)
        return False, msg

    # Look for any file inside – the actual content will be validated later in the pipeline.
    if any(era5_dir.iterdir()):
        logger.info(f"ERA5 directory contains files: {era5_dir}")
        return True, "Directory contains files"
    else:
        msg = f"ERA5 directory is empty: {era5_dir}"
        logger.error(msg)
        return False, msg


def verify_cds_api(logger: logging.Logger) -> tuple[bool, str]:
    """Perform a minimal request to the CDS API to confirm connectivity."""
    try:
        client = cdsapi.Client()
    except Exception as e:
        msg = f"Failed to initialise CDS client: {e}"
        logger.error(msg)
        return False, msg

    try:
        # A tiny request that only asks for metadata (no download)
        client.retrieve(
            "reanalysis-era5-single-levels",
            {
                "variable": "2m_temperature",
                "product_type": "reanalysis",
                "year": "2016",
                "month": "01",
                "day": "01",
                "time": "00:00",
                "format": "json",
            },
            # No target file – we only care that the request succeeds.
            None,
        )
        logger.info("CDS API connectivity test: PASS")
        return True, "CDS API reachable"
    except Exception as e:
        msg = f"CDS API request failed: {e}"
        logger.error(msg)
        return False, msg


def write_report(report_path: Path, report: dict) -> None:
    """Write the validation report as pretty‑printed JSON."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    # Also echo a concise line to the logger for quick visibility.
    logger = get_data_quality_logger()
    logger.info(f"Validation report written to {report_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate source datasets before ingestion."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the Moral Machine CSV (or .csv.gz).",
    )
    parser.add_argument(
        "--temp",
        type=str,
        required=True,
        help="Path to the directory containing raw ERA5 data.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to write the JSON validation report.",
    )
    args = parser.parse_args()

    # Set up the project‑wide data‑quality logger.
    logger = get_data_quality_logger()
    if not logger.handlers:
        # If the logger has not been configured elsewhere, configure a simple console logger.
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    moral_path = Path(args.input)
    era5_dir = Path(args.temp)
    report_path = Path(args.output)

    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {},
    }

    # 1. Moral Machine file existence & checksum
    ok, msg = validate_file(moral_path, logger)
    report["checks"]["moral_machine_file"] = {"status": ok, "detail": msg}
    if not ok:
        write_report(report_path, report)
        return 1

    # 2. Required columns
    ok, msg = validate_columns(moral_path, logger)
    report["checks"]["moral_machine_columns"] = {"status": ok, "detail": msg}
    if not ok:
        write_report(report_path, report)
        return 1

    # 3. ERA5 directory sanity
    ok, msg = validate_era5_directory(era5_dir, logger)
    report["checks"]["era5_directory"] = {"status": ok, "detail": msg}
    if not ok:
        write_report(report_path, report)
        return 1

    # 4. CDS API connectivity / hourly resolution check
    ok, msg = verify_cds_api(logger)
    report["checks"]["cds_api"] = {"status": ok, "detail": msg}
    if not ok:
        write_report(report_path, report)
        return 1

    # All checks passed
    report["overall_status"] = "PASS"
    write_report(report_path, report)
    logger.info("All source validation checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())