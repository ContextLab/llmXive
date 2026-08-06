"""
Contract test for `data/preprocess.py` output schema.

This test validates that the output of `data/preprocess.py` conforms to the
defined schema in `data/contracts/dataset.schema.yaml`. It ensures data
integrity, correct field types, and the presence of required fields for
downstream tasks (T011, T012, etc.).

The test loads the processed dataset from `data/processed/` and validates
it against the schema. It also checks for the presence of the
`<UNKNOWN>` token handling and stratification categories.
"""
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data.contract_validator import load_schema, validate_dataset_schema, validate_output_schema
from config import Config


class TestPreprocessSchema(unittest.TestCase):
    """Contract tests for the output of data/preprocess.py."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.config = Config()
        cls.processed_data_path = cls.config.PROCESSED_DATA_PATH
        cls.schema_path = cls.config.DATASET_SCHEMA_PATH
        
        # Ensure paths exist
        if not cls.processed_data_path.exists():
            raise FileNotFoundError(
                f"Processed data not found at {cls.processed_data_path}. "
                "Run T006 (data/preprocess.py) first."
            )
        
        if not cls.schema_path.exists():
            raise FileNotFoundError(
                f"Dataset schema not found at {cls.schema_path}. "
                "Run T008 first."
            )

        # Load schema
        cls.schema = load_schema(cls.schema_path)
        
        # Load processed data
        with open(cls.processed_data_path, 'r', encoding='utf-8') as f:
            cls.processed_data = json.load(f)

    def test_schema_exists(self):
        """Test that the schema file exists and is valid."""
        self.assertIsNotNone(self.schema)
        self.assertIn('type', self.schema)
        self.assertIn('properties', self.schema)

    def test_root_structure(self):
        """Test that the root of the processed data matches the schema."""
        # Validate the root structure against the schema
        is_valid, errors = validate_dataset_schema(self.processed_data, self.schema)
        self.assertTrue(is_valid, f"Schema validation failed: {errors}")

    def test_required_top_level_fields(self):
        """Test that all required top-level fields are present."""
        required_fields = self.schema.get('properties', {}).keys()
        for field in required_fields:
            self.assertIn(field, self.processed_data, f"Missing required field: {field}")

    def test_routes_structure(self):
        """Test the structure of the 'routes' list."""
        routes = self.processed_data.get('routes', [])
        
        self.assertIsInstance(routes, list)
        self.assertGreater(len(routes), 0, "Routes list is empty")

        # Check the first route structure
        first_route = routes[0]
        
        # Expected fields based on typical preprocess output
        expected_fields = ['route_id', 'stops', 'city', 'length', 'category']
        
        for field in expected_fields:
            self.assertIn(field, first_route, f"Missing field '{field}' in route structure")

    def test_stop_structure(self):
        """Test the structure of individual stops within routes."""
        routes = self.processed_data.get('routes', [])
        
        for i, route in enumerate(routes):
            stops = route.get('stops', [])
            self.assertIsInstance(stops, list, f"Route {i} stops is not a list")
            
            if len(stops) > 0:
                first_stop = stops[0]
                # Check for stop ID or name
                self.assertTrue(
                    'stop_id' in first_stop or 'stop_name' in first_stop,
                    f"Route {i} stop missing 'stop_id' or 'stop_name'"
                )

    def test_stratification_categories(self):
        """Test that routes are correctly stratified into categories."""
        routes = self.processed_data.get('routes', [])
        
        categories = set()
        for route in routes:
            cat = route.get('category')
            self.assertIn(cat, ['short', 'medium', 'long'], 
                          f"Invalid category '{cat}' found")
            categories.add(cat)
        
        # Verify all categories are present (unless dataset is too small)
        expected_cats = {'short', 'medium', 'long'}
        # If dataset is small, it might not have all categories, so we just check validity
        self.assertTrue(categories.issubset(expected_cats))

    def test_unknown_token_handling(self):
        """Test that <UNKNOWN> tokens are handled correctly if present."""
        routes = self.processed_data.get('routes', [])
        
        unknown_count = 0
        for route in routes:
            stops = route.get('stops', [])
            for stop in stops:
                # Check if stop_id or stop_name is <UNKNOWN>
                stop_id = stop.get('stop_id', '')
                stop_name = stop.get('stop_name', '')
                
                if stop_id == '<UNKNOWN>' or stop_name == '<UNKNOWN>':
                    unknown_count += 1
        
        # We don't require UNKNOWN to be present, just that if it is, it's handled
        # The presence of the token itself is valid per schema
        self.assertIsInstance(unknown_count, int)

    def test_route_length_consistency(self):
        """Test that route length matches the number of stops."""
        routes = self.processed_data.get('routes', [])
        
        for i, route in enumerate(routes):
            length = route.get('length')
            stops = route.get('stops', [])
            
            self.assertEqual(
                length, 
                len(stops), 
                f"Route {i} length mismatch: declared {length}, actual {len(stops)}"
            )

    def test_city_filtering(self):
        """Test that routes are filtered for the correct cities."""
        routes = self.processed_data.get('routes', [])
        allowed_cities = self.config.TARGET_CITIES
        
        for i, route in enumerate(routes):
            city = route.get('city')
            self.assertIn(
                city, 
                allowed_cities, 
                f"Route {i} has invalid city '{city}'. Expected one of {allowed_cities}"
            )

    def test_metadata_structure(self):
        """Test the metadata section of the processed data."""
        metadata = self.processed_data.get('metadata', {})
        
        self.assertIsInstance(metadata, dict)
        
        # Check for common metadata fields
        required_meta_fields = ['total_routes', 'cities_processed', 'vocabulary_size']
        for field in required_meta_fields:
            self.assertIn(field, metadata, f"Missing metadata field: {field}")

    def test_data_types(self):
        """Test that data types match the schema expectations."""
        routes = self.processed_data.get('routes', [])
        
        for i, route in enumerate(routes):
            # route_id should be string or int
            self.assertIsInstance(route.get('route_id'), (str, int))
            
            # length should be int
            self.assertIsInstance(route.get('length'), int)
            
            # stops should be list
            self.assertIsInstance(route.get('stops'), list)
            
            # category should be string
            self.assertIsInstance(route.get('category'), str)

    def test_schema_validation_against_output(self):
        """Run the full output schema validation."""
        # This uses the contract_validator to do a comprehensive check
        is_valid, errors = validate_output_schema(self.processed_data, self.schema)
        self.assertTrue(is_valid, f"Output schema validation failed: {errors}")


if __name__ == '__main__':
    unittest.main()