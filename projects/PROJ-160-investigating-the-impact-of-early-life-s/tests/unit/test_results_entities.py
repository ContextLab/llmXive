"""
Unit tests for the results entities (AnalysisResult, StatisticalModel).

These tests verify the data structures defined in code/analysis/results.py
are correctly structured and serialize/deserialize as expected.
"""

import pytest
import json
from code.analysis.results import StatisticalModel, AnalysisResult, ModelType


class TestStatisticalModel:
    """Tests for the StatisticalModel data class."""

    def test_creation_basic(self):
        """Test basic creation of a StatisticalModel."""
        model = StatisticalModel(
            model_type=ModelType.LINEAR_MIXED_EFFECTS,
            formula="CA3 ~ ACE + Age",
            dependent_variable="CA3",
            independent_variables=["ACE", "Age"],
            beta_coefficients={"ACE": 0.05, "Age": 0.12},
            sample_size=500
        )
        
        assert model.model_type == ModelType.LINEAR_MIXED_EFFECTS
        assert model.sample_size == 500
        assert model.beta_coefficients["ACE"] == 0.05

    def test_to_dict_serialization(self):
        """Test that model converts to dictionary correctly."""
        model = StatisticalModel(
            model_type=ModelType.LINEAR_MIXED_EFFECTS,
            formula="y ~ x",
            dependent_variable="y",
            independent_variables=["x"],
            beta_coefficients={"x": 1.5},
            confidence_intervals={"x": (0.5, 2.5)}
        )
        
        data = model.to_dict()
        
        assert data["model_type"] == "LMM"
        assert data["formula"] == "y ~ x"
        assert data["confidence_intervals"]["x"] == [0.5, 2.5]  # Tuples become lists in dict

    def test_to_json_serialization(self):
        """Test JSON serialization."""
        model = StatisticalModel(
            model_type=ModelType.LINEAR_MIXED_EFFECTS,
            formula="y ~ x",
            dependent_variable="y",
            independent_variables=["x"],
            beta_coefficients={"x": 1.5}
        )
        
        json_str = model.to_json()
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["model_type"] == "LMM"

    def test_from_dict_deserialization(self):
        """Test reconstruction from dictionary."""
        data = {
            "model_type": "LMM",
            "formula": "y ~ x",
            "dependent_variable": "y",
            "independent_variables": ["x"],
            "beta_coefficients": {"x": 1.5},
            "standard_errors": {"x": 0.2},
            "confidence_intervals": {"x": [1.1, 1.9]},
            "p_values": {"x": 0.01},
            "corrected_p_values": {"x": 0.03},
            "model_fit_stats": {"AIC": 100.0},
            "sample_size": 100
        }
        
        model = StatisticalModel.from_dict(data)
        
        assert model.model_type == ModelType.LINEAR_MIXED_EFFECTS
        assert model.beta_coefficients["x"] == 1.5
        assert model.confidence_intervals["x"] == (1.1, 1.9)  # Lists become tuples


class TestAnalysisResult:
    """Tests for the AnalysisResult data class."""

    def test_creation_with_model(self):
        """Test creation of AnalysisResult with a StatisticalModel."""
        model = StatisticalModel(
            model_type=ModelType.LINEAR_MIXED_EFFECTS,
            formula="CA3 ~ ACE",
            dependent_variable="CA3",
            independent_variables=["ACE"],
            beta_coefficients={"ACE": 0.05},
            p_values={"ACE": 0.03},
            corrected_p_values={"ACE": 0.09}
        )
        
        result = AnalysisResult(
            analysis_id="test-001",
            subfield="CA3",
            model=model,
            covariates_used=["ACE"],
            normalization_method="ICV"
        )
        
        assert result.analysis_id == "test-001"
        assert result.subfield == "CA3"
        assert result.normalization_method == "ICV"

    def test_default_interpretation_generation(self):
        """Test that default interpretation is generated if not provided."""
        model = StatisticalModel(
            model_type=ModelType.LINEAR_MIXED_EFFECTS,
            formula="CA3 ~ ACE",
            dependent_variable="CA3",
            independent_variables=["ACE"],
            beta_coefficients={"ACE": 0.05},
            p_values={"ACE": 0.03},
            corrected_p_values={"ACE": 0.09}  # Not significant after correction
        )
        
        result = AnalysisResult(
            analysis_id="test-002",
            subfield="CA3",
            model=model,
            covariates_used=["ACE"],
            normalization_method="ICV"
        )
        
        assert result.interpretation != ""
        assert "associational" in result.interpretation.lower()

    def test_significance_checking(self):
        """Test that significance flag is set correctly."""
        # Significant case
        model_sig = StatisticalModel(
            model_type=ModelType.LINEAR_MIXED_EFFECTS,
            formula="CA3 ~ ACE",
            dependent_variable="CA3",
            independent_variables=["ACE"],
            corrected_p_values={"ACE": 0.01}  # Significant
        )
        
        result_sig = AnalysisResult(
            analysis_id="test-003",
            subfield="CA3",
            model=model_sig,
            covariates_used=["ACE"],
            normalization_method="ICV"
        )
        
        assert result_sig.is_significant_after_correction is True

        # Non-significant case
        model_nonsig = StatisticalModel(
            model_type=ModelType.LINEAR_MIXED_EFFECTS,
            formula="CA3 ~ ACE",
            dependent_variable="CA3",
            independent_variables=["ACE"],
            corrected_p_values={"ACE": 0.15}  # Not significant
        )
        
        result_nonsig = AnalysisResult(
            analysis_id="test-004",
            subfield="CA3",
            model=model_nonsig,
            covariates_used=["ACE"],
            normalization_method="ICV"
        )
        
        assert result_nonsig.is_significant_after_correction is False

    def test_summary_report_generation(self):
        """Test that a summary report is generated."""
        model = StatisticalModel(
            model_type=ModelType.LINEAR_MIXED_EFFECTS,
            formula="CA3 ~ ACE + Age",
            dependent_variable="CA3",
            independent_variables=["ACE", "Age"],
            beta_coefficients={"ACE": 0.05, "Age": 0.12},
            standard_errors={"ACE": 0.02, "Age": 0.03},
            confidence_intervals={"ACE": (0.01, 0.09), "Age": (0.06, 0.18)},
            p_values={"ACE": 0.02, "Age": 0.001},
            corrected_p_values={"ACE": 0.06, "Age": 0.003},
            sample_size=1000
        )
        
        result = AnalysisResult(
            analysis_id="test-005",
            subfield="CA3",
            model=model,
            covariates_used=["ACE", "Age"],
            normalization_method="ICV"
        )
        
        report = result.summary_report()
        
        assert "Analysis Result: test-005" in report
        assert "CA3" in report
        assert "β=0.0500" in report
        assert "p_corr=0.0600" in report
        assert "Interpretation:" in report

    def test_serialization_roundtrip(self):
        """Test that result can be serialized and deserialized."""
        model = StatisticalModel(
            model_type=ModelType.LINEAR_MIXED_EFFECTS,
            formula="CA3 ~ ACE",
            dependent_variable="CA3",
            independent_variables=["ACE"],
            beta_coefficients={"ACE": 0.05},
            p_values={"ACE": 0.03},
            corrected_p_values={"ACE": 0.09}
        )
        
        original = AnalysisResult(
            analysis_id="test-006",
            subfield="CA3",
            model=model,
            covariates_used=["ACE"],
            normalization_method="ICV",
            transformation_applied="log"
        )
        
        # Convert to dict and back
        data = original.to_dict()
        restored = AnalysisResult.from_dict(data)
        
        assert restored.analysis_id == original.analysis_id
        assert restored.subfield == original.subfield
        assert restored.model.beta_coefficients == original.model.beta_coefficients
        assert restored.transformation_applied == "log"