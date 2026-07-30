"""
Unit tests for scale scoring logic.

This module verifies that the scoring functions in `code/analysis/scales.py`
correctly implement the definitions provided in `config/scales.yaml`.

Tests cover:
1. CES-D: Standard scoring with reverse item handling.
2. GAD-7: Standard summation scoring.
3. PCL-5: Standard summation scoring.
4. Edge cases: NaN handling, missing columns, and invalid values.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure the project root is in the path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.analysis.scales import load_scale_config, score_cesd, score_gad7, score_pcl5


@pytest.fixture
def scale_config():
    """Load the scale configuration from the YAML file."""
    config_path = PROJECT_ROOT / "code" / "config" / "scales.yaml"
    if not config_path.exists():
        pytest.fail(f"Scale config file not found at {config_path}. Please run T004 first.")
    return load_scale_config(config_path)

@pytest.fixture
def mock_cesd_data():
    """
    Create a mock DataFrame with CES-D items.
    Items are 0-3 scale.
    Reverse items: depressed5, depressed9, depressed12, depressed16, depressed18
    """
    # Generate 100 rows of random data (0-3)
    items = [f"depressed{i}" for i in range(1, 21)]
    data = np.random.randint(0, 4, size=(100, 20))
    df = pd.DataFrame(data, columns=items)
    
    # Inject some known values for specific tests
    # Row 0: All 0s -> Score 0
    df.loc[0, :] = 0
    # Row 1: All 3s -> Score 60 (before reverse logic, but reverse logic flips 3->0, 0->3? 
    # Wait, standard CES-D reverse: 
    # Pos items: 0=Rarely, 1=Some, 2=Often, 3=Most. Score = sum.
    # Neg items (Reverse): 0=Most, 1=Often, 2=Some, 3=Rarely. 
    # So if raw is 0 (Most), we want to score it as 3. If raw is 3 (Rarely), score as 0.
    # Formula: Score = (Max - Raw) for reverse items? Or specific mapping?
    # The config says "reverse_items" and "scoring: -3 per item" which is ambiguous.
    # Standard CES-D: 4 items are reverse keyed. 
    # If raw=0 (Rarely), score=0. If raw=3 (Most), score=3.
    # Reverse items: If raw=0 (Rarely), score=3. If raw=3 (Most), score=0.
    # Let's assume standard 0-3 scale where reverse = 3 - raw.
    
    # Row 2: All 3s on positive, 0s on reverse -> Max score
    # Positive items (indices 0,1,2,3,5,6,7,8,10,11,13,14,15,17,19) -> 3
    # Reverse items (indices 4,8,11,15,17) -> 0 (which becomes 3 after reverse)
    # Wait, let's just test the function logic directly with known inputs.
    return df

@pytest.fixture
def mock_gad7_data():
    """Create a mock DataFrame with GAD-7 items (0-3 scale)."""
    items = [f"gad{i}" for i in range(1, 8)]
    data = np.random.randint(0, 4, size=(100, 7))
    return pd.DataFrame(data, columns=items)

@pytest.fixture
def mock_pcl5_data():
    """Create a mock DataFrame with PCL-5 items (0-4 scale)."""
    items = [f"pcl{i}" for i in range(1, 26)]
    data = np.random.randint(0, 5, size=(100, 25))
    return pd.DataFrame(data, columns=items)

class TestScaleConfigLoading:
    def test_config_loads_successfully(self, scale_config):
        assert isinstance(scale_config, dict)
        assert "CES-D" in scale_config
        assert "GAD-7" in scale_config
        assert "PCL-5" in scale_config
    
    def test_cesd_items_count(self, scale_config):
        assert len(scale_config["CES-D"]["items"]) == 20
    
    def test_gad7_items_count(self, scale_config):
        assert len(scale_config["GAD-7"]["items"]) == 7
    
    def test_pcl5_items_count(self, scale_config):
        assert len(scale_config["PCL-5"]["items"]) == 25

class TestCESDScoring:
    def test_all_zeros_score_zero(self, scale_config):
        """If all items are 0, score should be 0 (assuming no reverse items are 0? 
        Wait, if reverse item is 0, and reverse logic is 3-0=3, then score is not 0.
        Let's construct a case where all items are scored 0.
        Positive items: 0 -> 0.
        Reverse items: 3 -> 0.
        So we need positive=0, reverse=3.
        """
        # Map item names to indices
        items = scale_config["CES-D"]["items"]
        reverse_items = scale_config["CES-D"]["reverse_items"]
        
        data = {}
        for i, item in enumerate(items):
            if item in reverse_items:
                data[item] = 3  # 3 becomes 0 after reverse (3-3=0)
            else:
                data[item] = 0  # 0 stays 0
        
        df = pd.DataFrame([data])
        scores = score_cesd(df, scale_config)
        assert scores.iloc[0] == 0
    
    def test_all_max_score(self, scale_config):
        """Positive=3, Reverse=0 (becomes 3). Total = 20 * 3 = 60."""
        items = scale_config["CES-D"]["items"]
        reverse_items = scale_config["CES-D"]["reverse_items"]
        
        data = {}
        for i, item in enumerate(items):
            if item in reverse_items:
                data[item] = 0  # 0 becomes 3 after reverse
            else:
                data[item] = 3  # 3 stays 3
        
        df = pd.DataFrame([data])
        scores = score_cesd(df, scale_config)
        assert scores.iloc[0] == 60
    
    def test_nan_handling(self, scale_config):
        """If a row has NaN, the result should be NaN (or handled per config, but usually NaN)."""
        items = scale_config["CES-D"]["items"]
        data = {item: 1 for item in items}
        data[items[0]] = np.nan
        df = pd.DataFrame([data])
        
        scores = score_cesd(df, scale_config)
        # Standard sum with NaN usually results in NaN unless skipna=True
        # The implementation likely uses sum(skipna=False) or similar to flag missingness.
        # We expect NaN here.
        assert pd.isna(scores.iloc[0])

class TestGAD7Scoring:
    def test_simple_sum(self, scale_config, mock_gad7_data):
        """GAD-7 is a simple sum of 7 items (0-3)."""
        # Set all to 1 -> sum = 7
        mock_gad7_data[:] = 1
        scores = score_gad7(mock_gad7_data, scale_config)
        assert scores.iloc[0] == 7
    
    def test_max_score(self, scale_config, mock_gad7_data):
        """Max score = 7 items * 3 = 21."""
        mock_gad7_data[:] = 3
        scores = score_gad7(mock_gad7_data, scale_config)
        assert scores.iloc[0] == 21
    
    def test_min_score(self, scale_config, mock_gad7_data):
        """Min score = 0."""
        mock_gad7_data[:] = 0
        scores = score_gad7(mock_gad7_data, scale_config)
        assert scores.iloc[0] == 0

class TestPCL5Scoring:
    def test_simple_sum(self, scale_config, mock_pcl5_data):
        """PCL-5 is a simple sum of 25 items (0-4)."""
        # Set all to 1 -> sum = 25
        mock_pcl5_data[:] = 1
        scores = score_pcl5(mock_pcl5_data, scale_config)
        assert scores.iloc[0] == 25
    
    def test_max_score(self, scale_config, mock_pcl5_data):
        """Max score = 25 items * 4 = 100."""
        mock_pcl5_data[:] = 4
        scores = score_pcl5(mock_pcl5_data, scale_config)
        assert scores.iloc[0] == 100
    
    def test_min_score(self, scale_config, mock_pcl5_data):
        """Min score = 0."""
        mock_pcl5_data[:] = 0
        scores = score_pcl5(mock_pcl5_data, scale_config)
        assert scores.iloc[0] == 0

class TestMissingColumns:
    def test_cesd_missing_column(self, scale_config):
        """Should raise KeyError or return NaN if a required item is missing."""
        items = scale_config["CES-D"]["items"]
        # Remove one item
        data = {item: 1 for item in items[1:]}
        df = pd.DataFrame([data])
        
        with pytest.raises(KeyError):
            score_cesd(df, scale_config)
    
    def test_gad7_missing_column(self, scale_config):
        """Should raise KeyError if a required item is missing."""
        items = scale_config["GAD-7"]["items"]
        data = {item: 1 for item in items[1:]}
        df = pd.DataFrame([data])
        
        with pytest.raises(KeyError):
            score_gad7(df, scale_config)

class TestInvalidValues:
    def test_cesd_invalid_value(self, scale_config):
        """If a value is outside 0-3, behavior is undefined but shouldn't crash. 
        We assume the function just sums. If validation is needed, it should be tested separately.
        For now, we test that it sums correctly even with out-of-bounds (if allowed)."""
        items = scale_config["CES-D"]["items"]
        data = {item: 1 for item in items}
        data[items[0]] = 5 # Invalid
        df = pd.DataFrame([data])
        
        # The function should just sum.
        scores = score_cesd(df, scale_config)
        # 19 * 1 + 5 = 24 (assuming no reverse logic on this specific item for simplicity of test)
        # Actually, let's pick a non-reverse item.
        reverse = scale_config["CES-D"]["reverse_items"]
        non_rev = [i for i in items if i not in reverse][0]
        data[non_rev] = 5
        df = pd.DataFrame([data])
        scores = score_cesd(df, scale_config)
        # 19 * 1 + 5 = 24
        assert scores.iloc[0] == 24