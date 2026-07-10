"""
Integration tests for the Fetcher module (T019).
These tests verify the end-to-end flow from CSV ingestion to file saving.
"""
import pytest
import tempfile
import os
from pathlib import Path
import csv

# Mock requests for integration tests to avoid hitting real network
from unittest.mock import patch, MagicMock

# Setup mock
mock_requests = MagicMock()
mock_response = MagicMock()
mock_response.text = "<html><body>Integration Test</body></html>"
mock_response.status_code = 200
mock_response.raise_for_status = MagicMock()
mock_requests.get.return_value = mock_response

with patch.dict('sys.modules', {'requests': mock_requests, 'requests.exceptions': MagicMock()}):
    from code.src.audit.fetcher import ingest_and_fetch


def test_integration_fetcher_full_flow():
    """
    Integration test: Create a CSV, run fetcher, verify files exist in data/raw/.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = Path(tmpdir) / "input"
        input_dir.mkdir()
        output_dir = Path(tmpdir) / "data" / "raw"

        # Prepare input CSV
        csv_path = input_dir / "urls.csv"
        test_urls = [
            "https://example.com/test1",
            "https://example.org/test2",
            "https://example.net/test3"
        ]

        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['url'])
            writer.writeheader()
            for url in test_urls:
                writer.writerow({'url': url})

        # Run fetcher
        # We need to patch the RAW_DATA_DIR constant in the fetcher module
        # or pass the output_dir to the function if we modify the API.
        # For this test, we will patch the module's behavior to use our temp dir.
        
        # Since ingest_and_fetch uses a hardcoded RAW_DATA_DIR, we patch it.
        with patch('code.src.audit.fetcher.RAW_DATA_DIR', output_dir):
            results = ingest_and_fetch(str(csv_path))

        # Assertions
        assert len(results) == len(test_urls), f"Expected {len(test_urls)} results, got {len(results)}"
        
        # Verify files exist
        for url, file_path in results:
            assert file_path.exists(), f"File not created for {url}: {file_path}"
            assert file_path.parent == output_dir, f"File not in expected directory: {file_path}"
            
            # Verify content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            assert "Integration Test" in content
