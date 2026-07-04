import pytest
from src.models.schemas import (
    SleepMetric,
    MicrobiomeSample,
    CorrelationResult,
    models_to_dict
)
from datetime import date
from typing import List, Dict, Any


class TestSleepMetric:
    """Unit tests for SleepMetric Pydantic model."""

    def test_sleep_metric_instantiation(self):
        """Test that SleepMetric can be instantiated with valid data."""
        sleep_data = SleepMetric(
            sample_id="S001",
            sleep_efficiency=0.85,
            sleep_duration_hours=7.5,
            sleep_latency_minutes=15.0,
            awakenings_count=2,
            measurement_date=date(2023, 10, 15)
        )

        assert sleep_data.sample_id == "S001"
        assert sleep_data.sleep_efficiency == 0.85
        assert sleep_data.sleep_duration_hours == 7.5
        assert sleep_data.sleep_latency_minutes == 15.0
        assert sleep_data.awakenings_count == 2
        assert sleep_data.measurement_date == date(2023, 10, 15)

    def test_sleep_metric_with_optional_fields(self):
        """Test SleepMetric instantiation with optional fields omitted."""
        sleep_data = SleepMetric(
            sample_id="S002",
            sleep_efficiency=0.90,
            sleep_duration_hours=8.0
        )

        assert sleep_data.sample_id == "S002"
        assert sleep_data.sleep_efficiency == 0.90
        assert sleep_data.sleep_duration_hours == 8.0
        assert sleep_data.sleep_latency_minutes is None
        assert sleep_data.awakenings_count is None
        assert sleep_data.measurement_date is None

    def test_sleep_metric_validation_efficiency_range(self):
        """Test that sleep_efficiency is validated to be between 0 and 1."""
        with pytest.raises(ValueError):
            SleepMetric(
                sample_id="S003",
                sleep_efficiency=1.5,
                sleep_duration_hours=7.0
            )

        with pytest.raises(ValueError):
            SleepMetric(
                sample_id="S004",
                sleep_efficiency=-0.1,
                sleep_duration_hours=7.0
            )

    def test_sleep_metric_serialization(self):
        """Test that SleepMetric can be serialized to dict."""
        sleep_data = SleepMetric(
            sample_id="S005",
            sleep_efficiency=0.80,
            sleep_duration_hours=6.5,
            sleep_latency_minutes=20.0,
            awakenings_count=3,
            measurement_date=date(2023, 10, 20)
        )

        data_dict = sleep_data.model_dump()
        assert isinstance(data_dict, dict)
        assert data_dict["sample_id"] == "S005"
        assert data_dict["sleep_efficiency"] == 0.80


class TestMicrobiomeSample:
    """Unit tests for MicrobiomeSample Pydantic model."""

    def test_microbiome_sample_instantiation(self):
        """Test that MicrobiomeSample can be instantiated with valid data."""
        sample = MicrobiomeSample(
            sample_id="M001",
            antibiotic_use_last_3m=False,
            phylum_firmicutes=0.45,
            phylum_bacteroidetes=0.35,
            phylum_actinobacteria=0.05,
            phylum_proteobacteria=0.08,
            phylum_other=0.07,
            shannon_diversity=3.2,
            simpson_diversity=0.85,
            observed_otus=1250,
            collection_date=date(2023, 10, 15)
        )

        assert sample.sample_id == "M001"
        assert sample.antibiotic_use_last_3m is False
        assert sample.phylum_firmicutes == 0.45
        assert sample.phylum_bacteroidetes == 0.35
        assert sample.shannon_diversity == 3.2
        assert sample.simpson_diversity == 0.85
        assert sample.observed_otus == 1250
        assert sample.collection_date == date(2023, 10, 15)

    def test_microbiome_sample_with_optional_fields(self):
        """Test MicrobiomeSample instantiation with optional fields omitted."""
        sample = MicrobiomeSample(
            sample_id="M002",
            antibiotic_use_last_3m=True,
            phylum_firmicutes=0.50,
            phylum_bacteroidetes=0.30
        )

        assert sample.sample_id == "M002"
        assert sample.antibiotic_use_last_3m is True
        assert sample.phylum_firmicutes == 0.50
        assert sample.phylum_bacteroidetes == 0.30
        assert sample.phylum_actinobacteria is None
        assert sample.phylum_proteobacteria is None
        assert sample.phylum_other is None
        assert sample.shannon_diversity is None
        assert sample.simpson_diversity is None
        assert sample.observed_otus is None
        assert sample.collection_date is None

    def test_microbiome_sample_validation_proportions(self):
        """Test that phylum proportions are validated to be between 0 and 1."""
        with pytest.raises(ValueError):
            MicrobiomeSample(
                sample_id="M003",
                antibiotic_use_last_3m=False,
                phylum_firmicutes=1.5
            )

        with pytest.raises(ValueError):
            MicrobiomeSample(
                sample_id="M004",
                antibiotic_use_last_3m=False,
                phylum_firmicutes=-0.1
            )

    def test_microbiome_sample_serialization(self):
        """Test that MicrobiomeSample can be serialized to dict."""
        sample = MicrobiomeSample(
            sample_id="M005",
            antibiotic_use_last_3m=False,
            phylum_firmicutes=0.40,
            phylum_bacteroidetes=0.40,
            shannon_diversity=3.5
        )

        data_dict = sample.model_dump()
        assert isinstance(data_dict, dict)
        assert data_dict["sample_id"] == "M005"
        assert data_dict["antibiotic_use_last_3m"] is False
        assert data_dict["phylum_firmicutes"] == 0.40


class TestCorrelationResult:
    """Unit tests for CorrelationResult Pydantic model."""

    def test_correlation_result_instantiation(self):
        """Test that CorrelationResult can be instantiated with valid data."""
        result = CorrelationResult(
            metric_a="shannon_diversity",
            metric_b="sleep_efficiency",
            correlation_coefficient=0.35,
            p_value=0.002,
            q_value=0.015,
            sample_size=150,
            is_moderate=True,
            is_meaningful=True
        )

        assert result.metric_a == "shannon_diversity"
        assert result.metric_b == "sleep_efficiency"
        assert result.correlation_coefficient == 0.35
        assert result.p_value == 0.002
        assert result.q_value == 0.015
        assert result.sample_size == 150
        assert result.is_moderate is True
        assert result.is_meaningful is True

    def test_correlation_result_weak_correlation(self):
        """Test CorrelationResult with weak correlation (|r| <= 0.3)."""
        result = CorrelationResult(
            metric_a="simpson_diversity",
            metric_b="sleep_latency_minutes",
            correlation_coefficient=0.15,
            p_value=0.08,
            q_value=0.12,
            sample_size=150,
            is_moderate=False,
            is_meaningful=False
        )

        assert result.is_moderate is False
        assert result.is_meaningful is False

    def test_correlation_result_significant_but_weak(self):
        """Test CorrelationResult where p-value is significant but correlation is weak."""
        result = CorrelationResult(
            metric_a="observed_otus",
            metric_b="sleep_duration_hours",
            correlation_coefficient=0.25,
            p_value=0.001,
            q_value=0.005,
            sample_size=200,
            is_moderate=False,
            is_meaningful=False
        )

        # is_moderate should be False because |r| <= 0.3
        assert result.is_moderate is False
        # is_meaningful requires both q < 0.05 AND |r| > 0.3
        assert result.is_meaningful is False

    def test_correlation_result_serialization(self):
        """Test that CorrelationResult can be serialized to dict."""
        result = CorrelationResult(
            metric_a="shannon_diversity",
            metric_b="sleep_efficiency",
            correlation_coefficient=0.42,
            p_value=0.001,
            q_value=0.008,
            sample_size=180,
            is_moderate=True,
            is_meaningful=True
        )

        data_dict = result.model_dump()
        assert isinstance(data_dict, dict)
        assert data_dict["metric_a"] == "shannon_diversity"
        assert data_dict["correlation_coefficient"] == 0.42


class TestModelsToDict:
    """Unit tests for the models_to_dict helper function."""

    def test_models_to_dict_sleep_metric(self):
        """Test models_to_dict with SleepMetric instance."""
        sleep_data = SleepMetric(
            sample_id="S001",
            sleep_efficiency=0.85,
            sleep_duration_hours=7.5
        )

        result = models_to_dict(sleep_data)
        assert isinstance(result, dict)
        assert result["sample_id"] == "S001"
        assert result["sleep_efficiency"] == 0.85

    def test_models_to_dict_microbiome_sample(self):
        """Test models_to_dict with MicrobiomeSample instance."""
        sample = MicrobiomeSample(
            sample_id="M001",
            antibiotic_use_last_3m=False,
            phylum_firmicutes=0.45
        )

        result = models_to_dict(sample)
        assert isinstance(result, dict)
        assert result["sample_id"] == "M001"
        assert result["antibiotic_use_last_3m"] is False

    def test_models_to_dict_correlation_result(self):
        """Test models_to_dict with CorrelationResult instance."""
        result_obj = CorrelationResult(
            metric_a="shannon_diversity",
            metric_b="sleep_efficiency",
            correlation_coefficient=0.35,
            p_value=0.002,
            q_value=0.015,
            sample_size=150,
            is_moderate=True,
            is_meaningful=True
        )

        result = models_to_dict(result_obj)
        assert isinstance(result, dict)
        assert result["metric_a"] == "shannon_diversity"
        assert result["correlation_coefficient"] == 0.35

    def test_models_to_dict_with_list(self):
        """Test models_to_dict with a list of model instances."""
        sleep_list = [
            SleepMetric(sample_id="S001", sleep_efficiency=0.80, sleep_duration_hours=7.0),
            SleepMetric(sample_id="S002", sleep_efficiency=0.90, sleep_duration_hours=8.0)
        ]

        result = models_to_dict(sleep_list)
        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0], dict)
        assert result[0]["sample_id"] == "S001"
        assert result[1]["sample_id"] == "S002"

    def test_models_to_dict_with_none(self):
        """Test models_to_dict with None input."""
        result = models_to_dict(None)
        assert result is None