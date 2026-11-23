import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import stratify_routes, validate_output

class TestStratifyRoutes:
    """Unit tests for the stratify_routes function (T006c)."""

    def test_stratify_routes_empty_input(self):
        """Test that empty input raises ValueError."""
        with pytest.raises(ValueError, match="Input data is empty"):
            stratify_routes([])

    def test_stratify_routes_all_short(self):
        """Test stratification with all short routes."""
        data = [
            {"stops": ["A", "B", "C"], "city": "Beijing"},
            {"stops": ["D", "E"], "city": "Shanghai"},
            {"stops": ["F", "G", "H", "I"], "city": "Guangzhou"}
        ]
        df = stratify_routes(data)
        
        assert len(df) == 3
        assert all(df['category'] == 'short')
        assert all(df['route_length'] < 15)
        assert validate_output(df)

    def test_stratify_routes_all_medium(self):
        """Test stratification with all medium routes."""
        data = [
            {"stops": list(range(15)), "city": "Beijing"},
            {"stops": list(range(20)), "city": "Shanghai"},
            {"stops": list(range(30)), "city": "Guangzhou"}
        ]
        df = stratify_routes(data)
        
        assert len(df) == 3
        assert all(df['category'] == 'medium')
        assert all((df['route_length'] >= 15) & (df['route_length'] <= 30))
        assert validate_output(df)

    def test_stratify_routes_all_long(self):
        """Test stratification with all long routes."""
        data = [
            {"stops": list(range(31)), "city": "Beijing"},
            {"stops": list(range(40)), "city": "Shanghai"},
            {"stops": list(range(50)), "city": "Guangzhou"}
        ]
        df = stratify_routes(data)
        
        assert len(df) == 3
        assert all(df['category'] == 'long')
        assert all(df['route_length'] > 30)
        assert validate_output(df)

    def test_stratify_routes_mixed(self):
        """Test stratification with mixed route lengths."""
        data = [
            {"stops": ["A", "B"], "city": "Beijing"},  # short
            {"stops": list(range(15, 25)), "city": "Shanghai"},  # medium
            {"stops": list(range(35, 45)), "city": "Guangzhou"}  # long
        ]
        df = stratify_routes(data)
        
        assert len(df) == 3
        categories = set(df['category'])
        assert categories == {'short', 'medium', 'long'}
        assert validate_output(df)

    def test_stratify_routes_boundary_values(self):
        """Test boundary values for categories."""
        data = [
            {"stops": list(range(14)), "city": "Beijing"},  # short (14 stops)
            {"stops": list(range(15)), "city": "Shanghai"},  # medium (15 stops)
            {"stops": list(range(30)), "city": "Guangzhou"},  # medium (30 stops)
            {"stops": list(range(31)), "city": "Shenzhen"}   # long (31 stops)
        ]
        df = stratify_routes(data)
        
        assert df.iloc[0]['category'] == 'short'
        assert df.iloc[1]['category'] == 'medium'
        assert df.iloc[2]['category'] == 'medium'
        assert df.iloc[3]['category'] == 'long'
        assert validate_output(df)

    def test_stratify_routes_unbalanced_categories_raises(self):
        """Test that missing categories raise ValueError."""
        # Only short and long, no medium
        data = [
            {"stops": ["A", "B"], "city": "Beijing"},
            {"stops": list(range(50)), "city": "Shanghai"}
        ]
        with pytest.raises(ValueError, match="Missing categories"):
            stratify_routes(data)

    def test_stratify_routes_preserves_route_data(self):
        """Test that original route data is preserved."""
        data = [
            {"stops": ["A", "B", "C"], "city": "Beijing", "route_id": "R1", "extra_field": 123}
        ]
        df = stratify_routes(data)
        
        assert df.iloc[0]['city'] == 'Beijing'
        assert df.iloc[0]['route_id'] == 'R1'
        assert df.iloc[0]['extra_field'] == 123
        assert 'category' in df.columns
        assert 'route_length' in df.columns
