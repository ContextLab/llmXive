import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Import the function to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.data.preprocess import stratify_routes

@pytest.fixture
def sample_routes():
    """Generate a sample dataset for testing."""
    return [
        {"route_id": "r1", "city": "Beijing", "stops": ["A", "B", "C"]},  # Short (3)
        {"route_id": "r2", "city": "Shanghai", "stops": ["D"] * 10},      # Short (10)
        {"route_id": "r3", "city": "Guangzhou", "stops": ["E"] * 15},     # Medium (15)
        {"route_id": "r4", "city": "Shenzhen", "stops": ["F"] * 25},     # Medium (25)
        {"route_id": "r5", "city": "Beijing", "stops": ["G"] * 31},      # Long (31)
        {"route_id": "r6", "city": "Shanghai", "stops": ["H"] * 50},     # Long (50)
        {"route_id": "r7", "city": "Beijing", "stops": ["I"] * 14},      # Short (14)
        {"route_id": "r8", "city": "Shanghai", "stops": ["J"] * 30},     # Medium (30)
    ]

def test_stratify_routes_creates_parquet(sample_routes, tmp_path):
    """Test that stratify_routes creates a valid Parquet file."""
    output_path = tmp_path / "stratified_routes.parquet"
    stratify_routes(sample_routes, str(output_path))
    
    assert output_path.exists(), "Output Parquet file was not created."
    assert output_path.stat().st_size > 0, "Output Parquet file is empty."

def test_stratify_routes_correct_categories(sample_routes, tmp_path):
    """Test that routes are assigned to correct categories."""
    output_path = tmp_path / "stratified_routes.parquet"
    stratify_routes(sample_routes, str(output_path))
    
    df = pd.read_parquet(output_path)
    
    # Check counts
    short_count = len(df[df["category"] == "short"])
    medium_count = len(df[df["category"] == "medium"])
    long_count = len(df[df["category"] == "long"])
    
    # Expected: 
    # Short: r1 (3), r2 (10), r7 (14) -> 3
    # Medium: r3 (15), r4 (25), r8 (30) -> 3
    # Long: r5 (31), r6 (50) -> 2
    assert short_count == 3, f"Expected 3 short routes, got {short_count}"
    assert medium_count == 3, f"Expected 3 medium routes, got {medium_count}"
    assert long_count == 2, f"Expected 2 long routes, got {long_count}"

def test_stratify_routes_empty_input():
    """Test that empty input raises ValueError."""
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
        tmp_path = tmp.name
    
    with pytest.raises(ValueError, match="Input data is empty"):
        stratify_routes([], tmp_path)
    
    # Cleanup
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

def test_stratify_routes_metadata(sample_routes, tmp_path):
    """Test that metadata (length, route_id) is preserved."""
    output_path = tmp_path / "stratified_routes.parquet"
    stratify_routes(sample_routes, str(output_path))
    
    df = pd.read_parquet(output_path)
    
    # Check that required columns exist
    assert "route_id" in df.columns
    assert "length" in df.columns
    assert "category" in df.columns
    assert "stops" in df.columns
    assert "city" in df.columns

def test_stratify_routes_length_calculation(sample_routes, tmp_path):
    """Test that 'length' column matches actual stop count."""
    output_path = tmp_path / "stratified_routes.parquet"
    stratify_routes(sample_routes, str(output_path))
    
    df = pd.read_parquet(output_path)
    
    for _, row in df.iterrows():
        assert row["length"] == len(row["stops"]), f"Length mismatch for {row['route_id']}"
        # Verify category logic
        if row["length"] < 15:
            assert row["category"] == "short"
        elif row["length"] <= 30:
            assert row["category"] == "medium"
        else:
            assert row["category"] == "long"
