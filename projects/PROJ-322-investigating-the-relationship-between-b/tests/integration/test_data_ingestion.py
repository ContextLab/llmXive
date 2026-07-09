"""
Integration test for the data ingestion pipeline.

This test verifies that subjects with missing time points are skipped
during manifest generation and that an appropriate exclusion log entry
is emitted.
"""
import csv
import logging
from pathlib import Path

import pytest

# Import the module under test.  The project uses a package layout where
# ``code`` is a top‑level package (it contains an ``__init__.py``), so we
# can import the module directly.
from code import data_ingestion as di


@pytest.fixture
def dummy_subjects():
    """
    Provide a list of subject dictionaries that mimics the structure
    expected by ``generate_manifest``:

    * ``sub-01`` has only an acute time point → should be skipped.
    * ``sub-02`` has both acute and chronic → should be included.
    """
    return [
        {"subject_id": "sub-01", "timepoints": ["acute"]},
        {"subject_id": "sub-02", "timepoints": ["acute", "chronic"]},
    ]


def test_ingestion_skips_subjects_with_missing_time_points_and_logs_exclusion(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, dummy_subjects
):
    """
    Run ``generate_manifest`` with a fabricated subject list and ensure:

    1. Subjects lacking the required time points are not written to the
       manifest CSV.
    2. An INFO‑level log entry describing the exclusion is emitted.
    """
    # Prepare a temporary manifest file path.
    manifest_path = tmp_path / "manifest.csv"

    # Force the logger used by the ingestion module to propagate to the
    # pytest ``caplog`` fixture.
    logger = logging.getLogger("data_ingestion")
    logger.setLevel(logging.INFO)

    # Capture logs emitted during manifest generation.
    caplog.set_level(logging.INFO, logger="data_ingestion")

    # Execute the function under test.
    di.generate_manifest(dummy_subjects, str(manifest_path))

    # ------------------------------------------------------------------
    # Verify the manifest contents.
    # ------------------------------------------------------------------
    # The manifest should exist and contain only the fully‑qualified subject.
    assert manifest_path.is_file(), "Manifest file was not created."

    with manifest_path.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    # Extract the subject IDs present in the CSV.
    subject_ids_in_manifest = {row["subject_id"] for row in rows}

    # ``sub-01`` must be absent because it lacks the chronic time point.
    assert "sub-01" not in subject_ids_in_manifest, (
        "Subject with missing time points was not skipped."
    )
    # ``sub-02`` must be present.
    assert "sub-02" in subject_ids_in_manifest, (
        "Subject with complete time points was not included."
    )

    # ------------------------------------------------------------------
    # Verify that an exclusion log entry was emitted.
    # ------------------------------------------------------------------
    exclusion_messages = [
        record.message
        for record in caplog.records
        if "Skipping subject" in record.message
    ]

    # There should be at least one log line that mentions the skipped subject.
    assert any(
        "sub-01" in msg for msg in exclusion_messages
    ), "No log entry recorded for the excluded subject."


# ----------------------------------------------------------------------
# Helper: monkey‑patch ``parse_subject_info`` so that if other parts of the
# pipeline (e.g., ``main``) are exercised in the future they will receive the
# same dummy data without touching the filesystem.
# ----------------------------------------------------------------------
@pytest.fixture(autouse=True)
def patch_parse_subject_info(monkeypatch, dummy_subjects):
    """
    Replace ``parse_subject_info`` with a stub that returns the dummy
    subject list.  This ensures that any internal call to the function
    during the test uses deterministic data.
    """
    monkeypatch.setattr(di, "parse_subject_info", lambda _: dummy_subjects)