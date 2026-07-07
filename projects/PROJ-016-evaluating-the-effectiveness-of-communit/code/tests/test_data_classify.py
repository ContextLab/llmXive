"""
Unit tests for regime classification logic.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.classify import load_metadata, classify_regime, convert_to_binary


class TestLoadMetadata:
    """Tests for the load_metadata function."""
    
    def test_load_valid_metadata(self):
        """Test loading a valid metadata file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                'indicator_code': 'AG.LND.FRST.ZS',
                'thresholds': {'lower': 0.2, 'upper': 0.8},
                'source': 'World Bank'
            }, f)
            temp_path = Path(f.name)
        
        try:
            metadata = load_metadata(temp_path)
            assert metadata['indicator_code'] == 'AG.LND.FRST.ZS'
            assert metadata['thresholds']['lower'] == 0.2
            assert metadata['thresholds']['upper'] == 0.8
        finally:
            temp_path.unlink()
    
    def test_missing_metadata_file(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_metadata(Path('/nonexistent/path/metadata.json'))
    
    def test_invalid_json(self):
        """Test that JSONDecodeError is raised for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_metadata(temp_path)
        finally:
            temp_path.unlink()


class TestClassifyRegime:
    """Tests for the classify_regime function."""
    
    def test_classification_above_upper_threshold(self):
        """Test classification when value is above upper threshold."""
        df = pd.DataFrame({'value': [0.9, 0.95, 1.0]})
        metadata = {'thresholds': {'lower': 0.2, 'upper': 0.8}}
        
        result = classify_regime(df, metadata)
        
        assert all(result['regime_type'] == 'CBNRM')
    
    def test_classification_below_lower_threshold(self):
        """Test classification when value is below lower threshold."""
        df = pd.DataFrame({'value': [0.1, 0.05, 0.0]})
        metadata = {'thresholds': {'lower': 0.2, 'upper': 0.8}}
        
        result = classify_regime(df, metadata)
        
        assert all(result['regime_type'] == 'State-Led')
    
    def test_classification_between_thresholds(self):
        """Test classification when value is between thresholds."""
        df = pd.DataFrame({'value': [0.3, 0.5, 0.7]})
        metadata = {'thresholds': {'lower': 0.2, 'upper': 0.8}}
        
        result = classify_regime(df, metadata)
        
        assert all(result['regime_type'] == 'Mixed')
    
    def test_classification_with_missing_values(self):
        """Test classification handles missing values correctly."""
        df = pd.DataFrame({'value': [0.9, None, 0.1]})
        metadata = {'thresholds': {'lower': 0.2, 'upper': 0.8}}
        
        result = classify_regime(df, metadata)
        
        assert result['regime_type'].iloc[0] == 'CBNRM'
        assert pd.isna(result['regime_type'].iloc[1])
        assert result['regime_type'].iloc[2] == 'State-Led'
    
    def test_missing_value_column(self):
        """Test that ValueError is raised when value column is missing."""
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        metadata = {'thresholds': {'lower': 0.2, 'upper': 0.8}}
        
        with pytest.raises(ValueError):
            classify_regime(df, metadata)


class TestConvertToBinary:
    """Tests for the convert_to_binary function."""
    
    def test_binary_conversion_cbnrm(self):
        """Test that CBNRM is converted to 1."""
        df = pd.DataFrame({'regime_type': ['CBNRM', 'CBNRM']})
        
        result = convert_to_binary(df)
        
        assert all(result['regime_type'] == 1)
    
    def test_binary_conversion_state_led(self):
        """Test that State-Led is converted to 0."""
        df = pd.DataFrame({'regime_type': ['State-Led', 'State-Led']})
        
        result = convert_to_binary(df)
        
        assert all(result['regime_type'] == 0)
    
    def test_binary_conversion_mixed(self):
        """Test that Mixed is converted to 0."""
        df = pd.DataFrame({'regime_type': ['Mixed', 'Mixed']})
        
        result = convert_to_binary(df)
        
        assert all(result['regime_type'] == 0)
    
    def test_binary_conversion_with_missing(self):
        """Test that missing values remain missing."""
        df = pd.DataFrame({'regime_type': ['CBNRM', None, 'State-Led']})
        
        result = convert_to_binary(df)
        
        assert result['regime_type'].iloc[0] == 1
        assert pd.isna(result['regime_type'].iloc[1])
        assert result['regime_type'].iloc[2] == 0