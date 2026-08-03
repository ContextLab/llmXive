"""
Tests for T012a dataset availability check.
"""
import os
import json
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.download import (
    verify_url_status,
    verify_dataset_manifest,
    download_datasets,
    DataUnavailableError
)

class TestDatasetAvailability:
    """Test suite for dataset availability checking functionality."""

    def test_verify_url_status_success(self):
        """Test successful URL verification with a known good URL."""
        # Use a reliable public URL for testing
        result = verify_url_status("https://httpbin.org/status/200", timeout=5)
        assert result is True

    def test_verify_url_status_failure(self):
        """Test failed URL verification with a bad URL."""
        result = verify_url_status("https://httpbin.org/status/404", timeout=5)
        assert result is False

    def test_verify_url_status_timeout(self):
        """Test URL verification with timeout."""
        result = verify_url_status("https://10.255.255.1", timeout=1)
        assert result is False

    def test_verify_dataset_manifest_structure(self):
        """Test that manifest verification returns expected structure."""
        result = verify_dataset_manifest("test_dataset", "direct_url", "https://example.com")
        
        assert "dataset" in result
        assert "source_type" in result
        assert "url" in result
        assert "status" in result
        assert "error" in result
        assert result["status"] in ["SUCCESS", "FAILED"]

    def test_download_datasets_returns_required_keys(self):
        """Test that download_datasets returns all required keys."""
        results = download_datasets()
        
        required_keys = ["recipe1m", "flavordb", "counterfactual", "use_proxy"]
        for key in required_keys:
            assert key in results, f"Missing required key: {key}"

    def test_download_datasets_status_values(self):
        """Test that status values are either SUCCESS or FAILED."""
        results = download_datasets()
        
        for dataset in ["recipe1m", "flavordb", "counterfactual"]:
            status = results.get(dataset, {}).get("status")
            assert status in ["SUCCESS", "FAILED"], f"Invalid status for {dataset}: {status}"

    def test_download_datasets_use_proxy_logic(self):
        """Test that use_proxy is set correctly based on individual dataset statuses."""
        results = download_datasets()
        
        flavordb_failed = results.get("flavordb", {}).get("status") == "FAILED"
        counterfactual_failed = results.get("counterfactual", {}).get("status") == "FAILED"
        
        expected_proxy = flavordb_failed or counterfactual_failed
        assert results["use_proxy"] == expected_proxy, \
            f"use_proxy mismatch: expected {expected_proxy}, got {results['use_proxy']}"

    def test_output_file_creation(self):
        """Test that the output file is created with valid JSON."""
        # Run the main function to generate output
        from data.download import main
        
        # Capture the results
        results = main()
        
        # Check that the file was created
        project_root = Path(__file__).parent.parent.parent
        output_path = project_root / "data" / "download_status.json"
        
        assert output_path.exists(), f"Output file not created: {output_path}"
        
        # Verify JSON content
        with open(output_path, 'r') as f:
            saved_results = json.load(f)
        
        assert saved_results == results, "Saved results don't match returned results"

    def test_data_unavailable_error_raises(self):
        """Test that DataUnavailableError can be raised."""
        with pytest.raises(DataUnavailableError):
            raise DataUnavailableError("Dataset not found")

    def test_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        results = download_datasets()
        
        assert "timestamp" in results
        timestamp = results["timestamp"]
        
        # Basic ISO format check (YYYY-MM-DDTHH:MM:SS)
        assert "T" in timestamp or " " in timestamp, \
            f"Timestamp not in ISO format: {timestamp}"
