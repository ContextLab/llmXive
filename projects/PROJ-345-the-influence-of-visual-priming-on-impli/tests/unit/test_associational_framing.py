"""
Unit tests for FR-003 associational framing requirements.

These tests verify that model outputs and reports explicitly frame
findings as associational and avoid causal language.
"""
import pytest
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.models.lmm import (
    run_lmm_analysis, 
    _format_associational_summary, 
    fit_lmm_with_retry
)
from code.reports.generate_report import generate_report_pdf

class TestAssociationalFraming:
    """Tests for FR-003 associational framing requirements."""

    @pytest.fixture
    def mock_data(self):
        """Create mock data for LMM testing."""
        data = {
            'response_time': np.random.normal(500, 50, 100),
            'prime_valence': np.random.choice([-1, 0, 1], 100),
            'stimulus_ambiguity': np.random.uniform(0, 1, 100),
            'stimulus_id': [f'stim_{i}' for i in range(100)],
            'participant_id': [f'p_{i % 10}' for i in range(100)]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_format_summary_uses_associational_language(self, mock_data, temp_dir):
        """Test that _format_associational_summary uses associational language."""
        # Mock a successful model result
        mock_result = MagicMock()
        mock_result.params = {
            'Intercept': 500.0,
            'prime_valence': 10.5,
            'stimulus_ambiguity': -5.2,
            'prime_valence:stimulus_ambiguity': 2.1
        }
        mock_result.conf_int = MagicMock(return_value=pd.DataFrame({
            0: [490, 5, -10, 1],
            1: [510, 15, 0, 3]
        }, index=['Intercept', 'prime_valence', 'stimulus_ambiguity', 'prime_valence:stimulus_ambiguity']))
        
        formatted = _format_associational_summary(mock_result)
        
        # Check for associational language
        assert "interpretation_note" in formatted
        assert "associational" in formatted["interpretation_note"].lower()
        assert "causal" not in formatted["interpretation_note"].lower() or "not" in formatted["interpretation_note"].lower()
        
        # Check each effect has associational framing
        for param, data in formatted["fixed_effects"].items():
            assert "association" in data["interpretation"].lower()
            assert "causal_warning" in data
            assert "FR-003" in data["causal_warning"]

    def test_run_lmm_analysis_includes_associational_framing(self, mock_data, temp_dir):
        """Test that run_lmm_analysis includes associational framing in output."""
        input_file = temp_dir / "input.csv"
        output_file = temp_dir / "results.json"
        
        mock_data.to_csv(input_file, index=False)
        
        # Mock the fit_lmm_with_retry to return a successful result
        with patch('code.models.lmm.fit_lmm_with_retry') as mock_fit:
            mock_result = MagicMock()
            mock_result.converged = True
            mock_result.params = {'Intercept': 500.0, 'prime_valence': 10.5}
            mock_result.conf_int = MagicMock(return_value=pd.DataFrame({
                0: [490], 1: [510]
            }, index=['Intercept']))
            mock_fit.return_value = (mock_result, {"converged": True, "attempts": 1})
            
            results = run_lmm_analysis(str(input_file), str(output_file))
            
            # Check associational framing flags
            assert results.get("associational_framing") is True
            assert results.get("causal_claims") is False
            assert "interpretation" in results
            assert "associational" in results["interpretation"].lower()
            assert "causal" not in results["interpretation"].lower() or "no" in results["interpretation"].lower()

    def test_report_generation_includes_disclaimer(self, temp_dir):
        """Test that generated report includes FR-003 disclaimer."""
        results_file = temp_dir / "results.json"
        report_file = temp_dir / "report.txt"
        
        # Create mock results
        mock_results = {
            "status": "success",
            "formula": "response_time ~ prime_valence * stimulus_ambiguity",
            "metadata": {"converged": True, "final_optimizer": "lbfgs"},
            "results": {
                "fixed_effects": {
                    "prime_valence": {
                        "coefficient": 10.5,
                        "direction": "positive",
                        "interpretation": "A positive association was observed.",
                        "causal_warning": "This finding is associational; no causal claims are made per FR-003."
                    }
                }
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(mock_results, f)
        
        generate_report_pdf(str(results_file), str(report_file))
        
        # Read and verify report content
        with open(report_file, 'r') as f:
            report_content = f.read()
        
        # Check for FR-003 disclaimer
        assert "ASSOCIATIONAL" in report_content
        assert "NO CAUSAL CLAIMS" in report_content
        assert "observational" in report_content.lower()
        assert "derived prime valence" in report_content.lower()
        assert "causes" not in report_content or "DO NOT say" in report_content

    def test_report_guidelines_prevent_causal_language(self, temp_dir):
        """Test that report includes guidelines preventing causal language."""
        results_file = temp_dir / "results.json"
        report_file = temp_dir / "report.txt"
        
        mock_results = {
            "status": "success",
            "formula": "response_time ~ prime_valence",
            "metadata": {"converged": True, "final_optimizer": "lbfgs"},
            "results": {
                "fixed_effects": {
                    "prime_valence": {
                        "coefficient": 10.5,
                        "direction": "positive",
                        "interpretation": "A positive association was observed.",
                        "causal_warning": "This finding is associational; no causal claims are made per FR-003."
                    }
                }
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(mock_results, f)
        
        generate_report_pdf(str(results_file), str(report_file))
        
        with open(report_file, 'r') as f:
            report_content = f.read()
        
        # Check for interpretation guidelines
        assert "DO say" in report_content
        assert "DO NOT say" in report_content
        assert "causes" in report_content  # In the context of what NOT to say