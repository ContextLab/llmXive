import pytest
import pandas as pd
import json
import os
from pathlib import Path
import tempfile
import sys

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.preprocess import (
    filter_cities,
    build_vocabulary,
    apply_vocabulary_filter,
    stratify_routes,
    TARGET_CITIES
)

@pytest.fixture
def sample_dataset():
    """Create a sample dataset for testing."""
    return [
        {
            "route_id": "route_1",
            "city": "Beijing",
            "stations": ["A", "B", "C", "D", "E"]
        },
        {
            "route_id": "route_2",
            "city": "Shanghai",
            "stations": ["F", "G", "H"]
        },
        {
            "route_id": "route_3",
            "city": "Guangzhou",
            "stations": ["I", "J", "K", "L"]
        },
        {
            "route_id": "route_4",
            "city": "Shenzhen",
            "stations": ["M", "N", "O", "P", "Q", "R"]
        },
        {
            "route_id": "route_5",
            "city": "Chengdu",  # Not in target cities
            "stations": ["S", "T", "U"]
        },
        {
            "route_id": "route_6",
            "city": "Beijing",
            "stations": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "AA", "BB", "CC", "DD", "EE", "FF", "GG", "HH", "II", "JJ", "KK", "LL", "MM", "NN", "OO", "PP", "QQ", "RR", "SS", "TT", "UU", "VV", "WW", "XX", "YY", "ZZ"]
        }
    ]

class TestFilterCities:
    def test_filter_cities_returns_only_target_cities(self, sample_dataset):
        """Test that filter_cities returns only routes from target cities."""
        result = filter_cities(sample_dataset, TARGET_CITIES)
        
        cities_in_result = {route['city'] for route in result}
        assert cities_in_result == set(TARGET_CITIES)
        
        # Check that Chengdu is excluded
        assert len(result) == 5  # 6 total - 1 Chengdu

    def test_filter_cities_custom_cities(self, sample_dataset):
        """Test filtering with a custom list of cities."""
        custom_cities = ["Beijing", "Shanghai"]
        result = filter_cities(sample_dataset, custom_cities)
        
        cities_in_result = {route['city'] for route in result}
        assert cities_in_result == set(custom_cities)
        assert len(result) == 3  # Beijing (2) + Shanghai (1)

    def test_filter_cities_no_matches_raises_error(self, sample_dataset):
        """Test that filtering with non-existent cities raises ValueError."""
        with pytest.raises(ValueError, match="No routes found"):
            filter_cities(sample_dataset, ["NonExistentCity"])

    def test_filter_cities_preserves_route_data(self, sample_dataset):
        """Test that route data is preserved after filtering."""
        result = filter_cities(sample_dataset, TARGET_CITIES)
        
        # Check that original data is preserved
        beijing_routes = [r for r in result if r['city'] == 'Beijing']
        assert len(beijing_routes) == 2
        assert beijing_routes[0]['route_id'] == 'route_1'
        assert beijing_routes[0]['stations'] == ["A", "B", "C", "D", "E"]

class TestBuildVocabulary:
    def test_build_vocabulary_includes_all_stations(self, sample_dataset):
        """Test that vocabulary includes all unique stations."""
        vocab = build_vocabulary(sample_dataset)
        
        all_stations = set()
        for route in sample_dataset:
            all_stations.update(route['stations'])
        
        # Check that all stations are in vocabulary
        for station in all_stations:
            assert station in vocab
        
        # Check that <UNKNOWN> token is included
        assert '<UNKNOWN>' in vocab

    def test_build_vocabulary_top_n(self, sample_dataset):
        """Test vocabulary building with top_n limit."""
        vocab = build_vocabulary(sample_dataset, top_n=5)
        
        # Should have 5 stations + 1 <UNKNOWN>
        assert len(vocab) == 6
        assert '<UNKNOWN>' in vocab

    def test_build_vocabulary_ids_are_unique(self, sample_dataset):
        """Test that vocabulary IDs are unique."""
        vocab = build_vocabulary(sample_dataset)
        
        ids = list(vocab.values())
        assert len(ids) == len(set(ids))

class TestApplyVocabularyFilter:
    def test_apply_vocabulary_filter_converts_stations(self, sample_dataset):
        """Test that stations are converted to IDs."""
        vocab = build_vocabulary(sample_dataset)
        result = apply_vocabulary_filter(sample_dataset, vocab)
        
        for route in result:
            assert 'station_ids' in route
            assert isinstance(route['station_ids'], list)
            # All IDs should be integers
            for station_id in route['station_ids']:
                assert isinstance(station_id, int)

    def test_apply_vocabulary_filter_handles_unknown(self, sample_dataset):
        """Test that unknown stations are replaced with <UNKNOWN> token."""
        # Create a route with an unknown station
        dataset_with_unknown = sample_dataset + [{
            "route_id": "route_unknown",
            "city": "Beijing",
            "stations": ["UnknownStation123"]
        }]
        
        vocab = build_vocabulary(sample_dataset)  # Build vocab without the unknown station
        result = apply_vocabulary_filter(dataset_with_unknown, vocab)
        
        unknown_route = next(r for r in result if r['route_id'] == 'route_unknown')
        unknown_id = vocab['<UNKNOWN>']
        
        # All stations in the unknown route should be mapped to <UNKNOWN>
        for station_id in unknown_route['station_ids']:
            assert station_id == unknown_id

class TestStratifyRoutes:
    def test_stratify_routes_correct_categories(self, sample_dataset):
        """Test that routes are correctly categorized by length."""
        df = stratify_routes(sample_dataset)
        
        # Check categories
        for _, row in df.iterrows():
            length = row['route_length']
            category = row['length_category']
            
            if length < 15:
                assert category == 'short'
            elif length <= 30:
                assert category == 'medium'
            else:
                assert category == 'long'

    def test_stratify_routes_returns_dataframe(self, sample_dataset):
        """Test that stratify_routes returns a DataFrame."""
        result = stratify_routes(sample_dataset)
        assert isinstance(result, pd.DataFrame)

    def test_stratify_routes_contains_required_columns(self, sample_dataset):
        """Test that the DataFrame contains required columns."""
        df = stratify_routes(sample_dataset)
        
        required_columns = ['route_id', 'city', 'stations', 'route_length', 'length_category']
        for col in required_columns:
            assert col in df.columns