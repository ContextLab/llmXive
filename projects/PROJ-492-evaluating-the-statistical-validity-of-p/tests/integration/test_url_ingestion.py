"""Integration test for URL ingestion (FR-001 verification).

This test asserts that input/urls.csv processing completes without error,
as required by coverage-executability-08d5764f.

FR-001: The system shall ingest and deduplicate URLs from a CSV file
without errors when the input file is properly formatted.
"""
import csv
import os
import tempfile
from pathlib import Path

import pytest

from code.src.audit.ingestor import (
    ingest_and_deduplicate,
    read_urls_from_csv,
    write_urls_to_csv,
)
from code.src.utils.logger import get_default_logger


class TestURLIngestionFR001:
    """Integration tests for FR-001 URL ingestion verification."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_urls_csv(self, temp_dir):
        """Create a sample input/urls.csv file."""
        input_dir = temp_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)

        urls_file = input_dir / "urls.csv"
        urls = [
            "https://example.com/test1",
            "https://example.com/test2",
            "https://techblog.io/ab-test-summary",
            "https://example.com/test1",  # duplicate
            "https://saasmetrics.com/experiment",
            "https://techblog.io/ab-test-summary",  # duplicate
        ]

        with open(urls_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["url", "source"])
            for url in urls:
                writer.writerow([url, "manual"])

        return urls_file

    @pytest.fixture
    def malformed_urls_csv(self, temp_dir):
        """Create a sample input/urls.csv with edge cases."""
        input_dir = temp_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)

        urls_file = input_dir / "urls_malformed.csv"
        urls = [
            "https://valid-domain.com/test",
            "",  # empty URL
            "https://another-valid.com/test",
            "not-a-url",  # invalid URL
        ]

        with open(urls_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["url", "source"])
            for url in urls:
                writer.writerow([url, "manual"])

        return urls_file

    def test_read_urls_from_csv_completes_without_error(
        self, temp_dir, sample_urls_csv
    ):
        """FR-001: Reading URLs from CSV completes without error."""
        logger = get_default_logger()
        urls, errors = read_urls_from_csv(sample_urls_csv, logger)

        # Should complete without raising exceptions
        assert isinstance(urls, list)
        assert len(urls) > 0
        assert all(isinstance(url, str) for url in urls)

    def test_deduplication_completes_without_error(
        self, temp_dir, sample_urls_csv
    ):
        """FR-001: URL deduplication completes without error."""
        logger = get_default_logger()
        urls, _ = read_urls_from_csv(sample_urls_csv, logger)
        deduped_urls, errors = ingest_and_deduplicate(urls, logger)

        # Should complete without raising exceptions
        assert isinstance(deduped_urls, list)
        # Verify deduplication worked (original had 6, should have 4 unique)
        assert len(deduped_urls) < len(urls)

    def test_write_deduped_urls_to_csv_completes_without_error(
        self, temp_dir, sample_urls_csv
    ):
        """FR-001: Writing deduped URLs to CSV completes without error."""
        logger = get_default_logger()
        urls, _ = read_urls_from_csv(sample_urls_csv, logger)
        deduped_urls, _ = ingest_and_deduplicate(urls, logger)

        output_dir = temp_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "urls_deduped.csv"

        # Should complete without raising exceptions
        write_urls_to_csv(deduped_urls, output_file, logger)

        # Verify file was created
        assert output_file.exists()

        # Verify content
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) > 1  # header + data

    def test_full_ingestion_pipeline_completes_without_error(
        self, temp_dir, sample_urls_csv
    ):
        """FR-001: Full ingestion pipeline completes without error."""
        logger = get_default_logger()

        output_dir = temp_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run full ingestion pipeline
        result = ingest_and_deduplicate(
            read_urls_from_csv(sample_urls_csv, logger)[0],
            logger,
        )

        deduped_urls, errors = result

        # Verify pipeline completed
        assert isinstance(deduped_urls, list)
        assert isinstance(errors, list)

    def test_empty_urls_csv_completes_without_error(self, temp_dir):
        """FR-001: Empty URLs CSV completes without error."""
        input_dir = temp_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)

        urls_file = input_dir / "urls_empty.csv"
        with open(urls_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["url", "source"])

        logger = get_default_logger()
        urls, errors = read_urls_from_csv(urls_file, logger)

        # Should complete without raising exceptions
        assert isinstance(urls, list)
        assert len(urls) == 0

    def test_urls_with_whitespace_completes_without_error(
        self, temp_dir, sample_urls_csv
    ):
        """FR-001: URLs with whitespace complete processing without error."""
        # Add URLs with whitespace to test robustness
        input_dir = temp_dir / "input"
        urls_file = input_dir / "urls_whitespace.csv"

        urls = [
            "  https://example.com/test1  ",
            "https://example.com/test2",
        ]

        with open(urls_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["url", "source"])
            for url in urls:
                writer.writerow([url, "manual"])

        logger = get_default_logger()
        urls_list, errors = read_urls_from_csv(urls_file, logger)

        # Should complete without raising exceptions
        assert isinstance(urls_list, list)
        assert len(urls_list) > 0

    def test_ingestion_produces_output_file(self, temp_dir, sample_urls_csv):
        """FR-001: Ingestion produces the expected output file."""
        logger = get_default_logger()

        output_dir = temp_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "urls_deduped.csv"

        # Run ingestion
        urls, _ = read_urls_from_csv(sample_urls_csv, logger)
        deduped_urls, _ = ingest_and_deduplicate(urls, logger)
        write_urls_to_csv(deduped_urls, output_file, logger)

        # Verify output file exists and has correct structure
        assert output_file.exists()

        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

            # Should have header row
            assert len(rows) >= 1
            assert rows[0][0] == "url"

            # Should have data rows (at least 1 after deduplication)
            assert len(rows) > 1

    def test_no_exceptions_raised_during_processing(
        self, temp_dir, sample_urls_csv
    ):
        """FR-001: No exceptions are raised during URL ingestion."""
        logger = get_default_logger()

        # This test ensures the entire process completes without exceptions
        try:
            urls, errors = read_urls_from_csv(sample_urls_csv, logger)
            deduped_urls, dedup_errors = ingest_and_deduplicate(urls, logger)

            output_dir = temp_dir / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "urls_deduped.csv"

            write_urls_to_csv(deduped_urls, output_file, logger)

            # If we reach here, no exceptions were raised
            assert True

        except Exception as e:
            pytest.fail(f"URL ingestion raised an exception: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])