import pytest
import json
import os
from pathlib import Path
import sys
import tempfile
import time

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_analysis_resource_profile import load_resource_profile, aggregate_analysis_resources

class TestLoadResourceProfile:
    def test_load_valid_profile(self, tmp_path):
        """Test loading a valid JSON resource profile."""
        profile_path = tmp_path / "resource_profile.json"
        expected_data = {"peak_ram_gb": 4.5, "total_runtime_seconds": 120}
        with open(profile_path, 'w') as f:
            json.dump(expected_data, f)
        
        result = load_resource_profile(profile_path)
        assert result == expected_data

    def test_load_missing_file(self, tmp_path):
        """Test loading a non-existent file returns None."""
        profile_path = tmp_path / "non_existent.json"
        result = load_resource_profile(profile_path)
        assert result is None

    def test_load_invalid_json(self, tmp_path):
        """Test loading an invalid JSON file returns None."""
        profile_path = tmp_path / "invalid.json"
        with open(profile_path, 'w') as f:
            f.write("not valid json")
        
        result = load_resource_profile(profile_path)
        assert result is None

class TestAggregateAnalysisResources:
    def test_aggregate_with_preprocessing_profile(self):
        """Test aggregation when preprocessing profile exists."""
        preprocessing_profile = {"peak_ram_gb": 5.0, "other_key": "value"}
        start = time.time() - 100
        end = time.time()
        
        result = aggregate_analysis_resources(preprocessing_profile, start, end)
        
        assert "peak_ram_gb" in result
        assert result["peak_ram_gb"] == 5.0
        assert "total_runtime_seconds" in result
        assert result["total_runtime_seconds"] > 0
        assert result["phase"] == "analysis"

    def test_aggregate_without_preprocessing_profile(self):
        """Test aggregation when preprocessing profile is missing."""
        result = aggregate_analysis_resources(None, time.time() - 100, time.time())
        
        assert result["peak_ram_gb"] == 0.0
        assert "total_runtime_seconds" in result
        assert result["phase"] == "analysis"
        assert "note" in result