import pytest
from code.analysis import apply_holm_bonferroni

class TestHolmBonferroni:
    def test_single_p_value(self):
        """Test with a single p-value."""
        p_values = [{'p_value': 0.03, 'task_type': 'math'}]
        result = apply_holm_bonferroni(p_values)
        assert len(result) == 1
        # Adjusted p = 0.03 * 1 = 0.03
        assert result[0]['adjusted_p_value'] == pytest.approx(0.03, rel=1e-5)
        assert result[0]['significant'] is True

    def test_multiple_p_values_unordered(self):
        """Test with multiple p-values, ensuring sorting and monotonicity."""
        p_values = [
            {'p_value': 0.01, 'task_type': 'math'},
            {'p_value': 0.05, 'task_type': 'science'},
            {'p_value': 0.02, 'task_type': 'history'}
        ]
        # Sorted: 0.01, 0.02, 0.05
        # n=3
        # i=1 (0.01): adj = 0.01 * 3 = 0.03
        # i=2 (0.02): adj = 0.02 * 2 = 0.04
        # i=3 (0.05): adj = 0.05 * 1 = 0.05
        
        result = apply_holm_bonferroni(p_values)
        
        # Check results in original order
        # math (0.01) -> 0.03
        # science (0.05) -> 0.05
        # history (0.02) -> 0.04
        
        assert result[0]['adjusted_p_value'] == pytest.approx(0.03, rel=1e-5)
        assert result[0]['significant'] is True
        
        assert result[1]['adjusted_p_value'] == pytest.approx(0.05, rel=1e-5)
        assert result[1]['significant'] is False # 0.05 is not < 0.05
        
        assert result[2]['adjusted_p_value'] == pytest.approx(0.04, rel=1e-5)
        assert result[2]['significant'] is True

    def test_monotonicity_enforcement(self):
        """Test that adjusted p-values are monotonically increasing."""
        # Construct a case where raw calculation would violate monotonicity
        # p1 = 0.04, p2 = 0.01 (n=2)
        # i=1 (0.01): adj = 0.01 * 2 = 0.02
        # i=2 (0.04): adj = 0.04 * 1 = 0.04 (ok)
        # Let's try: p1=0.01, p2=0.001 (n=2)
        # i=1 (0.001): adj = 0.002
        # i=2 (0.01): adj = 0.01
        # This is fine.
        
        # Try: p1=0.04, p2=0.03 (n=2)
        # i=1 (0.03): adj = 0.06
        # i=2 (0.04): adj = 0.04 -> Should be forced to 0.06
        
        p_values = [
            {'p_value': 0.04, 'task_type': 'A'},
            {'p_value': 0.03, 'task_type': 'B'}
        ]
        result = apply_holm_bonferroni(p_values)
        
        # B (0.03) -> 0.03 * 2 = 0.06
        # A (0.04) -> 0.04 * 1 = 0.04 -> capped at 0.06
        assert result[0]['adjusted_p_value'] == pytest.approx(0.06, rel=1e-5)
        assert result[1]['adjusted_p_value'] == pytest.approx(0.06, rel=1e-5)
    
    def test_empty_list(self):
        """Test with empty list."""
        result = apply_holm_bonferroni([])
        assert result == []
    
    def test_alpha_parameter(self):
        """Test with different alpha."""
        p_values = [{'p_value': 0.01}]
        result = apply_holm_bonferroni(p_values, alpha=0.01)
        # adj = 0.01, alpha = 0.01 -> significant is False (strictly less)
        assert result[0]['significant'] is False