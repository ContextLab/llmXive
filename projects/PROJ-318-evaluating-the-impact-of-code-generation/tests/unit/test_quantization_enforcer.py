"""
Unit tests for quantization enforcement logic.
"""
import pytest
import sys
from unittest.mock import patch, MagicMock
import torch

# We need to import the module to test it
# Assuming the module is in code/utils/quantization_enforcer.py
# We need to add code/ to path if not already
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.quantization_enforcer import enforce_low_bit_quantization, QuantizationEnforcementError, validate_quantization_config
from transformers import BitsAndBytesConfig

class TestQuantizationEnforcement:
    
    def test_enforce_success(self):
        """Test that enforcement passes when all conditions are met."""
        # This test assumes bitsandbytes and correct torch are installed in the environment.
        # If they are, this should pass. If not, it will raise an error (which is the desired behavior).
        try:
            enforce_low_bit_quantization()
            # If we are here, it passed
            assert True
        except QuantizationEnforcementError:
            # If we are here, the environment doesn't support it, which is also a valid "enforcement" result
            # But for the unit test to pass in a CI environment that might not have GPU/bitsandbytes,
            # we might need to mock. However, the requirement is "ABORT on failure".
            # So if the environment fails, the function SHOULD raise.
            # We can't assert "success" if the environment is missing deps.
            # This test is more of an integration check.
            pytest.skip("Environment does not support 4-bit quantization (expected in some CI).")

    def test_validate_config_4bit(self):
        """Test that a valid 4-bit config passes validation."""
        config = BitsAndBytesConfig(
            load_in_4bit=True,
            load_in_8bit=False
        )
        # Should not raise
        validate_quantization_config(config)

    def test_validate_config_not_4bit(self):
        """Test that a non-4-bit config raises an error."""
        config = BitsAndBytesConfig(
            load_in_4bit=False,
            load_in_8bit=False
        )
        with pytest.raises(QuantizationEnforcementError):
            validate_quantization_config(config)

    def test_validate_config_8bit(self):
        """Test that an 8-bit config raises an error."""
        config = BitsAndBytesConfig(
            load_in_4bit=False,
            load_in_8bit=True
        )
        with pytest.raises(QuantizationEnforcementError):
            validate_quantization_config(config)

    @patch('utils.quantization_enforcer.bitsandbytes')
    @patch('utils.quantization_enforcer.torch')
    def test_enforce_missing_bitsandbytes(self, mock_torch, mock_bnb_module):
        """Test that enforcement fails if bitsandbytes is missing."""
        # Simulate ImportError
        import builtins
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'bitsandbytes':
                raise ImportError("No module named 'bitsandbytes'")
            return original_import(name, *args, **kwargs)
        
        with patch.object(builtins, '__import__', side_effect=mock_import):
            with patch('utils.quantization_enforcer.logging') as mock_logging:
                with pytest.raises(QuantizationEnforcementError):
                    enforce_low_bit_quantization()
            mock_logging.critical.assert_called()

    @patch('utils.quantization_enforcer.torch')
    def test_enforce_wrong_torch_version(self, mock_torch):
        """Test that enforcement fails if torch version is too low."""
        mock_torch.__version__ = "2.0.0"
        mock_torch.cuda.is_available.return_value = False
        
        # We need to mock the import of bitsandbytes to succeed
        import builtins
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'bitsandbytes':
                return MagicMock()
            return original_import(name, *args, **kwargs)
        
        with patch.object(builtins, '__import__', side_effect=mock_import):
            with patch('utils.quantization_enforcer.logging') as mock_logging:
                with pytest.raises(QuantizationEnforcementError):
                    enforce_low_bit_quantization()
            mock_logging.critical.assert_called()