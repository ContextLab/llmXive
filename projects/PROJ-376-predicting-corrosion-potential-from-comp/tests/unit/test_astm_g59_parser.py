"""
Unit tests for the ASTM G59 tolerance parser module.

These tests verify that the tolerance configuration is loaded correctly,
that default values are properly applied when the standard does not define
a specific value, and that error handling works as expected.
"""

import pytest
import yaml
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils.astm_g59_parser import (
    load_astm_tolerance_config,
    get_tolerance_value,
    get_tolerance_source_info,
    validate_tolerance_for_comparison
)
from utils.exceptions import CorrosionPipelineError


class TestASTMG59Parser:
    """Test suite for ASTM G59 tolerance parser functions."""

    @pytest.fixture
    def valid_config_file(self, tmp_path):
        """Create a temporary valid configuration file."""
        config_content = {
            'tolerance': {
                'value': 25.0,
                'unit': 'mV',
                'source': 'Literature-derived default',
                'standard_reference': 'ASTM G59-97(2014)',
                'notes': 'Default value from literature',
                'verified': True
            }
        }
        config_file = tmp_path / 'astm_g59_tolerance.yaml'
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_content, f)
        return config_file

    @pytest.fixture
    def missing_value_config_file(self, tmp_path):
        """Create a temporary configuration file with missing value field."""
        config_content = {
            'tolerance': {
                'unit': 'mV',
                'source': 'Unknown'
            }
        }
        config_file = tmp_path / 'astm_g59_tolerance.yaml'
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_content, f)
        return config_file

    @pytest.fixture
    def missing_section_config_file(self, tmp_path):
        """Create a temporary configuration file with missing tolerance section."""
        config_content = {
            'other_section': {
                'value': 10.0
            }
        }
        config_file = tmp_path / 'astm_g59_tolerance.yaml'
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config_content, f)
        return config_file

    def test_load_valid_config(self, valid_config_file):
        """Test loading a valid configuration file."""
        config = load_astm_tolerance_config(valid_config_file)

        assert 'tolerance' in config
        assert config['tolerance']['value'] == 25.0
        assert config['tolerance']['unit'] == 'mV'
        assert config['tolerance']['source'] == 'Literature-derived default'
        assert config['tolerance']['verified'] is True

    def test_load_missing_value_raises_error(self, missing_value_config_file):
        """Test that missing value field raises CorrosionPipelineError."""
        with pytest.raises(CorrosionPipelineError) as exc_info:
            load_astm_tolerance_config(missing_value_config_file)

        assert "Missing required field 'value'" in str(exc_info.value)

    def test_load_missing_section_raises_error(self, missing_section_config_file):
        """Test that missing tolerance section raises CorrosionPipelineError."""
        with pytest.raises(CorrosionPipelineError) as exc_info:
            load_astm_tolerance_config(missing_section_config_file)

        assert "Missing 'tolerance' section" in str(exc_info.value)

    def test_load_nonexistent_file_raises_error(self, tmp_path):
        """Test that loading a nonexistent file raises CorrosionPipelineError."""
        nonexistent_file = tmp_path / 'nonexistent.yaml'

        with pytest.raises(CorrosionPipelineError) as exc_info:
            load_astm_tolerance_config(nonexistent_file)

        assert "not found" in str(exc_info.value)

    def test_get_tolerance_value(self, valid_config_file):
        """Test extracting tolerance value and unit."""
        value, unit = get_tolerance_value(valid_config_file)

        assert value == 25.0
        assert unit == 'mV'

    def test_get_tolerance_source_info(self, valid_config_file):
        """Test retrieving source information."""
        info = get_tolerance_source_info(valid_config_file)

        assert info['source'] == 'Literature-derived default'
        assert info['standard_reference'] == 'ASTM G59-97(2014)'
        assert 'notes' in info
        assert info['verified'] == 'True'

    def test_validate_tolerance_positive_value(self, valid_config_file):
        """Test validation of a positive tolerance value."""
        value, unit = get_tolerance_value(valid_config_file)
        result = validate_tolerance_for_comparison(value, unit)

        assert result is True

    def test_validate_tolerance_negative_value_raises_error(self, valid_config_file):
        """Test that negative tolerance value raises CorrosionPipelineError."""
        with pytest.raises(CorrosionPipelineError) as exc_info:
            validate_tolerance_for_comparison(-10.0, 'mV')

        assert "Invalid tolerance value" in str(exc_info.value)
        assert "positive number" in str(exc_info.value)

    def test_validate_tolerance_zero_value_raises_error(self, valid_config_file):
        """Test that zero tolerance value raises CorrosionPipelineError."""
        with pytest.raises(CorrosionPipelineError) as exc_info:
            validate_tolerance_for_comparison(0.0, 'mV')

        assert "Invalid tolerance value" in str(exc_info.value)

    def test_tolerance_always_defined(self, valid_config_file):
        """
        Verify that a tolerance value is always defined as per SC-002.

        This test ensures that even if the standard does not define a specific
        value, a literature-derived default is available and usable.
        """
        value, unit = get_tolerance_value(valid_config_file)

        # The value must be defined and positive
        assert value is not None
        assert isinstance(value, (int, float))
        assert value > 0

        # The unit must be defined
        assert unit is not None
        assert len(unit) > 0

        # Source must indicate it's a default or derived value
        info = get_tolerance_source_info(valid_config_file)
        assert 'default' in info['source'].lower() or 'derived' in info['source'].lower()
