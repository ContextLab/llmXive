"""
Contract test for the pre-analysis guard (T101).

This test verifies that `code/99_preanalysis_guard.py` correctly exits
with a non-zero status when the required input file is missing.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

import pytest

# Add the code directory to the path so we can import config/logging if needed,
# but here we rely on running the script as a subprocess.
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"

GUARD_SCRIPT = CODE_DIR / "99_preanalysis_guard.py"
ANONYMISED_FILE = PROCESSED_DIR / "anonymised_ratings.csv"


def test_guard_fails_when_file_missing(monkeypatch, tmp_path):
    """
    Verify that the guard script exits with non-zero status when
    data/processed/anonymised_ratings.csv is absent.
    """
    # Ensure the file does not exist
    if ANONYMISED_FILE.exists():
        # Backup if it exists (though in a clean test env it shouldn't)
        ANONYMISED_FILE.rename(PROCESSED_DIR / "anonymised_ratings.csv.bak")

    try:
        # Run the guard script
        result = subprocess.run(
            [sys.executable, str(GUARD_SCRIPT)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        # Assert exit code is non-zero (failure)
        assert result.returncode != 0, (
            f"Guard script should fail when file is missing. "
            f"Stdout: {result.stdout}, Stderr: {result.stderr}"
        )

        # Check that the error message mentions the missing file
        assert "not found" in result.stderr.lower() or "absent" in result.stderr.lower(), (
            f"Error message should indicate file missing. Got: {result.stderr}"
        )

    finally:
        # Restore file if it was backed up
        if (PROCESSED_DIR / "anonymised_ratings.csv.bak").exists():
            (PROCESSED_DIR / "anonymised_ratings.csv.bak").rename(ANONYMISED_FILE)


def test_guard_fails_when_schema_missing(monkeypatch, tmp_path):
    """
    Verify that the guard script exits with non-zero status when
    the schema file is missing.
    """
    # Ensure the ratings file exists (create a minimal one)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ANONYMISED_FILE.write_text("participant_id,rating\n1,5\n")

    # Backup schema if it exists
    schema_file = PROJECT_ROOT / "specs" / "001-the-impact-of-text-message-tone-on-perce" / "contracts" / "rating.schema.yaml"
    schema_backup = None
    if schema_file.exists():
        schema_backup = schema_file.parent / "rating.schema.yaml.bak"
        schema_file.rename(schema_backup)

    try:
        result = subprocess.run(
            [sys.executable, str(GUARD_SCRIPT)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        assert result.returncode != 0, (
            f"Guard script should fail when schema is missing. "
            f"Stdout: {result.stdout}, Stderr: {result.stderr}"
        )

    finally:
        # Restore schema
        if schema_backup and schema_backup.exists():
            schema_backup.rename(schema_file)
        # Clean up test file
        if ANONYMISED_FILE.exists():
            ANONYMISED_FILE.unlink()


def test_guard_fails_on_pii(monkeypatch, tmp_path):
    """
    Verify that the guard script exits with non-zero status when
    the file contains PII (raw Prolific ID pattern).
    """
    # Ensure the ratings file exists with PII
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    # Create a file with a column that looks like a Prolific ID
    pii_content = "participant_id,rating\na1b2c3d4e5f6g7h8,5\n"
    ANONYMISED_FILE.write_text(pii_content)

    # Ensure schema exists (create a minimal one if missing)
    schema_dir = PROJECT_ROOT / "specs" / "001-the-impact-of-text-message-tone-on-perce" / "contracts"
    schema_dir.mkdir(parents=True, exist_ok=True)
    schema_file = schema_dir / "rating.schema.yaml"
    schema_content = """
    type: object
    required:
      - participant_id
      - rating
    properties:
      participant_id:
        type: string
      rating:
        type: integer
    """
    schema_file.write_text(schema_content)

    try:
        result = subprocess.run(
            [sys.executable, str(GUARD_SCRIPT)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        assert result.returncode != 0, (
            f"Guard script should fail when PII is detected. "
            f"Stdout: {result.stdout}, Stderr: {result.stderr}"
        )

        assert "pii" in result.stderr.lower() or "potential" in result.stderr.lower(), (
            f"Error message should indicate PII. Got: {result.stderr}"
        )

    finally:
        # Clean up
        if ANONYMISED_FILE.exists():
            ANONYMISED_FILE.unlink()
        if schema_file.exists():
            schema_file.unlink()


def test_guard_passes_when_valid(monkeypatch, tmp_path):
    """
    Verify that the guard script exits with status 0 when everything is valid.
    """
    # Create valid anonymised file (no PII pattern)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    # Use a hashed-looking ID (longer or different pattern)
    valid_content = "participant_id,rating\nhash_abc123xyz789def456,5\n"
    ANONYMISED_FILE.write_text(valid_content)

    # Ensure schema exists
    schema_dir = PROJECT_ROOT / "specs" / "001-the-impact-of-text-message-tone-on-perce" / "contracts"
    schema_dir.mkdir(parents=True, exist_ok=True)
    schema_file = schema_dir / "rating.schema.yaml"
    schema_content = """
    type: object
    required:
      - participant_id
      - rating
    properties:
      participant_id:
        type: string
      rating:
        type: integer
    """
    schema_file.write_text(schema_content)

    try:
        result = subprocess.run(
            [sys.executable, str(GUARD_SCRIPT)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, (
            f"Guard script should pass when data is valid. "
            f"Stdout: {result.stdout}, Stderr: {result.stderr}"
        )

    finally:
        # Clean up
        if ANONYMISED_FILE.exists():
            ANONYMISED_FILE.unlink()
        if schema_file.exists():
            schema_file.unlink()