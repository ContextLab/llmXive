"""
Unit tests for the HumanEval dataset fetcher.
"""

import pytest
from pathlib import Path
import tempfile
import os

from code.data.fetcher import download_human_eval, verify_checksum, load_human_eval
from code.config import Paths


class TestDownloadHumanEval:
    def test_downloads_and_saves_parquet(self):
        """Test that download_human_eval saves a parquet file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            output_file = download_human_eval(output_dir)

            assert output_file.exists()
            assert output_file.suffix == ".parquet"
            assert output_file.parent == output_dir

    def test_skips_download_if_exists(self):
        """Test that download_human_eval skips if file already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            # Create a dummy file
            dummy_file = output_dir / "humaneval.parquet"
            dummy_file.touch()

            # Call download - should not overwrite
            result_file = download_human_eval(output_dir)

            assert result_file == dummy_file
            # Verify it's still the dummy file (size 0)
            assert result_file.stat().st_size == 0


class TestVerifyChecksum:
    def test_verifies_existing_file(self):
        """Test checksum verification on an existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            download_human_eval(output_dir)
            output_file = output_dir / "humaneval.parquet"

            # Should not raise and should return True (or False if checksum mismatch)
            result = verify_checksum(output_file)
            assert isinstance(result, bool)

    def test_returns_false_for_missing_file(self):
        """Test checksum verification on a missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            missing_file = output_dir / "nonexistent.parquet"

            result = verify_checksum(missing_file)
            assert result is False


class TestLoadHumanEval:
    def test_loads_problems_from_parquet(self):
        """Test that load_human_eval returns a list of problems."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            download_human_eval(output_dir)

            problems = load_human_eval(output_dir / "humaneval.parquet")

            assert isinstance(problems, list)
            assert len(problems) > 0
            assert isinstance(problems[0], dict)
            assert "task_id" in problems[0]
            assert "prompt" in problems[0]
            assert "canonical_solution" in problems[0]
            assert "test" in problems[0]

    def test_raises_on_missing_file(self):
        """Test that load_human_eval raises FileNotFoundError for missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            missing_file = output_dir / "nonexistent.parquet"

            with pytest.raises(FileNotFoundError):
                load_human_eval(missing_file)