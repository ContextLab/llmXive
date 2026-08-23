import json
import os
import tempfile
from pathlib import Path
import pytest

# We need to mock the config and paths if they aren't set up in the test environment
# But for unit testing the logic, we can test the functions directly with mock data
# The main() function relies on config, so we might skip testing main() or mock it.

# Import the functions to test
# Note: We are importing from the module we just created.
# Since we are in a test file, we assume the module is importable.
# If the project structure is not fully set up in the test runner, we might need to adjust sys.path.
# However, the task requires the code to be real and runnable.

# Let's assume the test runner sets up the path correctly.
# If not, we can add a sys.path manipulation here for robustness in the test file.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.robustness import compare_model_significance, run_sensitivity_analysis

class TestCompareModelSignificance:
    def test_both_significant(self):
        """Test when both models show significant results."""
        model_a = {
            "fixed_effects": {
                "salience_score": {"pvalue": 0.01, "coef": 0.5}
            }
        }
        model_b = {
            "fixed_effects": {
                "salience_score": {"pvalue": 0.02, "coef": 0.48}
            }
        }
        
        result = compare_model_significance(model_a, model_b, "salience_score")
        
        assert result["status"] != "incomplete"
        assert result["model_a_significant"] is True
        assert result["model_b_significant"] is True
        assert result["robust"] is True
        assert result["change_status"] == "both_significant"

    def test_lost_significance(self):
        """Test when Model A is significant but Model B is not."""
        model_a = {
            "fixed_effects": {
                "salience_score": {"pvalue": 0.01, "coef": 0.5}
            }
        }
        model_b = {
            "fixed_effects": {
                "salience_score": {"pvalue": 0.08, "coef": 0.45}
            }
        }
        
        result = compare_model_significance(model_a, model_b, "salience_score")
        
        assert result["model_a_significant"] is True
        assert result["model_b_significant"] is False
        assert result["robust"] is False
        assert result["change_status"] == "lost_significance_in_B"

    def test_missing_pvalue(self):
        """Test handling of missing p-values."""
        model_a = {
            "fixed_effects": {
                "other_var": {"pvalue": 0.01}
            }
        }
        model_b = {
            "fixed_effects": {
                "salience_score": {"pvalue": 0.02}
            }
        }
        
        result = compare_model_significance(model_a, model_b, "salience_score")
        
        assert result["status"] == "incomplete"
        assert "Missing p-values" in result["reason"]

class TestRunSensitivityAnalysis:
    def test_end_to_end(self):
        """Test the full pipeline of loading, comparing, and writing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create mock input
            input_data = {
                "model_a": {
                    "fixed_effects": {
                        "salience_score": {"pvalue": 0.03, "coef": 0.5}
                    }
                },
                "model_b": {
                    "fixed_effects": {
                        "salience_score": {"pvalue": 0.04, "coef": 0.49}
                    }
                }
            }
            
            input_path = tmpdir / "results.json"
            output_path = tmpdir / "sensitivity_output.json"
            
            with open(input_path, 'w') as f:
                json.dump(input_data, f)
            
            # Run the function
            result = run_sensitivity_analysis(input_path, output_path)
            
            # Verify output file exists
            assert output_path.exists()
            
            # Verify content
            with open(output_path, 'r') as f:
                saved_result = json.load(f)
            
            assert saved_result["robust"] is True
            assert saved_result["change_status"] == "both_significant"
            assert "timestamp" in saved_result