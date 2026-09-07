import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.services.proxy_extractor import calculate_filter_applied_contribution, ConfigurationError
from code.config import CONFIG

class TestFilterAppliedContribution:
    def test_filter_applied_weight_from_contract(self, tmp_path):
        """Test that the weight is correctly read from the contract file."""
        # Create a temporary contract file
        contract_dir = tmp_path / "contracts"
        contract_dir.mkdir()
        contract_file = contract_dir / "analysis.schema.yaml"
        
        contract_content = """
        analysis:
          control_proxy:
            weights:
              filter_applied_weight: 2.5
        """
        contract_file.write_text(contract_content)
        
        # Mock CONFIG.PROJECT_ROOT
        original_root = CONFIG.PROJECT_ROOT
        CONFIG.PROJECT_ROOT = str(tmp_path)
        
        try:
            df = pd.DataFrame({
                'filter_applied': [1, 1, 0, 1]
            })
            
            result = calculate_filter_applied_contribution(df)
            
            # Expected: 2.5 * [1, 1, 0, 1] = [2.5, 2.5, 0.0, 2.5]
            expected = pd.Series([2.5, 2.5, 0.0, 2.5])
            
            pd.testing.assert_series_equal(result, expected)
        finally:
            CONFIG.PROJECT_ROOT = original_root

    def test_missing_weight_raises_error(self, tmp_path):
        """Test that a missing weight in contract raises ConfigurationError."""
        contract_dir = tmp_path / "contracts"
        contract_dir.mkdir()
        contract_file = contract_dir / "analysis.schema.yaml"
        
        # Contract without the required weight
        contract_content = """
        analysis:
          control_proxy:
            weights:
              other_weight: 1.0
        """
        contract_file.write_text(contract_content)
        
        original_root = CONFIG.PROJECT_ROOT
        CONFIG.PROJECT_ROOT = str(tmp_path)
        
        try:
            df = pd.DataFrame({'filter_applied': [1]})
            
            with pytest.raises(ConfigurationError):
                calculate_filter_applied_contribution(df)
        finally:
            CONFIG.PROJECT_ROOT = original_root

    def test_nan_handling(self, tmp_path):
        """Test that NaN values in filter_applied are handled correctly."""
        contract_dir = tmp_path / "contracts"
        contract_dir.mkdir()
        contract_file = contract_dir / "analysis.schema.yaml"
        
        contract_content = """
        analysis:
          control_proxy:
            weights:
              filter_applied_weight: 1.0
        """
        contract_file.write_text(contract_content)
        
        original_root = CONFIG.PROJECT_ROOT
        CONFIG.PROJECT_ROOT = str(tmp_path)
        
        try:
            df = pd.DataFrame({
                'filter_applied': [1.0, np.nan, 0.0]
            })
            
            result = calculate_filter_applied_contribution(df)
            
            # NaN should be treated as 0 -> 0.0
            expected = pd.Series([1.0, 0.0, 0.0])
            
            pd.testing.assert_series_equal(result, expected)
        finally:
            CONFIG.PROJECT_ROOT = original_root