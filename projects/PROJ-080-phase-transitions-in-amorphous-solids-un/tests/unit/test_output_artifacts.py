import pytest
import pandas as pd
import json
from pathlib import Path
import numpy as np

class TestOutputArtifacts:
    """Tests for T017: Output artifacts generation."""
    
    @pytest.fixture
    def output_dir(self):
        """Create a temporary output directory."""
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir
    
    def test_precursor_metrics_csv_exists(self, output_dir):
        """Test that precursor_metrics.csv is created."""
        csv_path = output_dir / "precursor_metrics.csv"
        assert csv_path.exists(), "precursor_metrics.csv should exist"
        
        # Check it's not empty
        df = pd.read_csv(csv_path)
        assert not df.empty, "precursor_metrics.csv should not be empty"
        
        # Check for D2_min columns
        assert any("particle" in col for col in df.columns), \
            "Should have particle columns for D2_min values"
    
    def test_yield_flags_json_exists(self, output_dir):
        """Test that yield_flags.json is created."""
        json_path = output_dir / "yield_flags.json"
        assert json_path.exists(), "yield_flags.json should exist"
        
        # Check it's valid JSON
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Check required fields
        assert "flag" in data, "yield_flags.json should have 'flag' field"
        assert "yield_events_detected" in data, "yield_flags.json should have 'yield_events_detected'"
        assert "total_count" in data, "yield_flags.json should have 'total_count'"
        
        # Check flag values
        valid_flags = ["single-yield", "multi-yield", "indeterminate"]
        assert data["flag"] in valid_flags, f"Flag should be one of {valid_flags}"
    
    def test_yield_flags_structure(self, output_dir):
        """Test the structure of yield_flags.json."""
        json_path = output_dir / "yield_flags.json"
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Check yield events structure
        if data["total_count"] > 0:
            assert isinstance(data["yield_events_detected"], list), \
                "yield_events_detected should be a list"
            
            for event in data["yield_events_detected"]:
                assert "event_id" in event, "Event should have event_id"
                assert "peak_index" in event, "Event should have peak_index"
                assert "peak_value" in event, "Event should have peak_value"
                assert "drop_magnitude" in event, "Event should have drop_magnitude"
                assert "drop_percentage" in event, "Event should have drop_percentage"
    
    def test_d2_min_values_are_numeric(self, output_dir):
        """Test that D2_min values are numeric."""
        csv_path = output_dir / "precursor_metrics.csv"
        df = pd.read_csv(csv_path)
        
        # Check all columns are numeric (except index)
        for col in df.columns:
            if "particle" in col:
                assert pd.api.types.is_numeric_dtype(df[col]), \
                    f"Column {col} should be numeric"
    
    def test_multi_yield_flagging(self, output_dir):
        """Test that multi-yield events are properly flagged."""
        json_path = output_dir / "yield_flags.json"
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        if data["total_count"] > 1:
            assert data["flag"] == "multi-yield", \
                "Should be flagged as multi-yield when >1 events detected"
            assert data["status"] == "Complex plasticity detected", \
                "Status should indicate complex plasticity"
    
    def test_indeterminate_flagging(self, output_dir):
        """Test that indeterminate cases are properly flagged."""
        json_path = output_dir / "yield_flags.json"
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        if data["total_count"] == 0:
            assert data["flag"] == "indeterminate", \
                "Should be flagged as indeterminate when no events detected"
            assert data["status"] == "No sharp stress peak detected", \
                "Status should indicate no sharp peak detected"
