"""Unit tests for the URL ingestion and deduplication module."""

import pytest
import tempfile
import csv
from pathlib import Path

from code.src.audit.ingestor import (
    read_urls_from_csv,
    deduplicate_urls,
    write_urls_to_csv,
    ingest_and_deduplicate
)


class TestReadUrlsFromCsv:
    """Tests for read_urls_from_csv function."""

    def test_read_valid_csv(self, tmp_path):
        """Test reading URLs from a valid CSV file."""
        input_file = tmp_path / "urls.csv"
        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['url'])
            writer.writeheader()
            writer.writerow({'url': 'https://example.com/test1'})
            writer.writerow({'url': 'https://example.com/test2'})

        urls = read_urls_from_csv(str(input_file))
        assert len(urls) == 2
        assert urls[0] == 'https://example.com/test1'
        assert urls[1] == 'https://example.com/test2'

    def test_read_csv_with_empty_urls(self, tmp_path):
        """Test that empty URLs are skipped."""
        input_file = tmp_path / "urls.csv"
        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['url'])
            writer.writeheader()
            writer.writerow({'url': 'https://example.com/test1'})
            writer.writerow({'url': ''})
            writer.writerow({'url': '   '})
            writer.writerow({'url': 'https://example.com/test2'})

        urls = read_urls_from_csv(str(input_file))
        assert len(urls) == 2

    def test_read_nonexistent_file(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            read_urls_from_csv(str(tmp_path / "nonexistent.csv"))

    def test_read_invalid_csv_format(self, tmp_path):
        """Test that ValueError is raised for invalid CSV format."""
        input_file = tmp_path / "urls.csv"
        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['name'])
            writer.writeheader()
            writer.writerow({'name': 'test'})

        with pytest.raises(ValueError):
            read_urls_from_csv(str(input_file))


class TestDeduplicateUrls:
    """Tests for deduplicate_urls function."""

    def test_deduplicate_case_sensitive(self):
        """Test case-sensitive deduplication."""
        urls = [
            'https://example.com/test',
            'https://example.com/Test',
            'https://example.com/TEST',
            'https://example.com/other'
        ]
        deduplicated, count = deduplicate_urls(urls, case_insensitive=False)
        assert len(deduplicated) == 4
        assert count == 0

    def test_deduplicate_case_insensitive(self):
        """Test case-insensitive deduplication."""
        urls = [
            'https://example.com/test',
            'https://example.com/Test',
            'https://example.com/TEST',
            'https://example.com/other'
        ]
        deduplicated, count = deduplicate_urls(urls, case_insensitive=True)
        assert len(deduplicated) == 2
        assert count == 2

    def test_deduplicate_empty_list(self):
        """Test deduplication of empty list."""
        urls = []
        deduplicated, count = deduplicate_urls(urls)
        assert len(deduplicated) == 0
        assert count == 0

    def test_deduplicate_no_duplicates(self):
        """Test deduplication when there are no duplicates."""
        urls = [
            'https://example.com/test1',
            'https://example.com/test2',
            'https://example.com/test3'
        ]
        deduplicated, count = deduplicate_urls(urls)
        assert len(deduplicated) == 3
        assert count == 0

    def test_deduplicate_all_duplicates(self):
        """Test deduplication when all URLs are duplicates."""
        urls = [
            'https://example.com/test',
            'https://example.com/test',
            'https://example.com/test'
        ]
        deduplicated, count = deduplicate_urls(urls)
        assert len(deduplicated) == 1
        assert count == 2


class TestWriteUrlsToCsv:
    """Tests for write_urls_to_csv function."""

    def test_write_urls(self, tmp_path):
        """Test writing URLs to CSV file."""
        output_file = tmp_path / "output.csv"
        urls = [
            'https://example.com/test1',
            'https://example.com/test2'
        ]
        write_urls_to_csv(urls, str(output_file))

        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['url'] == 'https://example.com/test1'
            assert rows[0]['domain'] == 'example.com'

    def test_write_creates_parent_directory(self, tmp_path):
        """Test that write_urls_to_csv creates parent directories."""
        output_file = tmp_path / "subdir" / "nested" / "output.csv"
        urls = ['https://example.com/test']
        write_urls_to_csv(urls, str(output_file))

        assert output_file.exists()

    def test_write_empty_list(self, tmp_path):
        """Test writing empty URL list."""
        output_file = tmp_path / "output.csv"
        write_urls_to_csv([], str(output_file))

        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0


class TestIngestAndDeduplicate:
    """Tests for the main ingest_and_deduplicate function."""

    def test_full_pipeline(self, tmp_path):
        """Test the complete ingestion and deduplication pipeline."""
        # Create input file
        input_file = tmp_path / "input.csv"
        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['url'])
            writer.writeheader()
            writer.writerow({'url': 'https://example.com/test1'})
            writer.writerow({'url': 'https://example.com/test2'})
            writer.writerow({'url': 'https://example.com/test1'})  # duplicate
            writer.writerow({'url': 'https://other.com/test'})

        output_file = tmp_path / "output.csv"

        stats = ingest_and_deduplicate(str(input_file), str(output_file))

        assert stats['total_urls_read'] == 4
        assert stats['unique_urls'] == 3
        assert stats['duplicates_removed'] == 1
        assert output_file.exists()

    def test_pipeline_preserves_first_occurrence(self, tmp_path):
        """Test that the first occurrence of a URL is preserved."""
        input_file = tmp_path / "input.csv"
        with open(input_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['url'])
            writer.writeheader()
            writer.writerow({'url': 'https://example.com/test'})
            writer.writerow({'url': 'https://example.com/TEST'})  # duplicate

        output_file = tmp_path / "output.csv"
        ingest_and_deduplicate(str(input_file), str(output_file))

        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['url'] == 'https://example.com/test'
