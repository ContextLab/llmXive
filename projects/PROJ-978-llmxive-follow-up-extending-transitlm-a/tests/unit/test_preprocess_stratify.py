import pytest
import pandas as pd
import os
import json
import tempfile
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocess import stratify_routes

class TestStratifyRoutes:
    
    def test_stratify_routes_creates_parquet(self, tmp_path):
        """Test that stratify_routes creates a valid parquet file."""
        # Create sample data
        sample_data = [
            {"route_id": "1", "route_stops": ["A", "B", "C", "D", "E"] * 5},  # 25 stops -> medium
            {"route_id": "2", "route_stops": ["A", "B", "C"] * 3},  # 9 stops -> short
            {"route_id": "3", "route_stops": ["A", "B", "C", "D", "E"] * 10},  # 50 stops -> long
            {"route_id": "4", "route_stops": ["A", "B", "C", "D", "E"] * 2},  # 10 stops -> short
            {"route_id": "5", "route_stops": ["A", "B", "C", "D", "E"] * 4},  # 20 stops -> medium
            {"route_id": "6", "route_stops": ["A", "B", "C", "D", "E"] * 8},  # 40 stops -> long
            {"route_id": "7", "route_stops": ["A", "B", "C", "D", "E"] * 2},  # 10 stops -> short
            {"route_id": "8", "route_stops": ["A", "B", "C", "D", "E"] * 4},  # 20 stops -> medium
            {"route_id": "9", "route_stops": ["A", "B", "C", "D", "E"] * 8},  # 40 stops -> long
            {"route_id": "10", "route_stops": ["A", "B", "C", "D", "E"] * 2},  # 10 stops -> short
            {"route_id": "11", "route_stops": ["A", "B", "C", "D", "E"] * 4},  # 20 stops -> medium
            {"route_id": "12", "route_stops": ["A", "B", "C", "D", "E"] * 8},  # 40 stops -> long
        ]
        
        output_path = tmp_path / "stratified_routes.parquet"
        
        # Run stratification
        df = stratify_routes(sample_data, str(output_path))
        
        # Verify file exists
        assert output_path.exists(), "Output parquet file was not created"
        
        # Verify row count
        assert len(df) == 12, f"Expected 12 rows, got {len(df)}"
        
        # Verify categories
        assert 'category' in df.columns, "Category column missing"
        assert 'stop_count' in df.columns, "Stop count column missing"
        
        # Verify category distribution
        categories = df['category'].value_counts()
        assert 'short' in categories.index, "Short category missing"
        assert 'medium' in categories.index, "Medium category missing"
        assert 'long' in categories.index, "Long category missing"
        
        # Verify specific assignments
        short_routes = df[df['category'] == 'short']
        medium_routes = df[df['category'] == 'medium']
        long_routes = df[df['category'] == 'long']
        
        assert all(short_routes['stop_count'] < 15), "Short routes should have <15 stops"
        assert all((medium_routes['stop_count'] >= 15) & (medium_routes['stop_count'] <= 30)), \
            "Medium routes should have 15-30 stops"
        assert all(long_routes['stop_count'] > 30), "Long routes should have >30 stops"
    
    def test_stratify_routes_empty_data(self, tmp_path):
        """Test that stratify_routes raises error for empty data."""
        output_path = tmp_path / "stratified_routes.parquet"
        
        with pytest.raises(AssertionError, match="Stratified dataset is empty"):
            stratify_routes([], str(output_path))
    
    def test_stratify_routes_balanced_categories(self, tmp_path):
        """Test that stratify_routes validates category balance."""
        # Create data that is intentionally unbalanced
        # 10 short, 1 medium, 1 long
        sample_data = []
        for i in range(10):
            sample_data.append({"route_id": f"short_{i}", "route_stops": ["A", "B"]})  # 2 stops
        sample_data.append({"route_id": "medium_1", "route_stops": ["A", "B"] * 10})  # 20 stops
        sample_data.append({"route_id": "long_1", "route_stops": ["A", "B"] * 20})  # 40 stops
        
        output_path = tmp_path / "stratified_routes.parquet"
        
        with pytest.raises(AssertionError, match="Categories are not balanced"):
            stratify_routes(sample_data, str(output_path))
    
    def test_stratify_routes_thresholds(self, tmp_path):
        """Test boundary conditions for stratification thresholds."""
        # Create routes at exact boundaries
        sample_data = [
            {"route_id": "1", "route_stops": ["A"] * 14},  # 14 -> short
            {"route_id": "2", "route_stops": ["A"] * 15},  # 15 -> medium
            {"route_id": "3", "route_stops": ["A"] * 30},  # 30 -> medium
            {"route_id": "4", "route_stops": ["A"] * 31},  # 31 -> long
        ]
        
        output_path = tmp_path / "stratified_routes.parquet"
        df = stratify_routes(sample_data, str(output_path))
        
        assert df.iloc[0]['category'] == 'short', "14 stops should be short"
        assert df.iloc[1]['category'] == 'medium', "15 stops should be medium"
        assert df.iloc[2]['category'] == 'medium', "30 stops should be medium"
        assert df.iloc[3]['category'] == 'long', "31 stops should be long"
    
    def test_stratify_routes_output_format(self, tmp_path):
        """Test that the output parquet file can be loaded correctly."""
        sample_data = [
            {"route_id": "1", "route_stops": ["A", "B", "C", "D", "E"] * 5},
            {"route_id": "2", "route_stops": ["A", "B", "C"] * 3},
            {"route_id": "3", "route_stops": ["A", "B", "C", "D", "E"] * 10},
        ]
        
        output_path = tmp_path / "stratified_routes.parquet"
        stratify_routes(sample_data, str(output_path))
        
        # Load back and verify
        loaded_df = pd.read_parquet(output_path)
        assert len(loaded_df) == 3
        assert 'category' in loaded_df.columns
        assert 'stop_count' in loaded_df.columns
        assert 'route_id' in loaded_df.columns
        assert 'route_stops' in loaded_df.columns