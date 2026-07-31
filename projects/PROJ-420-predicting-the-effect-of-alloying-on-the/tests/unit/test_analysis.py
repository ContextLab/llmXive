import pytest
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

from analysis import validate_framing, run_perturbation_sensitivity_analysis
from config import get_config

class TestAssociationalFramingVerification:
    """Tests for T030b: Associational framing verification."""

    def test_validate_framing_no_causal_phrases(self, tmp_path):
        """Test that a report without causal phrases passes verification."""
        report_content = """
        # Final Report

        ## Results
        The analysis shows a correlation between Cu content and Poisson's ratio.
        We observe that higher Cu levels are associated with increased stiffness.

        ## Framing
        These findings should be interpreted as associational, not causal.
        The data is observational and lacks randomization.
        """
        
        report_path = tmp_path / "final_report.md"
        output_path = tmp_path / "framing_check.json"
        
        report_path.write_text(report_content)
        
        result = validate_framing(str(report_path), str(output_path))
        
        assert result["framing_verified"] is True
        assert len(result["detected_causal_phrases"]) == 0
        assert output_path.exists()
        
        # Verify JSON structure
        with open(output_path) as f:
            saved_result = json.load(f)
        assert saved_result["framing_verified"] is True

    def test_validate_framing_with_causal_phrases(self, tmp_path):
        """Test that a report with causal phrases fails verification."""
        report_content = """
        # Final Report

        ## Results
        Adding Cu causes an increase in Poisson's ratio.
        Higher Mg levels leads to reduced ductility.
        Si determines the overall mechanical properties.
        """
        
        report_path = tmp_path / "final_report.md"
        output_path = tmp_path / "framing_check.json"
        
        report_path.write_text(report_content)
        
        result = validate_framing(str(report_path), str(output_path))
        
        assert result["framing_verified"] is False
        assert len(result["detected_causal_phrases"]) > 0
        assert "causes" in result["detected_causal_phrases"]
        assert "leads to" in result["detected_causal_phrases"]
        assert "determines" in result["detected_causal_phrases"]

    def test_validate_framing_missing_report(self, tmp_path):
        """Test that missing report file raises FileNotFoundError."""
        output_path = tmp_path / "framing_check.json"
        
        with pytest.raises(FileNotFoundError):
            validate_framing(str(tmp_path / "nonexistent.md"), str(output_path))

    def test_validate_framing_output_structure(self, tmp_path):
        """Test that output JSON has correct structure."""
        report_content = "This report has no issues."
        report_path = tmp_path / "final_report.md"
        output_path = tmp_path / "framing_check.json"
        
        report_path.write_text(report_content)
        
        result = validate_framing(str(report_path), str(output_path))
        
        assert "framing_verified" in result
        assert "detected_causal_phrases" in result
        assert "total_causal_phrases_found" in result
        assert "report_path" in result
        assert "verification_timestamp" in result
        assert isinstance(result["detected_causal_phrases"], list)
        assert isinstance(result["framing_verified"], bool)

    def test_validate_framing_edge_cases(self, tmp_path):
        """Test edge cases like empty report, special characters."""
        # Empty report
        report_path = tmp_path / "empty_report.md"
        output_path = tmp_path / "empty_check.json"
        report_path.write_text("")
        
        result = validate_framing(str(report_path), str(output_path))
        assert result["framing_verified"] is True  # No causal phrases in empty text

        # Report with special characters
        report_path = tmp_path / "special_report.md"
        output_path = tmp_path / "special_check.json"
        report_path.write_text("Special chars: © ® ™ and symbols like → ↓ ↑")
        
        result = validate_framing(str(report_path), str(output_path))
        assert result["framing_verified"] is True

class TestPerturbationSensitivityAnalysis:
    """Tests for T027b: Perturbation-based sensitivity analysis."""

    def test_run_perturbation_analysis_creates_output(self, tmp_path, monkeypatch):
        """Test that perturbation analysis creates the expected output file."""
        # Create mock data files
        raw_data = pd.DataFrame({
            'Cu': [0.05, 0.06, 0.04],
            'Mg': [0.03, 0.04, 0.02],
            'Si': [0.02, 0.03, 0.01],
            'Zn': [0.01, 0.02, 0.005],
            'Mn': [0.005, 0.01, 0.003],
            'poissons_ratio': [0.34, 0.35, 0.33]
        })
        
        ilr_data = pd.DataFrame({
            'ilr_1': [0.1, 0.11, 0.09],
            'ilr_2': [0.2, 0.21, 0.19],
            'ilr_3': [0.3, 0.31, 0.29],
            'poissons_ratio': [0.34, 0.35, 0.33]
        })
        
        raw_path = tmp_path / "filtered_alloys.csv"
        ilr_path = tmp_path / "filtered_alloys_ilr.csv"
        output_path = tmp_path / "element_importance.csv"
        
        raw_data.to_csv(raw_path, index=False)
        ilr_data.to_csv(ilr_path, index=False)
        
        # Mock model
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0.34, 0.35, 0.33])
        
        with patch('analysis.load_trained_model', return_value=mock_model):
            result = run_perturbation_sensitivity_analysis(
                mock_model, str(raw_path), str(ilr_path), str(output_path)
            )
        
        assert output_path.exists()
        assert isinstance(result, dict)
        assert len(result) == 5  # 5 elements
        
        # Verify output CSV structure
        df = pd.read_csv(output_path)
        assert 'element' in df.columns
        assert 'importance_score' in df.columns
        assert 'std_dev' in df.columns
        assert len(df) == 5

    def test_perturbation_analysis_random_state(self, tmp_path, monkeypatch):
        """Test that perturbation analysis uses random_state=42."""
        # This test verifies that the function uses a fixed random state
        # for reproducibility
        raw_data = pd.DataFrame({
            'Cu': [0.05],
            'Mg': [0.03],
            'Si': [0.02],
            'Zn': [0.01],
            'Mn': [0.005],
            'poissons_ratio': [0.34]
        })
        
        ilr_data = pd.DataFrame({
            'ilr_1': [0.1],
            'ilr_2': [0.2],
            'ilr_3': [0.3],
            'poissons_ratio': [0.34]
        })
        
        raw_path = tmp_path / "filtered_alloys.csv"
        ilr_path = tmp_path / "filtered_alloys_ilr.csv"
        output_path = tmp_path / "element_importance.csv"
        
        raw_data.to_csv(raw_path, index=False)
        ilr_data.to_csv(ilr_path, index=False)
        
        mock_model = Mock()
        mock_model.predict.return_value = np.array([0.34])
        
        with patch('analysis.load_trained_model', return_value=mock_model):
            result1 = run_perturbation_sensitivity_analysis(
                mock_model, str(raw_path), str(ilr_path), str(output_path)
            )
            
            result2 = run_perturbation_sensitivity_analysis(
                mock_model, str(raw_path), str(ilr_path), str(output_path)
            )
        
        # Results should be identical due to fixed random state
        for element in result1:
            assert abs(result1[element] - result2[element]) < 1e-10