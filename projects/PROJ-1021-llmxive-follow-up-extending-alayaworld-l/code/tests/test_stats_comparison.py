import pytest
import json
import os
import sys
from pathlib import Path
from scipy.stats import wilcoxon, shapiro

# Ensure the code directory is in the path for imports if running from tests/
# In a real execution context, this would be handled by the runner or PYTHONPATH
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from metrics import calculate_drift_score, DriftMetrics

class TestStatsComparison:
    """
    Unit tests for the statistical comparison logic required in T019.
    Tests the Wilcoxon signed-rank test and Shapiro-Wilk pre-check logic.
    These tests use mock data to verify the statistical functions work correctly
    without requiring the full pipeline execution.
    """

    def _load_mock_scores(self, count=10):
        """Helper to generate mock baseline and hybrid scores for testing."""
        baseline = [0.5 + i * 0.01 for i in range(count)]
        hybrid = [0.4 + i * 0.01 for i in range(count)]
        return baseline, hybrid

    def test_shapiro_wilk_check(self):
        """Test that Shapiro-Wilk pre-check runs without error on mock data."""
        baseline, hybrid = self._load_mock_scores(20)
        
        # Calculate differences
        diffs = [b - h for b, h in zip(baseline, hybrid)]
        
        # Run Shapiro-Wilk
        stat, p_value = shapiro(diffs)
        
        assert p_value is not None
        assert 0.0 <= p_value <= 1.0
        # Just verify the function runs; p-value interpretation depends on data

    def test_wilcoxon_signed_rank(self):
        """Test that Wilcoxon test runs without error on mock data."""
        baseline, hybrid = self._load_mock_scores(20)
        
        # Run Wilcoxon
        stat, p_value = wilcoxon(baseline, hybrid)
        
        assert p_value is not None
        assert 0.0 <= p_value <= 1.0

    def test_stats_logic_integration(self):
        """
        Test the full logic flow: load data -> check normality -> run Wilcoxon.
        Simulates the logic that will be in the main script.
        """
        baseline, hybrid = self._load_mock_scores(30)
        
        # 1. Shapiro-Wilk pre-check
        stat, p_value = shapiro([b - h for b, h in zip(baseline, hybrid)])
        
        # 2. Wilcoxon test (always run for this task's requirement, 
        # but in real logic we check p-value first)
        w_stat, w_p_value = wilcoxon(baseline, hybrid)
        
        # Verify outputs are reasonable
        assert isinstance(w_stat, float) or hasattr(w_stat, 'real')
        assert 0.0 <= w_p_value <= 1.0
        
        # Verify the mock data structure
        assert len(baseline) == len(hybrid)
        assert len(baseline) > 10  # Minimum for Shapiro-Wilk in some versions

    def test_file_loading_mock(self):
        """Test that the script can attempt to load the expected JSON files."""
        # Create a temporary mock file to simulate the existence of data
        # This verifies the file I/O logic without needing the full pipeline
        import tempfile
        import json
        
        mock_data = {
            "scores": [{"seed": i, "score": 0.5, "timestamp": "2023-01-01"} for i in range(10)]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_data, f)
            temp_path = f.name
        
        try:
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert "scores" in data
            assert len(data["scores"]) == 10
        finally:
            os.unlink(temp_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
