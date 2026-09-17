"""
Unit tests for the significance flagging module (T020).
"""
import pytest
import json
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.significance import check_significance, write_significance_flag


class TestCheckSignificance:
    """Tests for the check_significance function."""

    def test_significant_p_value(self):
        """Test that p < alpha returns True."""
        assert check_significance(0.03, 0.05) is True
        assert check_significance(0.001, 0.05) is True
        assert check_significance(0.049, 0.05) is True

    def test_not_significant_p_value(self):
        """Test that p >= alpha returns False."""
        assert check_significance(0.05, 0.05) is False
        assert check_significance(0.10, 0.05) is False
        assert check_significance(0.99, 0.05) is False

    def test_custom_alpha(self):
        """Test with a custom alpha threshold."""
        assert check_significance(0.01, 0.01) is False
        assert check_significance(0.009, 0.01) is True
        assert check_significance(0.02, 0.01) is False

    def test_invalid_p_value_type(self):
        """Test that non-numeric p_val raises TypeError."""
        with pytest.raises(TypeError):
            check_significance("0.03", 0.05)
        with pytest.raises(TypeError):
            check_significance(None, 0.05)

    def test_boundary_conditions(self):
        """Test edge cases for p-value range."""
        # 0.0 is significant
        assert check_significance(0.0, 0.05) is True
        # 1.0 is not significant
        assert check_significance(1.0, 0.05) is False


class TestWriteSignificanceFlag:
    """Tests for the write_significance_flag function."""

    def test_writes_correct_json(self, tmp_path):
        """Test that the output JSON is correctly formatted."""
        output_file = tmp_path / "test_significance.json"
        p_val = 0.04
        alpha = 0.05
        
        result = write_significance_flag(p_val=p_val, alpha=alpha, output_path=output_file)
        
        # Check returned dict
        assert result["is_significant"] is True
        assert result["p_value"] == p_val
        assert result["alpha"] == alpha
        
        # Check file content
        with open(output_file, 'r') as f:
            file_content = json.load(f)
        
        assert file_content == result
        assert file_content["is_significant"] is True

    def test_writes_non_significant(self, tmp_path):
        """Test output for non-significant result."""
        output_file = tmp_path / "test_non_sig.json"
        p_val = 0.08
        
        result = write_significance_flag(p_val=p_val, output_path=output_file)
        
        assert result["is_significant"] is False
        
        with open(output_file, 'r') as f:
            file_content = json.load(f)
        
        assert file_content["is_significant"] is False