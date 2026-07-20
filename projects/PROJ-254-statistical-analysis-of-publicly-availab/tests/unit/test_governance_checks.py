"""
Unit tests for governance enforcement logic.

Specifically tests that the pipeline fails gracefully when required
spec amendment files are missing while the code attempts to access
Last.fm data.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the function under test from the existing API surface
from code.ingest import ingest_lastfm
from code.utils import setup_logging, get_logger

# Setup logging for tests
setup_logging()
logger = get_logger()


class TestGovernanceChecks:
    """Tests for governance enforcement in the ingestion pipeline."""

    def test_ingest_lastfm_fails_when_amendment_missing(self):
        """
        Assert that ingest_lastfm raises a RuntimeError when
        spec_amendment_lastfm.md is missing and Last.fm data is required.
        
        This ensures the governance logic in T050 is enforced:
        - If the waiver file exists, skip ingestion.
        - If the waiver file is missing, attempt to fetch Last.fm.
        - If the fetch fails (or data is unavailable), raise RuntimeError.
        """
        # Create a temporary directory to simulate the project root
        with tempfile.TemporaryDirectory() as tmp_dir:
            specs_dir = Path(tmp_dir) / "specs" / "001-genre-evolution"
            specs_dir.mkdir(parents=True, exist_ok=True)
            
            # Ensure the waiver file does NOT exist
            waiver_file = specs_dir / "spec_amendment_lastfm.md"
            if waiver_file.exists():
                waiver_file.unlink()
            
            # Temporarily change the working directory or mock the path check
            # Since ingest_lastfm likely checks relative paths or a constant,
            # we rely on the function's internal logic to check for the file.
            # We expect it to fail to fetch Last.fm (which it will in this env)
            # AND fail the governance check if the file is missing.
            
            # Save original CWD
            original_cwd = os.getcwd()
            try:
                # Change to the temp directory to simulate a clean project state
                os.chdir(tmp_dir)
                
                # The function should attempt to check for the waiver.
                # If missing, it tries to fetch. Fetching Last.fm 1B events
                # in a test environment without credentials/network will fail.
                # The key is that it raises an error, not that it succeeds or
                # silently skips.
                
                with pytest.raises(RuntimeError) as exc_info:
                    ingest_lastfm()
                
                # Verify the error message indicates governance or data failure
                error_msg = str(exc_info.value).lower()
                assert "lastfm" in error_msg or "governance" in error_msg or "missing" in error_msg or "failed" in error_msg
                
            finally:
                os.chdir(original_cwd)

    def test_ingest_lastfm_skips_when_amendment_present(self):
        """
        Assert that ingest_lastfm skips ingestion when
        spec_amendment_lastfm.md exists.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            specs_dir = Path(tmp_dir) / "specs" / "001-genre-evolution"
            specs_dir.mkdir(parents=True, exist_ok=True)
            
            # Create the waiver file
            waiver_file = specs_dir / "spec_amendment_lastfm.md"
            waiver_file.write_text("# Waiver for Last.fm Data\n\nLast.fm ingestion waived.")
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                
                # The function should detect the waiver and return/skip
                # without raising an error about missing data.
                # We expect it to return normally (None or similar)
                result = ingest_lastfm()
                
                # If it returns without error, the waiver logic worked.
                # Depending on implementation, it might return None or a status.
                assert result is None or isinstance(result, (dict, type(None)))
                
            finally:
                os.chdir(original_cwd)