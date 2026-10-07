import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.clean import (
    process_chunk,
    load_meddra_mapping,
    check_memory_usage,
    get_memory_usage_gb
)

class TestMapSOC:
    def test_meddra_mapping_load(self):
        """Test loading MedDRA mapping from CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mapping_path = Path(tmpdir) / "meddra_soc_mapping.csv"
            mapping_data = {
                'LLT': ['LLT1', 'LLT2', 'LLT3'],
                'SOC_CODE': ['SOC1', 'SOC2', 'SOC3'],
                'SOC_NAME': ['Name1', 'Name2', 'Name3']
            }
            pd.DataFrame(mapping_data).to_csv(mapping_path, index=False)
            
            # Mock the global path
            with patch('src.data.clean.MEDDRA_MAPPING_PATH', mapping_path):
                import src.data.clean as clean_module
                mapping_df = load_meddra_mapping(pytest.fixture(lambda: None) if False else MagicMock())
                
                assert len(mapping_df) == 3
                assert 'SOC_CODE' in mapping_df.columns
                assert 'LLT' in mapping_df.columns

    def test_meddra_mapping_missing_file(self):
        """Test that missing mapping file raises error."""
        with patch('src.data.clean.MEDDRA_MAPPING_PATH', Path("/nonexistent/path.csv")):
            with pytest.raises(SystemExit) as exc_info:
                load_meddra_mapping(MagicMock())
            assert exc_info.value.code == "E_MAPPINGS_INVALID"

    def test_meddra_mapping_missing_columns(self):
        """Test that mapping with missing columns raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mapping_path = Path(tmpdir) / "meddra_soc_mapping.csv"
            mapping_data = {
                'LLT': ['LLT1', 'LLT2'],
                'SOC_NAME': ['Name1', 'Name2']  # Missing SOC_CODE
            }
            pd.DataFrame(mapping_data).to_csv(mapping_path, index=False)
            
            with patch('src.data.clean.MEDDRA_MAPPING_PATH', mapping_path):
                with pytest.raises(SystemExit) as exc_info:
                    load_meddra_mapping(MagicMock())
                assert exc_info.value.code == "E_MAPPINGS_INVALID"

class TestProcessData:
    def test_covid_filtering(self):
        """Test that COVID-19 records are correctly filtered."""
        data = {
            'VAX_TYPE': ['COVID-19 Vaccine', 'Flu Vaccine', 'COVID-19 mRNA', 'Other Vaccine'],
            'REPT_DATE': ['2021-01-01', '2021-01-02', '2021-01-03', '2021-01-04'],
            'LLT': ['LLT1', 'LLT2', 'LLT3', 'LLT4']
        }
        df = pd.DataFrame(data)
        
        mock_logger = MagicMock()
        mapping_df = pd.DataFrame({
            'LLT': ['LLT1', 'LLT2', 'LLT3', 'LLT4'],
            'SOC_CODE': ['SOC1', 'SOC2', 'SOC3', 'SOC4'],
            'SOC_NAME': ['Name1', 'Name2', 'Name3', 'Name4']
        })
        
        result = process_chunk(df, mock_logger, mapping_df)
        
        assert len(result['covid']) == 2  # COVID-19 Vaccine, COVID-19 mRNA
        assert len(result['non_covid']) == 2  # Flu Vaccine, Other Vaccine
        assert len(result['flu']) == 1  # Flu Vaccine
        assert len(result['non_covid_non_flu']) == 1  # Other Vaccine

    def test_empty_vax_type_filtering(self):
        """Test that empty/null VAX_TYPE records are excluded."""
        data = {
            'VAX_TYPE': ['COVID-19 Vaccine', '', None, 'Flu Vaccine'],
            'REPT_DATE': ['2021-01-01', '2021-01-02', '2021-01-03', '2021-01-04'],
            'LLT': ['LLT1', 'LLT2', 'LLT3', 'LLT4']
        }
        df = pd.DataFrame(data)
        
        mock_logger = MagicMock()
        mapping_df = pd.DataFrame({
            'LLT': ['LLT1', 'LLT2', 'LLT3', 'LLT4'],
            'SOC_CODE': ['SOC1', 'SOC2', 'SOC3', 'SOC4'],
            'SOC_NAME': ['Name1', 'Name2', 'Name3', 'Name4']
        })
        
        result = process_chunk(df, mock_logger, mapping_df)
        
        # Empty and null VAX_TYPE should be excluded
        assert len(result['combined']) == 2  # Only COVID-19 Vaccine and Flu Vaccine

    def test_missing_rept_date_filtering(self):
        """Test that records with missing REPT_DATE are excluded."""
        data = {
            'VAX_TYPE': ['COVID-19 Vaccine', 'Flu Vaccine', 'COVID-19 mRNA'],
            'REPT_DATE': ['2021-01-01', None, '2021-01-03'],
            'LLT': ['LLT1', 'LLT2', 'LLT3']
        }
        df = pd.DataFrame(data)
        
        mock_logger = MagicMock()
        mapping_df = pd.DataFrame({
            'LLT': ['LLT1', 'LLT2', 'LLT3'],
            'SOC_CODE': ['SOC1', 'SOC2', 'SOC3'],
            'SOC_NAME': ['Name1', 'Name2', 'Name3']
        })
        
        result = process_chunk(df, mock_logger, mapping_df)
        
        # Record with missing REPT_DATE should be excluded
        assert len(result['combined']) == 2  # Only COVID-19 Vaccine and COVID-19 mRNA

    def test_soc_mapping(self):
        """Test that SOC codes are correctly mapped from LLT."""
        data = {
            'VAX_TYPE': ['COVID-19 Vaccine'],
            'REPT_DATE': ['2021-01-01'],
            'LLT': ['LLT1']
        }
        df = pd.DataFrame(data)
        
        mock_logger = MagicMock()
        mapping_df = pd.DataFrame({
            'LLT': ['LLT1'],
            'SOC_CODE': ['SOC1'],
            'SOC_NAME': ['Name1']
        })
        
        result = process_chunk(df, mock_logger, mapping_df)
        
        assert len(result['combined']) == 1
        assert result['combined']['SOC_CODE'].iloc[0] == 'SOC1'

class TestMemoryUsage:
    def test_get_memory_usage_gb(self):
        """Test that memory usage is returned in GB."""
        mem_gb = get_memory_usage_gb()
        assert isinstance(mem_gb, float)
        assert mem_gb > 0
        assert mem_gb < 100  # Reasonable upper bound

    def test_check_memory_usage_below_limit(self):
        """Test that check_memory_usage doesn't exit when below limit."""
        mock_logger = MagicMock()
        
        # Mock get_memory_usage_gb to return a value below limit
        with patch('src.data.clean.get_memory_usage_gb', return_value=5.0):
            # Should not raise
            check_memory_usage(mock_logger)
            mock_logger.error.assert_not_called()

    def test_check_memory_usage_above_limit(self):
        """Test that check_memory_usage exits when above limit."""
        mock_logger = MagicMock()
        
        # Mock get_memory_usage_gb to return a value above limit
        with patch('src.data.clean.get_memory_usage_gb', return_value=8.0):
            with patch('src.data.clean.MEMORY_LIMIT_GB', 7.0):
                with pytest.raises(SystemExit) as exc_info:
                    check_memory_usage(mock_logger)
                assert exc_info.value.code == "E_MEMORY_LIMIT"
                mock_logger.error.assert_called()
                assert "MEMORY_LIMIT_EXCEEDED" in mock_logger.error.call_args[0][0]