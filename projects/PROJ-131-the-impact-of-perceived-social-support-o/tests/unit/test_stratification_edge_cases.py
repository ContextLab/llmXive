"""
Unit tests for stratification edge cases (T046).

Verifies that the sensitivity analysis correctly handles:
1. Platforms with N < 30 (E-SMALL-N-001)
2. Platforms with low variance
3. Scenarios where fewer than 2 valid platforms remain
"""
import pytest
import pandas as pd
import numpy as np
import logging
from io import StringIO
from pathlib import Path
import sys

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.sensitivity import stratify_by_platform, MIN_STRATUM_SIZE

# Configure logging to capture output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestStratificationEdgeCases:
    
    def test_small_n_excluded(self, caplog):
        """
        Test that platforms with N < 30 are excluded and logged as E-SMALL-N-001.
        """
        # Create a mock dataset
        data = {
            'platform': ['A'] * 10 + ['B'] * 50 + ['C'] * 20,
            'harassment_severity': np.random.rand(80),
            'social_support': np.random.rand(80),
            'depression': np.random.rand(80),
            'age': np.random.randint(18, 60, 80),
            'gender': ['M', 'F'] * 40,
            'education': np.random.randint(1, 5, 80),
            'income': np.random.randint(20, 100, 80)
        }
        df = pd.DataFrame(data)
        
        with caplog.at_level(logging.ERROR):
            result = stratify_by_platform(df)
        
        # Verify platform A (N=10) and C (N=20) are excluded
        assert 'A' not in result, "Platform A (N=10) should be excluded"
        assert 'C' not in result, "Platform C (N=20) should be excluded"
        assert 'B' in result, "Platform B (N=50) should be included"
        
        # Verify log message
        assert any("E-SMALL-N-001" in record.message for record in caplog.records), \
            "Expected E-SMALL-N-001 log message for small N platforms"
        
        print(f"Test passed: Small N platforms correctly excluded. Result keys: {list(result.keys())}")

    def test_low_variance_excluded(self, caplog):
        """
        Test that platforms with low variance in harassment severity are excluded.
        """
        # Create a dataset with one platform having zero variance
        data = {
            'platform': ['A'] * 50 + ['B'] * 50,
            'harassment_severity': [0.5] * 50 + np.random.rand(50), # A has no variance
            'social_support': np.random.rand(100),
            'depression': np.random.rand(100),
            'age': np.random.randint(18, 60, 100),
            'gender': ['M', 'F'] * 50,
            'education': np.random.randint(1, 5, 100),
            'income': np.random.randint(20, 100, 100)
        }
        df = pd.DataFrame(data)
        
        with caplog.at_level(logging.ERROR):
            result = stratify_by_platform(df)
        
        # Platform A should be excluded due to low variance (SD=0)
        assert 'A' not in result, "Platform A (SD=0) should be excluded"
        assert 'B' in result, "Platform B should be included"
        
        assert any("E-LOW-VAR-001" in record.message for record in caplog.records), \
            "Expected E-LOW-VAR-001 log message for low variance platform"

    def test_skip_if_less_than_two_platforms(self, caplog):
        """
        Test that if fewer than 2 valid platforms remain, stratification is skipped.
        """
        # Create a dataset with only one valid platform
        data = {
            'platform': ['A'] * 10 + ['B'] * 50, # A is too small, only B remains
            'harassment_severity': np.random.rand(60),
            'social_support': np.random.rand(60),
            'depression': np.random.rand(60),
            'age': np.random.randint(18, 60, 60),
            'gender': ['M', 'F'] * 30,
            'education': np.random.randint(1, 5, 60),
            'income': np.random.randint(20, 100, 60)
        }
        df = pd.DataFrame(data)
        
        with caplog.at_level(logging.ERROR):
            result = stratify_by_platform(df)
        
        # Should return empty dict
        assert result == {}, "Should return empty dict if < 2 valid platforms"
        
        assert any("E-SKIP-001" in record.message for record in caplog.records), \
            "Expected E-SKIP-001 log message when < 2 platforms remain"

    def test_all_platforms_valid(self):
        """
        Test normal operation when all platforms meet criteria.
        """
        data = {
            'platform': ['A'] * 50 + ['B'] * 50 + ['C'] * 50,
            'harassment_severity': np.random.rand(150),
            'social_support': np.random.rand(150),
            'depression': np.random.rand(150),
            'age': np.random.randint(18, 60, 150),
            'gender': ['M', 'F'] * 75,
            'education': np.random.randint(1, 5, 150),
            'income': np.random.randint(20, 100, 150)
        }
        df = pd.DataFrame(data)
        
        result = stratify_by_platform(df)
        
        assert len(result) == 3, "All 3 platforms should be included"
        assert set(result.keys()) == {'A', 'B', 'C'}
        
        # Verify counts
        assert len(result['A']) == 50
        assert len(result['B']) == 50
        assert len(result['C']) == 50

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
