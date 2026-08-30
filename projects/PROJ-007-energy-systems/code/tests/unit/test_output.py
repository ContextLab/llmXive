"""
Unit tests for the output serialization module (src/models/output.py).

Tests cover:
- JSON serialization and deserialization
- Parquet serialization and deserialization
- Round-trip integrity
- Error handling for invalid formats and missing files
"""
import pytest
import json
import tempfile
from pathlib import Path
from src.models.schemas import AnalysisResult
from src.models.output import (
    save_analysis_result,
    load_analysis_result,
    _save_to_json,
    _save_to_parquet,
    _load_from_json,
    _load_from_parquet
)


@pytest.fixture
def sample_analysis_result():
    """Create a sample AnalysisResult for testing."""
    return AnalysisResult(
        att_estimate=125.45,
        att_std_error=15.20,
        p_value=0.003,
        confidence_interval=(95.67, 155.23),
        methodology="OLS with cluster-robust SE",
        balance_status="PASS",
        placebo_passed=True,
        n_treatment=150,
        n_control=148,
        caliper_used=0.05,
        sensitivity_analysis={
            "caliper_0.01": {"att": 120.1, "p": 0.005},
            "caliper_0.10": {"att": 130.2, "p": 0.002}
        }
    )


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestSaveAnalysisResult:
    def test_save_json_success(self, sample_analysis_result, temp_dir):
        """Test successful JSON serialization."""
        output_path = temp_dir / "result.json"
        result_path = save_analysis_result(sample_analysis_result, str(output_path), "json")
        
        assert result_path.exists()
        assert result_path.suffix == ".json"
        
        # Verify file content is valid JSON
        with open(result_path, "r") as f:
            data = json.load(f)
        
        assert data["att_estimate"] == 125.45
        assert data["p_value"] == 0.003
        assert "_exported_at" in data

    def test_save_parquet_success(self, sample_analysis_result, temp_dir):
        """Test successful Parquet serialization."""
        output_path = temp_dir / "result.parquet"
        result_path = save_analysis_result(sample_analysis_result, str(output_path), "parquet")
        
        assert result_path.exists()
        assert result_path.suffix == ".parquet"

    def test_invalid_format_raises_error(self, sample_analysis_result, temp_dir):
        """Test that invalid format raises ValueError."""
        output_path = temp_dir / "result.csv"
        
        with pytest.raises(ValueError, match="Unsupported format"):
            save_analysis_result(sample_analysis_result, str(output_path), "csv")

    def test_missing_directory_raises_error(self, sample_analysis_result):
        """Test that missing output directory raises FileNotFoundError."""
        output_path = "/nonexistent/directory/result.json"
        
        with pytest.raises(FileNotFoundError):
            save_analysis_result(sample_analysis_result, output_path)


class TestLoadAnalysisResult:
    def test_load_json_success(self, sample_analysis_result, temp_dir):
        """Test successful JSON deserialization."""
        # Save first
        output_path = temp_dir / "result.json"
        save_analysis_result(sample_analysis_result, str(output_path), "json")
        
        # Load back
        loaded = load_analysis_result(str(output_path), "json")
        
        assert loaded.att_estimate == sample_analysis_result.att_estimate
        assert loaded.p_value == sample_analysis_result.p_value
        assert loaded.confidence_interval == sample_analysis_result.confidence_interval
        assert loaded.sensitivity_analysis == sample_analysis_result.sensitivity_analysis

    def test_load_parquet_success(self, sample_analysis_result, temp_dir):
        """Test successful Parquet deserialization."""
        # Save first
        output_path = temp_dir / "result.parquet"
        save_analysis_result(sample_analysis_result, str(output_path), "parquet")
        
        # Load back
        loaded = load_analysis_result(str(output_path), "parquet")
        
        assert loaded.att_estimate == sample_analysis_result.att_estimate
        assert loaded.p_value == sample_analysis_result.p_value
        assert loaded.confidence_interval == sample_analysis_result.confidence_interval

    def test_load_missing_file_raises_error(self, temp_dir):
        """Test that missing input file raises FileNotFoundError."""
        missing_path = temp_dir / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            load_analysis_result(str(missing_path), "json")

    def test_load_invalid_format_raises_error(self, temp_dir):
        """Test that invalid format raises ValueError."""
        output_path = temp_dir / "result.json"
        save_analysis_result(sample_analysis_result, str(output_path), "json")
        
        with pytest.raises(ValueError, match="Unsupported format"):
            load_analysis_result(str(output_path), "csv")


class TestRoundTrip:
    def test_json_round_trip(self, sample_analysis_result, temp_dir):
        """Test that JSON save/load preserves all data."""
        output_path = temp_dir / "result.json"
        save_analysis_result(sample_analysis_result, str(output_path), "json")
        loaded = load_analysis_result(str(output_path), "json")
        
        assert loaded == sample_analysis_result

    def test_parquet_round_trip(self, sample_analysis_result, temp_dir):
        """Test that Parquet save/load preserves all data."""
        output_path = temp_dir / "result.parquet"
        save_analysis_result(sample_analysis_result, str(output_path), "parquet")
        loaded = load_analysis_result(str(output_path), "parquet")
        
        assert loaded.att_estimate == sample_analysis_result.att_estimate
        assert loaded.p_value == sample_analysis_result.p_value
        assert loaded.confidence_interval == sample_analysis_result.confidence_interval
        assert loaded.methodology == sample_analysis_result.methodology
        assert loaded.balance_status == sample_analysis_result.balance_status
        assert loaded.placebo_passed == sample_analysis_result.placebo_passed
        assert loaded.n_treatment == sample_analysis_result.n_treatment
        assert loaded.n_control == sample_analysis_result.n_control
        assert loaded.caliper_used == sample_analysis_result.caliper_used
        assert loaded.sensitivity_analysis == sample_analysis_result.sensitivity_analysis


class TestEdgeCases:
    def test_empty_sensitivity_analysis(self, temp_dir):
        """Test handling of None sensitivity analysis."""
        result = AnalysisResult(
            att_estimate=100.0,
            att_std_error=10.0,
            p_value=0.01,
            confidence_interval=(80.0, 120.0),
            methodology="Test",
            balance_status="PASS",
            placebo_passed=True,
            n_treatment=50,
            n_control=50,
            caliper_used=0.05,
            sensitivity_analysis=None
        )
        
        output_path = temp_dir / "result_no_sens.json"
        save_analysis_result(result, str(output_path), "json")
        loaded = load_analysis_result(str(output_path), "json")
        
        assert loaded.sensitivity_analysis is None

    def test_large_numbers(self, temp_dir):
        """Test handling of large numerical values."""
        result = AnalysisResult(
            att_estimate=1e10,
            att_std_error=1e8,
            p_value=1e-10,
            confidence_interval=(0.99e10, 1.01e10),
            methodology="Test",
            balance_status="PASS",
            placebo_passed=True,
            n_treatment=1000000,
            n_control=1000000,
            caliper_used=0.001,
            sensitivity_analysis={}
        )
        
        output_path = temp_dir / "result_large.json"
        save_analysis_result(result, str(output_path), "json")
        loaded = load_analysis_result(str(output_path), "json")
        
        assert loaded.att_estimate == result.att_estimate
        assert loaded.p_value == result.p_value