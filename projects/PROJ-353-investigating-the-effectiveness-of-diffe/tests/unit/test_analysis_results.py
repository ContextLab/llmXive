import json
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from generate_analysis_results import main as generate_main
from bonferroni_correction import apply_bonferroni_correction

class TestAnalysisResultsGeneration:
    
    def test_bonferroni_correction_logic(self):
        """Test that Bonferroni correction is applied correctly."""
        # Mock interaction data
        interaction_data = {
            "tobit_p_value": 0.02,
            "cox_p_value": 0.03,
            "tobit_coefficient": 0.5,
            "cox_coefficient": 1.2
        }
        
        corrected = apply_bonferroni_correction(interaction_data)
        
        # n_tests = 2
        assert corrected["tobit_p_corrected"] == pytest.approx(0.04)
        assert corrected["cox_p_corrected"] == pytest.approx(0.06)
        # min(0.04, 0.06) = 0.04 < 0.05 -> True
        assert corrected["is_significant"] is True

    def test_bonferroni_correction_not_significant(self):
        """Test that Bonferroni correction correctly identifies non-significant results."""
        interaction_data = {
            "tobit_p_value": 0.04,
            "cox_p_value": 0.04,
            "tobit_coefficient": 0.5,
            "cox_coefficient": 1.2
        }
        
        corrected = apply_bonferroni_correction(interaction_data)
        
        # n_tests = 2
        assert corrected["tobit_p_corrected"] == pytest.approx(0.08)
        assert corrected["cox_p_corrected"] == pytest.approx(0.08)
        # min(0.08, 0.08) = 0.08 > 0.05 -> False
        assert corrected["is_significant"] is False

    def test_analysis_results_file_structure(self):
        """Test that the generated analysis_results.json has the correct structure."""
        # Create a temporary file for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            interaction_file = tmp_path / "interaction_results.json"
            output_file = tmp_path / "analysis_results.json"
            
            # Write mock interaction data
            interaction_data = {
                "tobit_p_value": 0.02,
                "cox_p_value": 0.03,
                "tobit_coefficient": 0.5,
                "cox_coefficient": 1.2
            }
            with open(interaction_file, 'w') as f:
                json.dump(interaction_data, f)
            
            # Manually run the logic (since main() looks for fixed paths)
            corrected = apply_bonferroni_correction(interaction_data)
            
            # Write output
            with open(output_file, 'w') as f:
                json.dump(corrected, f, indent=2)
            
            # Verify structure
            with open(output_file, 'r') as f:
                results = json.load(f)
            
            required_keys = ["tobit_p_corrected", "cox_p_corrected", "is_significant", 
                             "tobit_coefficient", "cox_coefficient"]
            for key in required_keys:
                assert key in results, f"Missing key: {key}"

    def test_is_significant_boolean_type(self):
        """Test that is_significant is a boolean."""
        interaction_data = {
            "tobit_p_value": 0.02,
            "cox_p_value": 0.03,
            "tobit_coefficient": 0.5,
            "cox_coefficient": 1.2
        }
        
        corrected = apply_bonferroni_correction(interaction_data)
        
        assert isinstance(corrected["is_significant"], bool)