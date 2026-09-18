"""
Unit tests for src/ingest/fetch_thermal.py (T014b)

Tests verify:
- Constitution alignment check integration
- Metadata generation check integration
- Data fetching from verified sources
- Data validation logic
- Failure modes (loud failures, no synthetic fallback)
"""
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import sys
import json
import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ingest.fetch_thermal import (
    check_constitution_alignment,
    check_metadata_generation,
    validate_thermal_data,
    load_thermal_data,
    fetch_perovskite_thermal_data,
    fetch_from_nist,
    fetch_from_verified_literature
)

class TestConstitutionAlignmentCheck:
    """Tests for check_constitution_alignment function"""
    
    @patch('src.ingest.fetch_thermal.check_research_md')
    def test_alignment_verified(self, mock_check):
        """Test when alignment is verified"""
        mock_check.return_value = True
        result = check_constitution_alignment()
        assert result is True
    
    @patch('src.ingest.fetch_thermal.check_research_md')
    def test_alignment_not_found(self, mock_check):
        """Test when alignment is not found"""
        mock_check.return_value = False
        result = check_constitution_alignment()
        assert result is False
    
    @patch('src.ingest.fetch_thermal.check_research_md')
    def test_check_raises_exception(self, mock_check):
        """Test when check function raises an exception"""
        mock_check.side_effect = Exception("Check failed")
        result = check_constitution_alignment()
        assert result is False

class TestMetadataGenerationCheck:
    """Tests for check_metadata_generation function"""
    
    @patch('src.ingest.fetch_thermal.METADATA_PATH')
    def test_metadata_exists_and_valid(self, mock_path):
        """Test when metadata file exists and is valid"""
        mock_path.exists.return_value = True
        
        mock_file = mock_open(read_data="thermal_data: {version: '1.0'}")
        
        with patch('builtins.open', mock_file):
            with patch('yaml.safe_load', return_value={'thermal_data': {'version': '1.0'}}):
                result = check_metadata_generation()
                assert result is True
    
    @patch('src.ingest.fetch_thermal.METADATA_PATH')
    def test_metadata_missing(self, mock_path):
        """Test when metadata file is missing"""
        mock_path.exists.return_value = False
        result = check_metadata_generation()
        assert result is False
    
    @patch('src.ingest.fetch_thermal.METADATA_PATH')
    def test_metadata_missing_thermal_data_section(self, mock_path):
        """Test when metadata file exists but lacks thermal_data section"""
        mock_path.exists.return_value = True
        
        mock_file = mock_open(read_data="other_data: {}")
        
        with patch('builtins.open', mock_file):
            with patch('yaml.safe_load', return_value={'other_data': {}}):
                result = check_metadata_generation()
                assert result is False

class TestThermalDataValidation:
    """Tests for validate_thermal_data function"""
    
    def test_valid_data(self):
        """Test validation with valid data"""
        df = pd.DataFrame({
            'structure_id': ['A', 'B', 'C'],
            'thermal_conductivity': [1.5, 2.0, 3.5],
            'source_reference': ['DOI:10.1234', 'DOI:10.5678', 'DOI:10.9012'],
            'chemistry_class': ['oxide', 'halide', 'nitride'],
            'temperature': [300, 350, 400]
        })
        result = validate_thermal_data(df)
        assert result is True
    
    def test_missing_columns(self):
        """Test validation with missing columns"""
        df = pd.DataFrame({
            'structure_id': ['A', 'B'],
            'thermal_conductivity': [1.5, 2.0]
        })
        result = validate_thermal_data(df)
        assert result is False
    
    def test_null_values_in_critical_columns(self):
        """Test validation with null values (should warn but return True)"""
        df = pd.DataFrame({
            'structure_id': ['A', None, 'C'],
            'thermal_conductivity': [1.5, 2.0, 3.5],
            'source_reference': ['DOI:10.1234', 'DOI:10.5678', None],
            'chemistry_class': ['oxide', 'halide', 'nitride'],
            'temperature': [300, 350, 400]
        })
        result = validate_thermal_data(df)
        # Should return True but log warnings
        assert result is True
    
    def test_invalid_thermal_conductivity(self):
        """Test validation with non-positive thermal conductivity (should warn but return True)"""
        df = pd.DataFrame({
            'structure_id': ['A', 'B', 'C'],
            'thermal_conductivity': [-1.0, 2.0, 0.0],
            'source_reference': ['DOI:10.1234', 'DOI:10.5678', 'DOI:10.9012'],
            'chemistry_class': ['oxide', 'halide', 'nitride'],
            'temperature': [300, 350, 400]
        })
        result = validate_thermal_data(df)
        assert result is True

class TestDataFetching:
    """Tests for data fetching functions"""
    
    @patch('src.ingest.fetch_thermal.requests.get')
    def test_nist_fetch_success(self, mock_get):
        """Test successful NIST data fetch"""
        mock_response = MagicMock()
        mock_response.text = "structure_id,thermal_conductivity,source_reference,chemistry_class,temperature\nA,1.5,DOI:10.1234,oxide,300"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        df = fetch_from_nist()
        assert df is not None
        assert len(df) == 1
        assert df['structure_id'].iloc[0] == 'A'
    
    @patch('src.ingest.fetch_thermal.requests.get')
    def test_nist_fetch_failure(self, mock_get):
        """Test failed NIST data fetch"""
        mock_get.side_effect = Exception("Network error")
        df = fetch_from_nist()
        assert df is None
    
    @patch('src.ingest.fetch_thermal.requests.get')
    def test_verified_literature_fetch_success(self, mock_get):
        """Test successful verified literature data fetch"""
        mock_response = MagicMock()
        mock_response.text = "structure_id,thermal_conductivity,source_reference,chemistry_class,temperature\nB,2.0,DOI:10.5678,halide,350"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        df = fetch_from_verified_literature()
        assert df is not None
        assert len(df) == 1
        assert df['structure_id'].iloc[0] == 'B'
    
    @patch('src.ingest.fetch_thermal.requests.get')
    def test_verified_literature_fetch_failure(self, mock_get):
        """Test failed verified literature data fetch"""
        mock_get.side_effect = Exception("Network error")
        df = fetch_from_verified_literature()
        assert df is None

class TestLoadThermalData:
    """Tests for load_thermal_data function"""
    
    @patch('src.ingest.fetch_thermal.check_constitution_alignment')
    @patch('src.ingest.fetch_thermal.check_metadata_generation')
    @patch('src.ingest.fetch_thermal.fetch_from_nist')
    def test_load_data_success_from_nist(self, mock_nist, mock_meta, mock_const):
        """Test successful load from NIST"""
        mock_const.return_value = True
        mock_meta.return_value = True
        mock_nist.return_value = pd.DataFrame({
            'structure_id': ['A'],
            'thermal_conductivity': [1.5],
            'source_reference': ['DOI:10.1234'],
            'chemistry_class': ['oxide'],
            'temperature': [300]
        })
        
        df = load_thermal_data()
        assert df is not None
        assert len(df) == 1
    
    @patch('src.ingest.fetch_thermal.check_constitution_alignment')
    @patch('src.ingest.fetch_thermal.check_metadata_generation')
    @patch('src.ingest.fetch_thermal.fetch_from_nist')
    @patch('src.ingest.fetch_thermal.fetch_from_verified_literature')
    def test_load_data_fallback_to_literature(self, mock_lit, mock_nist, mock_meta, mock_const):
        """Test fallback to verified literature when NIST fails"""
        mock_const.return_value = True
        mock_meta.return_value = True
        mock_nist.return_value = None
        mock_lit.return_value = pd.DataFrame({
            'structure_id': ['B'],
            'thermal_conductivity': [2.0],
            'source_reference': ['DOI:10.5678'],
            'chemistry_class': ['halide'],
            'temperature': [350]
        })
        
        df = load_thermal_data()
        assert df is not None
        assert len(df) == 1
        assert df['structure_id'].iloc[0] == 'B'
    
    @patch('src.ingest.fetch_thermal.check_constitution_alignment')
    @patch('src.ingest.fetch_thermal.check_metadata_generation')
    @patch('src.ingest.fetch_thermal.fetch_from_nist')
    @patch('src.ingest.fetch_thermal.fetch_from_verified_literature')
    def test_load_data_all_sources_fail(self, mock_lit, mock_nist, mock_meta, mock_const):
        """Test failure when all sources are unavailable"""
        mock_const.return_value = True
        mock_meta.return_value = True
        mock_nist.return_value = None
        mock_lit.return_value = None
        
        with pytest.raises(RuntimeError, match="All thermal data sources failed"):
            load_thermal_data()
    
    @patch('src.ingest.fetch_thermal.check_constitution_alignment')
    def test_load_data_constitution_fails(self, mock_const):
        """Test failure when constitution check fails"""
        mock_const.return_value = False
        
        with pytest.raises(RuntimeError, match="Constitution VII alignment check failed"):
            load_thermal_data()

class TestFetchPerovskiteThermalData:
    """Tests for fetch_perovskite_thermal_data function"""
    
    @patch('src.ingest.fetch_thermal.load_thermal_data')
    @patch('src.ingest.fetch_thermal.get_thermal_data_version')
    def test_fetch_with_seed(self, mock_version, mock_load):
        """Test fetching data with seed parameter"""
        mock_load.return_value = pd.DataFrame({
            'structure_id': ['A'],
            'thermal_conductivity': [1.5],
            'source_reference': ['DOI:10.1234'],
            'chemistry_class': ['oxide'],
            'temperature': [300]
        })
        mock_version.return_value = '1.0'
        
        df = fetch_perovskite_thermal_data(seed=42)
        assert df is not None
        assert 'data_version' in df.columns
        assert 'fetch_timestamp' in df.columns
    
    @patch('src.ingest.fetch_thermal.load_thermal_data')
    def test_fetch_without_seed(self, mock_load):
        """Test fetching data without seed parameter"""
        mock_load.return_value = pd.DataFrame({
            'structure_id': ['B'],
            'thermal_conductivity': [2.0],
            'source_reference': ['DOI:10.5678'],
            'chemistry_class': ['halide'],
            'temperature': [350]
        })
        
        df = fetch_perovskite_thermal_data()
        assert df is not None
        assert len(df) == 1