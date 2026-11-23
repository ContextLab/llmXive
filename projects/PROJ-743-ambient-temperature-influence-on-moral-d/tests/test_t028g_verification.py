"""
Unit tests for Task T028g: Verify Dilemma Choice Derivation.

These tests ensure that the verification logic in `code/verify_dilemma_choice.py`
correctly identifies dependencies and integration.
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from verify_dilemma_choice import verify_code_independence, verify_model_integration

class TestCodeIndependence:
    def test_pass_no_response_time_reference(self, tmp_path):
        """Test that a script without response_time reference passes."""
        script_content = """
        import pandas as pd
        def derive_choice(df):
            # Logic based on lives saved
            df['dilemma_choice'] = 'save_many'
            return df
        """
        script_path = tmp_path / "mock_derive.py"
        script_path.write_text(script_content)
        
        result = verify_code_independence(script_path)
        assert result["status"] == "PASS"
        assert result["references_response_time"] is False

    def test_fail_with_response_time_reference(self, tmp_path):
        """Test that a script with response_time reference fails."""
        script_content = """
        import pandas as pd
        def derive_choice(df):
            # Incorrectly using response time to determine choice
            df['dilemma_choice'] = df['response_time'] > 5000
            return df
        """
        script_path = tmp_path / "mock_derive.py"
        script_path.write_text(script_content)
        
        result = verify_code_independence(script_path)
        assert result["status"] == "FAIL"
        assert result["references_response_time"] is True
        assert len(result["line_numbers"]) > 0

    def test_fail_script_not_found(self):
        """Test handling of missing script."""
        result = verify_code_independence(Path("/nonexistent/path.py"))
        assert result["status"] == "FAIL"
        assert "not found" in result["reason"]

class TestModelIntegration:
    def test_pass_model_includes_choice(self, tmp_path):
        """Test that a model script including dilemma_choice passes."""
        model_content = """
        import statsmodels.api as sm
        formula = "log_response_time ~ temperature + dilemma_choice + (1|participant)"
        """
        script_path = tmp_path / "mock_model.py"
        script_path.write_text(model_content)
        
        result = verify_model_integration(script_path, ["dilemma_choice"])
        assert result["status"] == "PASS"
        assert result["dilemma_choice_in_model"] is True

    def test_fail_model_excludes_choice(self, tmp_path):
        """Test that a model script missing dilemma_choice fails."""
        model_content = """
        import statsmodels.api as sm
        formula = "log_response_time ~ temperature + (1|participant)"
        """
        script_path = tmp_path / "mock_model.py"
        script_path.write_text(model_content)
        
        result = verify_model_integration(script_path, ["dilemma_choice"])
        assert result["status"] == "FAIL"
        assert result["dilemma_choice_in_model"] is False

    def test_fail_model_script_not_found(self):
        """Test handling of missing model script."""
        result = verify_model_integration(Path("/nonexistent/model.py"))
        assert result["status"] == "FAIL"
        assert "not found" in result["reason"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])