import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
import tempfile

# Add project root to path
root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from modeling.collinearity import calculate_vif, flag_high_collinearity, run_collinearity_diagnostics

class TestVIFCalculation:
    def test_calculate_vif_basic(self):
        """Test basic VIF calculation with known low collinearity data."""
        # Create data with low correlation
        np.random.seed(42)
        data = pd.DataFrame({
            'f1': np.random.randn(100),
            'f2': np.random.randn(100),
            'f3': np.random.randn(100)
        })
        
        vif = calculate_vif(data)
        
        assert len(vif) == 3
        # VIF should be close to 1 for uncorrelated features
        assert all(vif > 1.0)
        assert all(vif < 10.0) # Low collinearity

    def test_calculate_vif_high_collinearity(self):
        """Test VIF calculation with highly correlated features."""
        np.random.seed(42)
        base = np.random.randn(100)
        data = pd.DataFrame({
            'f1': base,
            'f2': base * 2 + 0.1 * np.random.randn(100), # Highly correlated
            'f3': np.random.randn(100)
        })
        
        vif = calculate_vif(data)
        
        # f1 and f2 should have high VIF
        assert vif['f1'] > 5.0
        assert vif['f2'] > 5.0
        # f3 should be low
        assert vif['f3'] < 5.0

    def test_calculate_vif_empty_dataframe(self):
        """Test that empty dataframe raises error."""
        data = pd.DataFrame()
        with pytest.raises(ValueError):
            calculate_vif(data)

class TestFlagCollinearity:
    def test_flag_high_collinearity(self):
        """Test flagging logic."""
        vif_series = pd.Series({
            'f1': 2.0,
            'f2': 6.5,
            'f3': 12.0
        })
        
        flagged = flag_high_collinearity(vif_series, threshold=5.0)
        
        assert len(flagged) == 3
        assert flagged[0]['feature_name'] == 'f1'
        assert flagged[0]['is_high_collinearity'] == False
        assert flagged[1]['is_high_collinearity'] == True
        assert flagged[2]['is_high_collinearity'] == True

class TestRunDiagnostics:
    def test_run_diagnostics_integration(self):
        """Test full diagnostic run with temporary files."""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, "test_data.csv")
            output_path = os.path.join(tmpdir, "test_results.json")
            
            # Create test data
            np.random.seed(42)
            df = pd.DataFrame({
                'metabolite_A': np.random.randn(50),
                'metabolite_B': np.random.randn(50),
                'metabolite_C': np.random.randn(50)
            })
            df.to_csv(input_path, index=False)
            
            # Run diagnostics
            results = run_collinearity_diagnostics(input_path, output_path, threshold=5.0)
            
            # Verify output file exists
            assert os.path.exists(output_path)
            
            # Verify JSON structure
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert 'collinearity_vif' in loaded
            assert 'collinearity_summary' in loaded
            assert 'high_collinearity_count' in loaded['collinearity_summary']
            assert 'threshold' in loaded['collinearity_summary']
            
            # Verify VIF values are reasonable
            vif_vals = [item['vif_value'] for item in loaded['collinearity_vif']]
            assert all(isinstance(v, (int, float)) for v in vif_vals)
            assert all(v > 1.0 for v in vif_vals)

    def test_run_diagnostics_missing_file(self):
        """Test that missing input file raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.json")
            
            with pytest.raises(FileNotFoundError):
                run_collinearity_diagnostics("nonexistent.csv", output_path)