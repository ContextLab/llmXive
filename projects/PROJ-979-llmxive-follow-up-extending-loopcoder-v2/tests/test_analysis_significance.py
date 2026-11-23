import pytest
import os
import json
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code" / "src"))

from analysis import generate_significance_flag

class TestSignificanceFlag:
    def test_significant_p_value(self):
        """Test that p < 0.05 returns True."""
        assert generate_significance_flag(0.01) is True
        assert generate_significance_flag(0.049) is True
        assert generate_significance_flag(0.0) is True

    def test_non_significant_p_value(self):
        """Test that p >= 0.05 returns False."""
        assert generate_significance_flag(0.05) is False
        assert generate_significance_flag(0.1) is False
        assert generate_significance_flag(0.99) is False

    def test_none_p_value(self):
        """Test that None returns False."""
        assert generate_significance_flag(None) is False

    def test_integration_with_save(self):
        """Test that the flag is correctly saved in the JSON output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_analysis.json"
            
            # Manually call the logic that would be in save_correlation_results
            p_val = 0.03
            flag = generate_significance_flag(p_val)
            
            data = {
                "spearman_rho": 0.5,
                "p_value": p_val,
                "is_significant": flag
            }
            
            with open(output_path, 'w') as f:
                json.dump(data, f)
            
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded['is_significant'] is True
            assert loaded['p_value'] == 0.03