"""
Unit tests for the URL Ingestion and Deduplication module (T018).
"""
import csv
import tempfile
from pathlib import Path
import pytest
from code.src.audit.ingestor import (
    read_urls_from_csv,
    deduplicate_urls,
    write_urls_to_csv,
    ingest_and_deduplicate
)


class TestReadUrlsFromCsv:
    def test_read_valid_csv(self, tmp_path):
        input_file = tmp_path / "urls.csv"
        input_file.write_text("url,source_id\nhttps://example.com/test,1\nhttps://another.com,2\n")
        
        urls = read_urls_from_csv(input_file)
        
        assert len(urls) == 2
        assert urls[0] == ("https://example.com/test", "1")
        assert urls[1] == ("https://another.com", "2")

    def test_read_csv_with_missing_source_id(self, tmp_path):
        input_file = tmp_path / "urls.csv"
        input_file.write_text("url\nhttps://example.com/test\n")
        
        urls = read_urls_from_csv(input_file)
        
        assert len(urls) == 1
        assert urls[0] == ("https://example.com/test", None)

    def test_read_empty_url_skipped(self, tmp_path):
        input_file = tmp_path / "urls.csv"
        input_file.write_text("url\n\nhttps://example.com/test\n")
        
        urls = read_urls_from_csv(input_file)
        
        assert len(urls) == 1
        assert urls[0] == ("https://example.com/test", None)

    def test_read_invalid_protocol_skipped(self, tmp_path):
        input_file = tmp_path / "urls.csv"
        input_file.write_text("url\nftp://example.com/test\nhttps://example.com/test\n")
        
        urls = read_urls_from_csv(input_file)
        
        assert len(urls) == 1
        assert urls[0] == ("https://example.com/test", None)

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_urls_from_csv(tmp_path / "nonexistent.csv")

    def test_missing_url_column(self, tmp_path):
        input_file = tmp_path / "urls.csv"
        input_file.write_text("link\nhttps://example.com\n")
        
        with pytest.raises(ValueError):
            read_urls_from_csv(input_file)


class TestDeduplicateUrls:
    def test_no_duplicates(self):
        urls = [
            ("https://example.com/a", "1"),
            ("https://example.com/b", "2"),
            ("https://other.com", "3")
        ]
        result = deduplicate_urls(urls)
        assert len(result) == 3
        assert result == urls

    def test_exact_duplicates(self):
        urls = [
            ("https://example.com/a", "1"),
            ("https://example.com/a", "2"), # Duplicate URL
            ("https://other.com", "3")
        ]
        result = deduplicate_urls(urls)
        assert len(result) == 2
        assert result[0] == ("https://example.com/a", "1") # Keeps first

    def test_case_insensitive_duplicates(self):
        urls = [
            ("https://Example.com/a", "1"),
            ("https://example.com/a", "2"), # Duplicate (case insensitive)
            ("https://other.com", "3")
        ]
        result = deduplicate_urls(urls)
        assert len(result) == 2
        assert result[0] == ("https://Example.com/a", "1")

    def test_trailing_slash_duplicates(self):
        urls = [
            ("https://example.com/a/", "1"),
            ("https://example.com/a", "2"), # Duplicate (trailing slash)
            ("https://other.com", "3")
        ]
        result = deduplicate_urls(urls)
        assert len(result) == 2
        assert result[0] == ("https://example.com/a/", "1")

    def test_empty_list(self):
        assert deduplicate_urls([]) == []


class TestWriteUrlsToCsv:
    def test_write_valid_urls(self, tmp_path):
        urls = [
            ("https://example.com/a", "1"),
            ("https://example.com/b", None)
        ]
        output_file = tmp_path / "out.csv"
        
        write_urls_to_csv(urls, output_file)
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['url'] == "https://example.com/a"
        assert rows[0]['source_id'] == "1"
        assert rows[1]['url'] == "https://example.com/b"
        assert rows[1]['source_id'] == "" # None becomes empty string

class TestIngestAndDeduplicate:
    def test_full_pipeline(self, tmp_path):
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        
        # Create input with duplicates
        input_file.write_text(
            "url,source_id\n"
            "https://example.com/1,1\n"
            "https://example.com/1,2\n" # Duplicate
            "https://other.com,3\n"
        )
        
        result = ingest_and_deduplicate(input_file, output_file)
        
        assert len(result) == 2
        assert output_file.exists()
        
        # Verify output content
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['url'] == "https://example.com/1"
        assert rows[1]['url'] == "https://other.com"
