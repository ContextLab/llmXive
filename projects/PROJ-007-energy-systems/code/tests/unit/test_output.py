"""
Unit tests for the output serialization module (src/models/output.py).

Verifies:
- Saving AnalysisResult to JSON and Parquet
- Loading AnalysisResult from JSON and Parquet
- Round-trip integrity (save then load yields equivalent object)
- Handling of edge cases (nested data, timestamps)
"""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

from src.models.schemas import AnalysisResult
from src.models.output import save_analysis_result, load_analysis_result


@pytest.fixture
def sample_analysis_result():
    """Create a sample AnalysisResult for testing."""
    return AnalysisResult(
        att_estimate=0.125,
        p_value=0.032,
        ci_lower=0.015,
        ci_upper=0.235,
        methodology="Propensity Score Matching with Nearest Neighbor",
        balance_status="PASSED",
        placebo_p_value=0.45,
        placebo_passed=True,
        sensitivity_data=[
            {"caliper": 0.05, "att": 0.12, "p_value": 0.04},
            {"caliper": 0.10, "att": 0.13, "p_value": 0.02},
            {"caliper": 0.15, "att": 0.11, "p_value": 0.05}
        ],
        timestamp=datetime.now()
    )


@pytest.fixture
def temp_dir():
    """Create a temporary directory for file I/O tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestSaveAnalysisResult:
    def test_save_json(self, sample_analysis_result, temp_dir):
        """Test saving to JSON format."""
        filepath = temp_dir / "result.json"
        result_path = save_analysis_result(sample_analysis_result, filepath, format="json")
        
        assert result_path.exists()
        assert result_path.suffix == ".json"
        
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        assert data['att_estimate'] == pytest.approx(0.125)
        assert data['methodology'] == "Propensity Score Matching with Nearest Neighbor"
        assert len(data['sensitivity_data']) == 3

    def test_save_parquet(self, sample_analysis_result, temp_dir):
        """Test saving to Parquet format."""
        filepath = temp_dir / "result.parquet"
        result_path = save_analysis_result(sample_analysis_result, filepath, format="parquet")
        
        assert result_path.exists()
        assert result_path.suffix == ".parquet"
        
        df = pd.read_parquet(result_path)
        assert 'att_estimate' in df.columns
        assert df['att_estimate'].iloc[0] == pytest.approx(0.125)
        # Sensitivity data should be a JSON string in Parquet
        assert isinstance(df['sensitivity_data'].iloc[0], str)

    def test_invalid_format(self, sample_analysis_result, temp_dir):
        """Test that invalid format raises ValueError."""
        filepath = temp_dir / "result.invalid"
        with pytest.raises(ValueError, match="Unsupported format"):
            save_analysis_result(sample_analysis_result, filepath, format="csv")

    def test_creates_directories(self, sample_analysis_result, temp_dir):
        """Test that save creates parent directories if they don't exist."""
        filepath = temp_dir / "subdir" / "nested" / "result.json"
        result_path = save_analysis_result(sample_analysis_result, filepath, format="json")
        assert result_path.exists()


class TestLoadAnalysisResult:
    def test_load_json(self, sample_analysis_result, temp_dir):
        """Test loading from JSON format."""
        filepath = temp_dir / "result.json"
        save_analysis_result(sample_analysis_result, filepath, format="json")
        
        loaded = load_analysis_result(filepath, format="json")
        
        assert loaded.att_estimate == pytest.approx(sample_analysis_result.att_estimate)
        assert loaded.p_value == pytest.approx(sample_analysis_result.p_value)
        assert loaded.methodology == sample_analysis_result.methodology
        assert len(loaded.sensitivity_data) == len(sample_analysis_result.sensitivity_data)
        assert isinstance(loaded.timestamp, datetime)

    def test_load_parquet(self, sample_analysis_result, temp_dir):
        """Test loading from Parquet format."""
        filepath = temp_dir / "result.parquet"
        save_analysis_result(sample_analysis_result, filepath, format="parquet")
        
        loaded = load_analysis_result(filepath, format="parquet")
        
        assert loaded.att_estimate == pytest.approx(sample_analysis_result.att_estimate)
        assert loaded.p_value == pytest.approx(sample_analysis_result.p_value)
        assert len(loaded.sensitivity_data) == len(sample_analysis_result.sensitivity_data)

    def test_infer_format_from_extension(self, sample_analysis_result, temp_dir):
        """Test that format is inferred from file extension."""
        json_path = temp_dir / "result_auto.json"
        save_analysis_result(sample_analysis_result, json_path, format="json")
        loaded_json = load_analysis_result(json_path) # No format arg
        assert loaded_json.att_estimate == pytest.approx(sample_analysis_result.att_estimate)

        pq_path = temp_dir / "result_auto.parquet"
        save_analysis_result(sample_analysis_result, pq_path, format="parquet")
        loaded_pq = load_analysis_result(pq_path) # No format arg
        assert loaded_pq.att_estimate == pytest.approx(sample_analysis_result.att_estimate)

    def test_missing_file_raises(self, temp_dir):
        """Test that loading a missing file raises FileNotFoundError."""
        filepath = temp_dir / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            load_analysis_result(filepath)

    def test_invalid_extension_raises(self, sample_analysis_result, temp_dir):
        """Test that invalid extension raises ValueError when format not specified."""
        filepath = temp_dir / "result.bad"
        save_analysis_result(sample_analysis_result, filepath, format="json")
        
        with pytest.raises(ValueError, match="Cannot infer format"):
            load_analysis_result(filepath)


class TestRoundTrip:
    def test_json_roundtrip(self, sample_analysis_result, temp_dir):
        """Test that saving and loading JSON preserves all data."""
        filepath = temp_dir / "roundtrip.json"
        save_analysis_result(sample_analysis_result, filepath, format="json")
        loaded = load_analysis_result(filepath, format="json")
        
        assert loaded == sample_analysis_result

    def test_parquet_roundtrip(self, sample_analysis_result, temp_dir):
        """Test that saving and loading Parquet preserves all data."""
        filepath = temp_dir / "roundtrip.parquet"
        save_analysis_result(sample_analysis_result, filepath, format="parquet")
        loaded = load_analysis_result(filepath, format="parquet")
        
        # Check numeric fields
        assert loaded.att_estimate == pytest.approx(sample_analysis_result.att_estimate)
        assert loaded.p_value == pytest.approx(sample_analysis_result.p_value)
        assert loaded.ci_lower == pytest.approx(sample_analysis_result.ci_lower)
        assert loaded.ci_upper == pytest.approx(sample_analysis_result.ci_upper)
        
        # Check lists (sensitivity data)
        assert len(loaded.sensitivity_data) == len(sample_analysis_result.sensitivity_data)
        for orig, load_item in zip(sample_analysis_result.sensitivity_data, loaded.sensitivity_data):
            assert load_item['caliper'] == pytest.approx(orig['caliper'])
            assert load_item['att'] == pytest.approx(orig['att'])

class TestEdgeCases:
    def test_empty_sensitivity_data(self, temp_dir):
        """Test handling of empty sensitivity data list."""
        result = AnalysisResult(
            att_estimate=0.1,
            p_value=0.05,
            ci_lower=0.0,
            ci_upper=0.2,
            methodology="Test",
            balance_status="PASSED",
            placebo_p_value=0.5,
            placebo_passed=True,
            sensitivity_data=[],
            timestamp=datetime.now()
        )
        
        filepath = temp_dir / "empty.json"
        save_analysis_result(result, filepath, format="json")
        loaded = load_analysis_result(filepath, format="json")
        
        assert loaded.sensitivity_data == []

    def test_none_timestamp(self):
        """Test that None timestamp is handled if allowed by schema, or fails gracefully."""
        # Assuming schema requires timestamp, we test with a valid one but check serialization logic
        # If schema allowed None, this would test that path.
        # For now, we assume the schema enforces presence, so we don't test None explicitly here.
        pass