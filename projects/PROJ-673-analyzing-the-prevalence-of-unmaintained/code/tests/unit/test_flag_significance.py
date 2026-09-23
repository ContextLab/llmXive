import pytest
import json
import tempfile
from pathlib import Path
from src.cli.flag_significance import (
    load_results, 
    flag_significance, 
    save_results,
    main
)

class TestFlagSignificance:
    """Unit tests for statistical significance flagging logic."""

    def test_flag_significant_p_less_than_005(self):
        """Test that p < 0.05 is flagged as significant."""
        results = {"p_value": 0.03, "correlation": 0.5}
        flagged = flag_significance(results)
        
        assert flagged['is_significant'] is True
        assert flagged['significance_level'] == "p < 0.05 (Significant)"
        assert flagged['alpha_threshold'] == 0.05

    def test_flag_not_significant_p_greater_than_005(self):
        """Test that p >= 0.05 is flagged as not significant."""
        results = {"p_value": 0.08, "correlation": 0.2}
        flagged = flag_significance(results)
        
        assert flagged['is_significant'] is False
        assert flagged['significance_level'] == "p >= 0.05 (Not Significant)"

    def test_flag_highly_significant_p_less_than_0001(self):
        """Test that p < 0.001 is flagged as highly significant."""
        results = {"p_value": 0.0005, "correlation": 0.8}
        flagged = flag_significance(results)
        
        assert flagged['is_significant'] is True
        assert flagged['significance_level'] == "p < 0.001 (Highly Significant)"

    def test_flag_very_significant_p_less_than_001(self):
        """Test that 0.001 <= p < 0.01 is flagged as very significant."""
        results = {"p_value": 0.005, "correlation": 0.7}
        flagged = flag_significance(results)
        
        assert flagged['is_significant'] is True
        assert flagged['significance_level'] == "p < 0.01 (Very Significant)"

    def test_custom_alpha_threshold(self):
        """Test significance flagging with a custom alpha threshold."""
        results = {"p_value": 0.03, "correlation": 0.5}
        # With alpha=0.01, 0.03 should be not significant
        flagged = flag_significance(results, alpha=0.01)
        
        assert flagged['is_significant'] is False
        assert flagged['alpha_threshold'] == 0.01

    def test_missing_p_value_raises_error(self):
        """Test that missing p_value raises ValueError."""
        results = {"correlation": 0.5}
        with pytest.raises(ValueError, match="must contain 'p_value'"):
            flag_significance(results)

    def test_invalid_p_value_type_raises_error(self):
        """Test that non-numeric p_value raises TypeError."""
        results = {"p_value": "invalid"}
        with pytest.raises(TypeError, match="p_value must be numeric"):
            flag_significance(results)

    def test_save_and_load_results(self):
        """Test saving results to file and loading them back."""
        results = {
            "p_value": 0.02,
            "correlation": 0.6,
            "sample_size": 100
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            save_results(results, temp_path)
            loaded = load_results(temp_path)
            
            assert loaded['p_value'] == results['p_value']
            assert loaded['correlation'] == results['correlation']
            assert loaded['sample_size'] == results['sample_size']
        finally:
            Path(temp_path).unlink()

    def test_flag_significance_preserves_existing_keys(self):
        """Test that flag_significance preserves existing keys in results."""
        original_results = {
            "p_value": 0.04,
            "correlation": 0.55,
            "sample_size": 200,
            "method": "spearman"
        }
        flagged = flag_significance(original_results)
        
        assert flagged['p_value'] == 0.04
        assert flagged['correlation'] == 0.55
        assert flagged['sample_size'] == 200
        assert flagged['method'] == "spearman"
        assert 'is_significant' in flagged
        assert 'significance_level' in flagged