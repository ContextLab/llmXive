import pytest
import logging
from unittest.mock import patch, MagicMock
from code.utils.stats import run_wilcoxon_test, SampleSizeException, StatsException

# Configure logging to capture warnings
logging.basicConfig(level=logging.WARNING)

class TestWilcoxonTest:
    def test_wilcoxon_normal_sample(self):
        """Test with a normal sample size (>= 30)."""
        # Create 30 pairs with slight differences
        human = [0.8] * 30
        llm = [0.7] * 30
        
        # This might fail if all values are identical, so let's add some noise
        human = [0.8 + i * 0.01 for i in range(30)]
        llm = [0.7 + i * 0.01 for i in range(30)]
        
        stat, p_val, warned = run_wilcoxon_test(human, llm)
        
        assert isinstance(stat, float)
        assert isinstance(p_val, float)
        assert not warned
        assert 0.0 <= p_val <= 1.0

    def test_wilcoxon_small_sample_warning(self):
        """Test with small sample size (< 30) and verify warning is issued."""
        human = [0.8, 0.9, 0.7]
        llm = [0.7, 0.8, 0.6]
        
        # Capture log output
        with patch('code.utils.stats.logger') as mock_logger:
            stat, p_val, warned = run_wilcoxon_test(human, llm)
            
            # Check that warning was logged
            mock_logger.warning.assert_called_once()
            assert "Statistical power may be low" in mock_logger.warning.call_args[0][0]
            
            # Check return values
            assert warned is True
            assert isinstance(stat, float)
            assert isinstance(p_val, float)

    def test_wilcoxon_empty_inputs(self):
        """Test that empty inputs raise StatsException."""
        with pytest.raises(StatsException):
            run_wilcoxon_test([], [])

    def test_wilcoxon_mismatched_lengths(self):
        """Test that mismatched lengths raise StatsException."""
        with pytest.raises(StatsException):
            run_wilcoxon_test([1.0, 2.0], [1.0])

    def test_wilcoxon_identical_scores(self):
        """Test with identical scores (stat should be 0)."""
        human = [0.5] * 10
        llm = [0.5] * 10
        
        stat, p_val, warned = run_wilcoxon_test(human, llm)
        
        # If all differences are 0, statistic is 0
        assert stat == 0.0
        # p-value might be 1.0 or NaN depending on implementation, but should be valid
        assert isinstance(p_val, float)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])