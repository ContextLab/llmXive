"""
Unit tests for configuration loading and normalization constants.
Verifies T032: Magic numbers are removed from heuristics and moved to config.
"""
import pytest
from pathlib import Path
import sys
import os
import yaml

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.config import load_config, validate_config
from classification.heuristics import normalize_state

class TestConfigLoading:
    """Test that config loads correctly from schema."""
    
    def test_load_config_exists(self):
        """Verify config file exists and loads."""
        config_path = Path(__file__).parent.parent.parent / "code" / "utils" / "config_schema.yaml"
        assert config_path.exists(), "config_schema.yaml must exist"
        
        wrapper = load_config(str(config_path))
        assert wrapper is not None
        assert wrapper.config is not None
        
    def test_normalization_config_loaded(self):
        """Verify normalization constants are loaded from config."""
        wrapper = load_config()
        norm_cfg = wrapper.config.normalization
        
        # Check that tolerance is a float and not hardcoded in code
        assert isinstance(norm_cfg.float_tolerance, float)
        assert norm_cfg.float_tolerance == 1.0e-6
        
        # Check placeholders
        assert norm_cfg.timestamp_placeholder == "[TIMESTAMP]"
        assert norm_cfg.id_placeholder == "[ID]"
        assert norm_cfg.ref_placeholder == "[REF]"
        
    def test_validate_config(self):
        """Verify config validation works."""
        wrapper = load_config()
        assert validate_config(wrapper) is True

class TestNormalizationNoMagicNumbers:
    """Test that normalization uses config values, not magic numbers."""
    
    def test_float_normalization_uses_config(self):
        """Verify float rounding uses config tolerance."""
        wrapper = load_config()
        tolerance = wrapper.config.normalization.float_tolerance
        
        # Test value that needs rounding
        test_val = 3.14159265358979
        
        # Normalize
        result = normalize_state(test_val)
        
        # Calculate expected decimal places
        decimal_places = max(0, int(-math.log10(tolerance)))
        expected = round(test_val, decimal_places)
        
        assert result == expected
        
    def test_timestamp_replacement_uses_config(self):
        """Verify timestamp placeholder comes from config."""
        wrapper = load_config()
        expected_placeholder = wrapper.config.normalization.timestamp_placeholder
        
        test_str = "Event at 2023-10-05T14:30:00Z occurred"
        result = normalize_state(test_str)
        
        assert expected_placeholder in result
        assert "2023-10-05" not in result
        
    def test_uuid_replacement_uses_config(self):
        """Verify ID placeholder comes from config."""
        wrapper = load_config()
        expected_placeholder = wrapper.config.normalization.id_placeholder
        
        test_str = "User ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890 logged in"
        result = normalize_state(test_str)
        
        assert expected_placeholder in result
        assert "a1b2c3d4" not in result

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
