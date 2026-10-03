import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the module under test
# We need to adjust the import path to match the project structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.clean import (
    map_soc_codes,
    load_meddra_mapping,
    check_memory_usage,
    process_chunk,
    get_memory_usage_gb
)

class TestMapSOC:
    def test_map_soc_codes_basic(self):
        """Test basic SOC mapping."""
        # Create sample data
        df = pd.DataFrame({
            "SOC_CODE": ["10000001", "10000002", "10000003"],
            "VAX_TYPE": ["Pfizer", "Moderna", "J&J"],
            "REPT_DATE": ["2020-01-01", "2020-01-02", "2020-01-03"]
        })
        
        # Create mapping
        mapping = pd.DataFrame({
            "SOC_CODE": ["10000001", "10000002", "10000003"],
            "SOC": ["Cardiac disorders", "Nervous system disorders", "Respiratory disorders"]
        })
        
        # Mock logger
        import logging
        logger = logging.getLogger("test")
        
        result = map_soc_codes(df, mapping, logger)
        
        assert len(result) == 3
        assert "SOC" in result.columns
        assert result["SOC"].tolist() == ["Cardiac disorders", "Nervous system disorders", "Respiratory disorders"]
    
    def test_map_soc_codes_with_missing(self):
        """Test mapping with missing SOC_CODE."""
        df = pd.DataFrame({
            "SOC_CODE": ["10000001", None, "10000003"],
            "VAX_TYPE": ["Pfizer", "Moderna", "J&J"],
            "REPT_DATE": ["2020-01-01", "2020-01-02", "2020-01-03"]
        })
        
        mapping = pd.DataFrame({
            "SOC_CODE": ["10000001", "10000003"],
            "SOC": ["Cardiac disorders", "Respiratory disorders"]
        })
        
        import logging
        logger = logging.getLogger("test")
        
        result = map_soc_codes(df, mapping, logger)
        
        # Should drop the row with missing SOC_CODE
        assert len(result) == 2
        assert "SOC" not in result[result["SOC_CODE"].isna()].index.tolist()

class TestProcessData:
    def test_process_chunk_grouping(self):
        """Test that process_chunk correctly labels groups."""
        df = pd.DataFrame({
            "SOC_CODE": ["10000001", "10000002", "10000003", "10000004"],
            "VAX_TYPE": ["Pfizer COVID-19", "Moderna COVID-19", "Fluvax Influenza", "J&J"],
            "REPT_DATE": ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"]
        })
        
        mapping = pd.DataFrame({
            "SOC_CODE": ["10000001", "10000002", "10000003", "10000004"],
            "SOC": ["A", "B", "C", "D"]
        })
        
        import logging
        logger = logging.getLogger("test")
        
        result = process_chunk(df, mapping, logger)
        
        # Check group labels
        assert result["VAX_GROUP"].tolist() == ["COVID-19", "COVID-19", "Non-COVID", "Non-COVID"]
        assert result["GROUP_LABEL"].tolist() == ["COVID-19", "COVID-19", "Flu-only", "Non-COVID-Non-Flu"]
    
    def test_process_chunk_drops_missing_rept_date(self):
        """Test that rows with missing REPT_DATE are dropped."""
        df = pd.DataFrame({
            "SOC_CODE": ["10000001", "10000002"],
            "VAX_TYPE": ["Pfizer", "Moderna"],
            "REPT_DATE": ["2020-01-01", None]
        })
        
        mapping = pd.DataFrame({
            "SOC_CODE": ["10000001", "10000002"],
            "SOC": ["A", "B"]
        })
        
        import logging
        logger = logging.getLogger("test")
        
        result = process_chunk(df, mapping, logger)
        
        assert len(result) == 1
        assert result.iloc[0]["REPT_DATE"] == "2020-01-01"

class TestMemoryUsage:
    def test_get_memory_usage_gb(self):
        """Test memory usage calculation."""
        # Just verify the function returns a float
        import tracemalloc
        tracemalloc.start()
        usage = get_memory_usage_gb()
        assert isinstance(usage, float)
        assert usage >= 0.0
        tracemalloc.stop()
    
    def test_check_memory_usage_no_error_under_limit(self):
        """Test that check_memory_usage does not raise under limit."""
        import logging
        logger = logging.getLogger("test")
        # This should not raise
        try:
            check_memory_usage(logger)
        except MemoryError:
            pytest.fail("check_memory_usage raised MemoryError under limit")
    
    def test_load_meddra_mapping_missing_file(self):
        """Test that load_meddra_mapping fails loudly if file is missing."""
        import logging
        logger = logging.getLogger("test")
        
        # Create a temporary directory with no mapping file
        with tempfile.TemporaryDirectory() as tmpdir:
            # Temporarily override the path
            import src.data.clean as clean_module
            original_path = clean_module.MEDDRA_MAPPING_PATH
            clean_module.MEDDRA_MAPPING_PATH = Path(tmpdir) / "nonexistent.csv"
            
            try:
                with pytest.raises(SystemExit) as excinfo:
                    load_meddra_mapping(logger)
                assert excinfo.value.code == 102  # E_MAPPING_MISSING
            finally:
                clean_module.MEDDRA_MAPPING_PATH = original_path