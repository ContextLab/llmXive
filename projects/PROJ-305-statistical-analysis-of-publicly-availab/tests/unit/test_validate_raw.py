import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

# Paths used throughout the tests
LOGS_DIR = Path("logs")
SCHEMA_PATH = Path(
    "specs/001-statistical-analysis-of-publicly-availab/contracts/raw_dataset.schema.yaml"
)
RAW_DATA_PATH = Path("data/raw/vaers_2020_2023.parquet")


def run_validator(schema_path: Path, input_path: Path) -> subprocess.CompletedProcess:
    """Helper to invoke the validator via subprocess."""
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "src.data.validate_raw",
            "--schema",
            str(schema_path),
            "--input",
            str(input_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_validate_raw_success():
    """
    The validator should succeed on the official raw VAERS parquet file.
    """
    # Ensure the raw file exists – the download step (T002) must have run beforehand.
    assert RAW_DATA_PATH.is_file(), f"Raw data not found at {RAW_DATA_PATH}"

    result = run_validator(SCHEMA_PATH, RAW_DATA_PATH)

    # Expect a clean exit and the PASS log file.
    assert result.returncode == 0, f"Validator exited with {result.returncode}"
    pass_log = LOGS_DIR / "validate_raw_pass.txt"
    assert pass_log.is_file(), "PASS log file was not created"
    assert pass_log.read_text().strip() == "PASS"


def test_validate_raw_failure(tmp_path: Path):
    """
    Create a deliberately malformed parquet (missing required columns) and
    verify that the validator exits with a non‑zero status and writes the
    FAIL log.
    """
    # Build a minimal DataFrame that omits SOC_CODE and REPT_DATE.
    malformed_df = pd.DataFrame(
        {
            "VAERS_ID": [1, 2],
            "VAX_TYPE": ["COVID-19", "Influenza"],
            # Intentionally leave out SOC_CODE and REPT_DATE
        }
    )
    malformed_file = tmp_path / "malformed.parquet"
    malformed_df.to_parquet(malformed_file)

    result = run_validator(SCHEMA_PATH, malformed_file)

    # Expect failure.
    assert result.returncode != 0, "Validator should have failed but exited with 0"
    fail_log = LOGS_DIR / "validate_raw_fail.txt"
    assert fail_log.is_file(), "FAIL log file was not created"
    # The log should contain the word "FAIL"
    assert "FAIL" in fail_log.read_text()
