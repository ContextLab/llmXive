"""
Unit tests for the AnalysisMetric model.
"""
import pytest
import json
from src.models.analysis_metric import AnalysisMetric, AnalysisMetricSchema, create_analysis_metric

class TestAnalysisMetricCreation:
    """Tests for basic creation and validation of AnalysisMetric."""

    def test_create_valid_metric(self):
        """Test creating a valid AnalysisMetric instance."""
        metric = create_analysis_metric(
            metric_name="pearson_correlation",
            feature_name="ast_depth",
            value=0.45,
            p_value=0.001,
            adjusted_p_value=0.005,
            method="pearson"
        )
        assert metric.metric_name == "pearson_correlation"
        assert metric.feature_name == "ast_depth"
        assert metric.value == 0.45
        assert metric.p_value == 0.001
        assert metric.adjusted_p_value == 0.005
        assert metric.method == "pearson"

    def test_missing_required_field(self):
        """Test that missing required fields raise a validation error."""
        with pytest.raises(Exception):
            # Missing 'method' which is required
            AnalysisMetric(
                metric_name="test",
                feature_name="test",
                value=1.0,
                p_value=0.05,
                adjusted_p_value=0.1
            )

    def test_invalid_type(self):
        """Test that invalid types are coerced or rejected."""
        # Pydantic usually coerces int to float for 'number' types
        metric = AnalysisMetric(
            metric_name="test",
            feature_name="test",
            value=1,  # int
            p_value=0.05,
            adjusted_p_value=0.1,
            method="test"
        )
        assert isinstance(metric.value, float)

class TestCreateAnalysisMetricFactory:
    """Tests for the factory function."""

    def test_factory_creates_instance(self):
        """Test that the factory returns an instance of AnalysisMetric."""
        metric = create_analysis_metric(
            metric_name="f1_score",
            feature_name="node_count",
            value=0.85,
            p_value=0.0,
            adjusted_p_value=0.0,
            method="f1"
        )
        assert isinstance(metric, AnalysisMetric)

class TestAnalysisMetricSerialization:
    """Tests for serialization methods."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metric = create_analysis_metric(
            metric_name="test",
            feature_name="test",
            value=1.0,
            p_value=0.05,
            adjusted_p_value=0.1,
            method="test"
        )
        data = metric.to_dict()
        assert data["metric_name"] == "test"
        assert data["value"] == 1.0
        assert "p_value" in data

    def test_to_json(self):
        """Test conversion to JSON string."""
        metric = create_analysis_metric(
            metric_name="test",
            feature_name="test",
            value=1.0,
            p_value=0.05,
            adjusted_p_value=0.1,
            method="test"
        )
        json_str = metric.to_json()
        parsed = json.loads(json_str)
        assert parsed["metric_name"] == "test"
        assert parsed["method"] == "test"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "metric_name": "mcc",
            "feature_name": "sanitization_present",
            "value": 0.6,
            "p_value": 0.02,
            "adjusted_p_value": 0.08,
            "method": "mcc"
        }
        metric = AnalysisMetric.from_dict(data)
        assert metric.metric_name == "mcc"
        assert metric.feature_name == "sanitization_present"

    def test_from_json(self):
        """Test creation from JSON string."""
        json_str = json.dumps({
            "metric_name": "roc_auc",
            "feature_name": "embedding_similarity_score",
            "value": 0.92,
            "p_value": 0.0001,
            "adjusted_p_value": 0.0005,
            "method": "roc"
        })
        metric = AnalysisMetric.from_json(json_str)
        assert metric.metric_name == "roc_auc"
        assert metric.value == 0.92