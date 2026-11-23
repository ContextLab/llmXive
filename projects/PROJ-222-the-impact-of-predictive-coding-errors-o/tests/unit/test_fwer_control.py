import pytest
import sys
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from analysis import verify_fwer_control, run_multiple_comparison_correction

class TestFWERControl:
    def test_single_test_no_correction(self):
        """Test that single test returns controlled status without correction."""
        p_values = [0.03]
        corrected = run_multiple_comparison_correction(p_values)
        status = verify_fwer_control(p_values, corrected)
        
        assert status["fwer_control_status"] == "controlled"
        assert status["num_tests"] == 1
        assert "Single test" in status["reason"]

    def test_multiple_tests_bonferroni_control(self):
        """Test that multiple tests with Bonferroni are reported as controlled."""
        p_values = [0.01, 0.04, 0.05, 0.20]
        corrected = run_multiple_comparison_correction(p_values, method="bonferroni")
        status = verify_fwer_control(p_values, corrected)
        
        assert status["fwer_control_status"] == "controlled"
        assert status["num_tests"] == 4
        assert "FWER controlled" in status["reason"]
        assert "bonferroni" in status["reason"].lower() or "correction" in status["reason"].lower()

    def test_fwer_alpha_threshold(self):
        """Verify alpha threshold is recorded correctly."""
        p_values = [0.01, 0.02]
        corrected = run_multiple_comparison_correction(p_values)
        status = verify_fwer_control(p_values, corrected, alpha=0.05)
        
        assert status["alpha_threshold"] == 0.05
        assert status["fwer_control_status"] == "controlled"

    def test_empty_p_values(self):
        """Handle empty list of p-values."""
        p_values = []
        corrected = []
        status = verify_fwer_control(p_values, corrected)
        
        assert status["fwer_control_status"] == "controlled"
        assert status["num_tests"] == 0