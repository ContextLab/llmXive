"""
Unit tests for Pydantic models defined in src/models/schemas.py.

Tests verify model instantiation, validation, and basic schema properties.
"""
import pytest
from src.models.schemas import (
    SleepMetric,
    MicrobiomeSample,
    CorrelationResult,
    models_to_dict
)


class TestSleepMetric:
    """Tests for the SleepMetric model."""

    def test_sleep_metric_instantiation(self):
        """Test that a valid SleepMetric can be instantiated."""
        data = {
            "sample_id": "S123",
            "sleep_efficiency": 0.85,
            "sleep_duration_hours": 7.5,
            "sleep_latency_minutes": 10.0,
            "awakenings_count": 1
        }
        metric = SleepMetric(**data)
        
        assert metric.sample_id == "S123"
        assert metric.sleep_efficiency == 0.85
        assert metric.sleep_duration_hours == 7.5
        assert metric.sleep_latency_minutes == 10.0
        assert metric.awakenings_count == 1

    def test_sleep_metric_minimal(self):
        """Test instantiation with only required fields."""
        data = {
            "sample_id": "S124",
            "sleep_efficiency": 0.90,
            "sleep_duration_hours": 6.0
        }
        metric = SleepMetric(**data)
        
        assert metric.sample_id == "S124"
        assert metric.sleep_efficiency == 0.90
        assert metric.sleep_duration_hours == 6.0
        assert metric.sleep_latency_minutes is None
        assert metric.awakenings_count is None

    def test_sleep_efficiency_validation(self):
        """Test that sleep_efficiency must be between 0 and 1."""
        with pytest.raises(Exception):
            SleepMetric(
                sample_id="S125",
                sleep_efficiency=1.5,
                sleep_duration_hours=5.0
            )
        
        with pytest.raises(Exception):
            SleepMetric(
                sample_id="S126",
                sleep_efficiency=-0.1,
                sleep_duration_hours=5.0
            )

    def test_sleep_duration_validation(self):
        """Test that sleep_duration_hours must be positive."""
        with pytest.raises(Exception):
            SleepMetric(
                sample_id="S127",
                sleep_efficiency=0.8,
                sleep_duration_hours=0
            )
        
        with pytest.raises(Exception):
            SleepMetric(
                sample_id="S128",
                sleep_efficiency=0.8,
                sleep_duration_hours=-1.0
            )


class TestMicrobiomeSample:
    """Tests for the MicrobiomeSample model."""

    def test_microbiome_sample_instantiation(self):
        """Test that a valid MicrobiomeSample can be instantiated."""
        data = {
            "sample_id": "M001",
            "antibiotic_use_last_3m": False,
            "sequencing_depth": 20000,
            "shannon_index": 3.5,
            "simpson_index": 0.9,
            "observed_otus": 300,
            "otu_counts": {"OTU_A": 100, "OTU_B": 50}
        }
        sample = MicrobiomeSample(**data)
        
        assert sample.sample_id == "M001"
        assert sample.antibiotic_use_last_3m is False
        assert sample.sequencing_depth == 20000
        assert sample.shannon_index == 3.5
        assert sample.otu_counts == {"OTU_A": 100, "OTU_B": 50}

    def test_microbiome_sample_empty_otu_counts(self):
        """Test that empty otu_counts is allowed (defaults to empty dict)."""
        data = {
            "sample_id": "M002",
            "antibiotic_use_last_3m": True,
            "sequencing_depth": 5000,
            "otu_counts": {}
        }
        sample = MicrobiomeSample(**data)
        assert sample.otu_counts == {}

    def test_otu_counts_validation(self):
        """Test that otu_counts values must be non-negative integers."""
        with pytest.raises(Exception):
            MicrobiomeSample(
                sample_id="M003",
                antibiotic_use_last_3m=False,
                sequencing_depth=1000,
                otu_counts={"OTU_X": -5}
            )
        
        with pytest.raises(Exception):
            MicrobiomeSample(
                sample_id="M004",
                antibiotic_use_last_3m=False,
                sequencing_depth=1000,
                otu_counts={"OTU_Y": "invalid"}
            )


class TestCorrelationResult:
    """Tests for the CorrelationResult model."""

    def test_correlation_result_instantiation(self):
        """Test that a valid CorrelationResult can be instantiated."""
        data = {
            "diversity_metric": "shannon_index",
            "sleep_variable": "sleep_efficiency",
            "spearman_r": -0.35,
            "p_value": 0.002,
            "q_value": 0.01,
            "sample_count": 150,
            "is_moderate": True,
            "is_meaningful": True
        }
        result = CorrelationResult(**data)
        
        assert result.diversity_metric == "shannon_index"
        assert result.sleep_variable == "sleep_efficiency"
        assert result.spearman_r == -0.35
        assert result.p_value == 0.002
        assert result.q_value == 0.01
        assert result.is_moderate is True
        assert result.is_meaningful is True

    def test_r_value_bounds(self):
        """Test that spearman_r must be between -1 and 1."""
        with pytest.raises(Exception):
            CorrelationResult(
                diversity_metric="x",
                sleep_variable="y",
                spearman_r=1.5,
                p_value=0.05,
                q_value=0.1,
                sample_count=10,
                is_moderate=False,
                is_meaningful=False
            )
        
        with pytest.raises(Exception):
            CorrelationResult(
                diversity_metric="x",
                sleep_variable="y",
                spearman_r=-1.5,
                p_value=0.05,
                q_value=0.1,
                sample_count=10,
                is_moderate=False,
                is_meaningful=False
            )

    def test_p_value_bounds(self):
        """Test that p-value must be between 0 and 1."""
        with pytest.raises(Exception):
            CorrelationResult(
                diversity_metric="x",
                sleep_variable="y",
                spearman_r=0.3,
                p_value=1.5,
                q_value=0.1,
                sample_count=10,
                is_moderate=False,
                is_meaningful=False
            )


class TestModelsToDict:
    """Tests for the utility function models_to_dict."""

    def test_models_to_dict_returns_schema(self):
        """Test that models_to_dict returns a dictionary with schema keys."""
        result = models_to_dict()
        
        assert isinstance(result, dict)
        assert "SleepMetric" in result
        assert "MicrobiomeSample" in result
        assert "CorrelationResult" in result
        
        # Check that values are schemas (dictionaries)
        for key, val in result.items():
            assert isinstance(val, dict)
            assert "properties" in val