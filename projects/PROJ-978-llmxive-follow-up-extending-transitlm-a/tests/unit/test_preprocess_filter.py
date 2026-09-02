import pytest
import os
import sys
from pathlib import Path
import json
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.preprocess import filter_cities, load_raw_dataset, save_processed_data, validate_output
from config import Config

class TestFilterCities:
    """Unit tests for the filter_cities function (T006a)."""

    def setup_method(self):
        """Create temporary test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.raw_data_path = os.path.join(self.temp_dir, "test_raw.json")
        
        # Create mock dataset with known cities
        self.mock_data = [
            {"route_id": "r1", "city": "Beijing", "stations": ["A", "B", "C"]},
            {"route_id": "r2", "city": "Shanghai", "stations": ["D", "E"]},
            {"route_id": "r3", "city": "Guangzhou", "stations": ["F", "G", "H", "I"]},
            {"route_id": "r4", "city": "Shenzhen", "stations": ["J"]},
            {"route_id": "r5", "city": "Chengdu", "stations": ["K", "L"]}, # Not in default list
            {"route_id": "r6", "city": "Beijing", "stations": ["M", "N"]},
        ]
        
        with open(self.raw_data_path, 'w') as f:
            json.dump(self.mock_data, f)

    def teardown_method(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_filter_cities_returns_correct_count(self):
        """Test that filtering returns the correct number of routes."""
        dataset = load_raw_dataset(self.raw_data_path)
        
        # Filter for the 4 standard cities
        filtered = filter_cities(dataset, cities=Config.CHINESE_CITIES)
        
        # Expected: r1, r2, r3, r4, r6 (Beijing appears twice)
        # Chengdu (r5) should be excluded
        expected_count = 5
        assert len(filtered) == expected_count, f"Expected {expected_count} routes, got {len(filtered)}"

    def test_filter_cities_excludes_non_target(self):
        """Test that non-target cities are excluded."""
        dataset = load_raw_dataset(self.raw_data_path)
        filtered = filter_cities(dataset, cities=["Beijing"])
        
        assert len(filtered) == 2
        cities_in_result = set(r['city'] for r in filtered)
        assert cities_in_result == {"Beijing"}

    def test_filter_cities_missing_city_field_raises(self):
        """Test that missing 'city' field raises ValueError."""
        bad_data = [
            {"route_id": "r1", "stations": ["A", "B"]}, # Missing city
        ]
        
        with pytest.raises(ValueError, match="Route missing 'city' field"):
            filter_cities(bad_data)

    def test_filter_cities_empty_result_raises(self):
        """Test that filtering with no matches raises ValueError."""
        dataset = load_raw_dataset(self.raw_data_path)
        
        with pytest.raises(ValueError, match="No routes found"):
            filter_cities(dataset, cities=["NonExistentCity"])

    def test_filter_cities_preserves_data(self):
        """Test that route data is preserved after filtering."""
        dataset = load_raw_dataset(self.raw_data_path)
        filtered = filter_cities(dataset, cities=["Beijing"])
        
        # Check that original data is intact
        assert filtered[0]['route_id'] == "r1"
        assert filtered[0]['stations'] == ["A", "B", "C"]

    def test_filter_cities_integration_with_save(self):
        """Integration test: filter -> save -> validate."""
        dataset = load_raw_dataset(self.raw_data_path)
        filtered = filter_cities(dataset, cities=Config.CHINESE_CITIES)
        
        output_path = os.path.join(self.temp_dir, "filtered.jsonl")
        save_processed_data(filtered, output_path, format='jsonl')
        
        assert validate_output(output_path, expected_min_rows=5)
        
        # Verify content
        with open(output_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 5
        for line in lines:
            route = json.loads(line)
            assert route['city'] in Config.CHINESE_CITIES


def test_filter_cities_uses_default_config(self):
    """Test that filter_cities uses Config.CHINESE_CITIES when no cities arg is provided."""
    dataset = load_raw_dataset(self.raw_data_path)
    
    # Mock the config to ensure we are testing the default behavior
    original_cities = Config.CHINESE_CITIES
    # We rely on the function logic: if cities is None, it uses Config.CHINESE_CITIES
    # We just need to ensure it doesn't crash and uses the default
    
    # This test is more about ensuring the default path works
    # We can't easily mock the class variable in a unit test without side effects,
    # so we verify the logic by passing None explicitly and checking it behaves like the default
    filtered = filter_cities(dataset, cities=None)
    
    # Should behave the same as passing the config list explicitly
    filtered_explicit = filter_cities(dataset, cities=Config.CHINESE_CITIES)
    
    assert len(filtered) == len(filtered_explicit)
    assert all(r['city'] in Config.CHINESE_CITIES for r in filtered)

def test_filter_cities_handles_large_dataset(self):
    """Test performance with a larger synthetic dataset."""
    # Generate a larger mock dataset
    large_data = []
    cities_list = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Other"]
    for i in range(1000):
        large_data.append({
            "route_id": f"r{i}",
            "city": cities_list[i % 5],
            "stations": [f"s{j}" for j in range(10)]
        })
    
    # Filter for the 4 main cities (80% of data)
    filtered = filter_cities(large_data, cities=Config.CHINESE_CITIES)
    
    expected = 800 # 4/5 of 1000
    assert len(filtered) == expected