import pytest
import sys
from pathlib import Path
import json
import tempfile
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import Config
from data.preprocess import filter_cities, load_raw_dataset, save_processed_data, validate_output

class TestFilterCities:
    """Tests for the filter_cities function in T006a."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_data = [
            {"city": "Beijing", "stops": ["A", "B", "C"]},
            {"city": "Shanghai", "stops": ["D", "E"]},
            {"city": "Guangzhou", "stops": ["F", "G", "H", "I"]},
            {"city": "Shenzhen", "stops": ["J"]},
            {"city": "Chengdu", "stops": ["K", "L"]},  # Not in default list
            {"city": "Unknown", "stops": ["M"]},
        ]

    def test_filter_cities_returns_correct_subset(self):
        """Test that filter_cities returns only routes from specified cities."""
        cities = ["Beijing", "Shanghai"]
        result = filter_cities(self.sample_data, cities)
        
        assert len(result) == 2
        assert all(r["city"] in cities for r in result)

    def test_filter_cities_with_default_config(self):
        """Test filtering with default Chinese cities from Config."""
        result = filter_cities(self.sample_data)
        
        # Should include Beijing, Shanghai, Guangzhou, Shenzhen
        # But not Chengdu (not in default list)
        expected_count = 4
        assert len(result) == expected_count

    def test_filter_cities_empty_result_raises_error(self):
        """Test that filtering with no matches raises ValueError."""
        cities = ["Tokyo", "Seoul"]
        with pytest.raises(ValueError):
            filter_cities(self.sample_data, cities)

    def test_filter_cities_case_sensitivity(self):
        """Test that city matching is case-sensitive as per data format."""
        # Note: Real data should have consistent casing, but this tests robustness
        data_mixed_case = [
            {"city": "beijing", "stops": ["A"]},
            {"city": "Beijing", "stops": ["B"]},
        ]
        result = filter_cities(data_mixed_case, ["Beijing"])
        assert len(result) == 1

    def test_filter_cities_handles_missing_city_field(self):
        """Test behavior when city field is missing."""
        data_missing = [
            {"stops": ["A"]},  # No city field
            {"city": "Beijing", "stops": ["B"]},
        ]
        result = filter_cities(data_missing, ["Beijing"])
        assert len(result) == 1

    def test_filter_cities_output_structure(self):
        """Test that output preserves original route structure."""
        cities = ["Beijing"]
        result = filter_cities(self.sample_data, cities)
        
        assert len(result) == 1
        assert "stops" in result[0]
        assert result[0]["city"] == "Beijing"
        assert result[0]["stops"] == ["A", "B", "C"]