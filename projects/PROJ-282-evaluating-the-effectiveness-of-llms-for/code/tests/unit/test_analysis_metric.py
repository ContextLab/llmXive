"""
Unit tests for the AnalysisMetric model (T009e).
Verifies that the generated model matches the schema and behaves correctly.
"""
import pytest
import json
from src.models.analysis_metric import AnalysisMetric, AnalysisMetricSchema, create_analysis_metric

class TestAnalysisMetricCreation:
    def test_create_valid_metric(self):
        """Test creating a valid AnalysisMetric."""
        metric = create_analysis_metric(
            metric_name="Pearson Correlation",
            feature_name="ast_depth",
            value=0.85,
            p_value=0.001,
            adjusted_p_value=0.005,
            method="Bonferroni"
        )
        assert metric.metric_name == "Pearson Correlation"
        assert metric.feature_name == "ast_depth"
        assert metric.value == 0.85
        assert metric.p_value == 0.001
        assert metric.adjusted_p_value == 0.005
        assert metric.method == "Bonferroni"

    def test_create_metric_from_dict(self):
        """Test creating a metric from a dictionary."""
        data = {
            "metric_name": "McNemar",
            "feature_name": "taint_api_count",
            "value": 12.5,
            "p_value": 0.0001,
            "adjusted_p_value": 0.001,
            "method": "Exact Binomial"
        }
        metric = AnalysisMetric(**data)
        assert metric.metric_name == "McNemar"
        assert metric.feature_name == "taint_api_count"
        assert metric.method == "Exact Binomial"

class TestAnalysisMetricValidation:
    def test_missing_required_field(self):
        """Test that missing required fields raise an error."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            AnalysisMetric(
                metric_name="Test",
                # missing feature_name, value, etc.
            )

    def test_invalid_type(self):
        """Test that invalid types are caught."""
        with pytest.raises(Exception):
            AnalysisMetric(
                metric_name="Test",
                feature_name="feat",
                value="not_a_number",  # Should be float
                p_value=0.1,
                adjusted_p_value=0.2,
                method="Test"
            )

class TestAnalysisMetricSerialization:
    def test_to_dict(self):
        """Test serialization to dictionary."""
        metric = create_analysis_metric(
            metric_name="Test",
            feature_name="feat",
            value=1.0,
            p_value=0.05,
            adjusted_p_value=0.1,
            method="Test"
        )
        data = metric.dict()
        assert data["metric_name"] == "Test"
        assert data["value"] == 1.0
        assert isinstance(data["p_value"], float)

    def test_to_json(self):
        """Test serialization to JSON string."""
        metric = create_analysis_metric(
            metric_name="Test",
            feature_name="feat",
            value=1.0,
            p_value=0.05,
            adjusted_p_value=0.1,
            method="Test"
        )
        json_str = metric.json()
        parsed = json.loads(json_str)
        assert parsed["metric_name"] == "Test"
        assert "adjusted_p_value" in parsed

class TestSchemaDrift:
    def test_schema_matches_contract(self):
        """
        Verify that the generated schema fields match the expected contract
        from contracts/analysis_metric.schema.yaml.
        """
        # Expected fields based on T009d schema
        expected_fields = {
            "metric_name",
            "feature_name",
            "value",
            "p_value",
            "adjusted_p_value",
            "method"
        }
        actual_fields = set(AnalysisMetricSchema.model_fields.keys())
        
        assert expected_fields == actual_fields, (
            f"Schema fields mismatch. Expected: {expected_fields}, Got: {actual_fields}"
        )