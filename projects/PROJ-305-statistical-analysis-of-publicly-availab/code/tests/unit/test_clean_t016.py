import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import shutil

# Add code to path if necessary
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.data.clean import load_meddra_mapping, process_chunk, map_soc_to_code

class TestT016Clean:
    @pytest.fixture
    def temp_mapping_file(self):
        """Create a temporary MedDRA mapping file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("LLT,SOC_CODE,SOC\n")
            f.write("LLT_001,CODE_001,SOC_A\n")
            f.write("LLT_002,CODE_002,SOC_B\n")
            f.write("LLT_003,CODE_003,SOC_C\n")
        return f.name

    @pytest.fixture
    def temp_cleaned_dir(self):
        """Create a temporary directory for processed data."""
        temp_dir = tempfile.mkdtemp()
        processed_dir = Path(temp_dir) / "processed"
        processed_dir.mkdir()
        return processed_dir

    def test_load_meddra_mapping_valid(self, temp_mapping_file, caplog):
        """Test loading a valid MedDRA mapping file."""
        # Temporarily set the global path
        import src.data.clean as clean_module
        original_path = clean_module.MEDDRA_MAPPING_PATH
        clean_module.MEDDRA_MAPPING_PATH = Path(temp_mapping_file)
        
        try:
            df = load_meddra_mapping(caplog)
            assert len(df) == 3
            assert "SOC" in df.columns
        finally:
            clean_module.MEDDRA_MAPPING_PATH = original_path

    def test_load_meddra_mapping_missing_file(self, caplog):
        """Test loading a missing MedDRA mapping file raises SystemExit."""
        import src.data.clean as clean_module
        original_path = clean_module.MEDDRA_MAPPING_PATH
        clean_module.MEDDRA_MAPPING_PATH = Path("non_existent_file.csv")
        
        with pytest.raises(SystemExit) as exc_info:
            load_meddra_mapping(caplog)
        assert exc_info.value.code == 20 # E_MAPPINGS_INVALID
        
        clean_module.MEDDRA_MAPPING_PATH = original_path

    def test_process_chunk_mapping(self, temp_mapping_file):
        """Test that process_chunk correctly maps LLT to SOC."""
        import src.data.clean as clean_module
        original_path = clean_module.MEDDRA_MAPPING_PATH
        clean_module.MEDDRA_MAPPING_PATH = Path(temp_mapping_file)
        
        # Create sample chunk
        data = {
            "VAX_TYPE": ["COVID-19", "Influenza", "Hepatitis B"],
            "REPT_DATE": ["2021-01-01", "2021-02-01", "2021-03-01"],
            "LLT": ["LLT_001", "LLT_002", "LLT_003"],
            "SOC_CODE": ["CODE_001", "CODE_002", "CODE_003"]
        }
        chunk = pd.DataFrame(data)
        
        # Mock logger
        import logging
        logger = logging.getLogger("test")
        
        df = load_meddra_mapping(logger)
        processed = process_chunk(chunk, df, logger)
        
        assert "SOC" in processed.columns
        assert processed.iloc[0]["SOC"] == "SOC_A"
        assert processed.iloc[1]["SOC"] == "SOC_B"
        assert processed.iloc[2]["SOC"] == "SOC_C"
        
        clean_module.MEDDRA_MAPPING_PATH = original_path

    def test_process_chunk_filtering(self):
        """Test that process_chunk filters out missing REPT_DATE and Unknown SOC."""
        # Create a temporary mapping file for this test
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("LLT,SOC_CODE,SOC\n")
            f.write("LLT_001,CODE_001,SOC_A\n")
            f.write("LLT_002,CODE_002,SOC_B\n")
        temp_file = f.name

        import src.data.clean as clean_module
        original_path = clean_module.MEDDRA_MAPPING_PATH
        clean_module.MEDDRA_MAPPING_PATH = Path(temp_file)
        
        data = {
            "VAX_TYPE": ["COVID-19", "Influenza", "Hepatitis B", "Unknown_Vax"],
            "REPT_DATE": ["2021-01-01", None, "2021-03-01", "2021-04-01"], # One missing date
            "LLT": ["LLT_001", "LLT_002", "UNKNOWN_LLT", "LLT_001"], # One unknown LLT
            "SOC_CODE": ["CODE_001", "CODE_002", "UNKNOWN_CODE", "CODE_001"]
        }
        chunk = pd.DataFrame(data)
        
        import logging
        logger = logging.getLogger("test")
        df = load_meddra_mapping(logger)
        processed = process_chunk(chunk, df, logger)
        
        # Should filter out row with None REPT_DATE (index 1)
        # Should filter out row with Unknown SOC (index 2)
        # Should keep index 0 and 3
        assert len(processed) == 2
        
        os.unlink(temp_file)
        clean_module.MEDDRA_MAPPING_PATH = original_path

    def test_vax_type_grouping(self):
        """Test VAX_TYPE_GROUP assignment."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("LLT,SOC_CODE,SOC\n")
            f.write("LLT_001,CODE_001,SOC_A\n")
        temp_file = f.name

        import src.data.clean as clean_module
        original_path = clean_module.MEDDRA_MAPPING_PATH
        clean_module.MEDDRA_MAPPING_PATH = Path(temp_file)
        
        data = {
            "VAX_TYPE": ["COVID-19", "Influenza A", "Hepatitis B", "Influenza B"],
            "REPT_DATE": ["2021-01-01"] * 4,
            "LLT": ["LLT_001"] * 4,
            "SOC_CODE": ["CODE_001"] * 4
        }
        chunk = pd.DataFrame(data)
        
        import logging
        logger = logging.getLogger("test")
        df = load_meddra_mapping(logger)
        processed = process_chunk(chunk, df, logger)
        
        groups = processed["VAX_TYPE_GROUP"].tolist()
        assert groups[0] == "COVID-19"
        assert groups[1] == "Flu-only"
        assert groups[2] == "Non-COVID-Non-Flu"
        assert groups[3] == "Flu-only"
        
        os.unlink(temp_file)
        clean_module.MEDDRA_MAPPING_PATH = original_path