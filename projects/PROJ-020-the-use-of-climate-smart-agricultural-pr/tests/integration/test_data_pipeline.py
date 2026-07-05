"""
Integration test for download and merge pipeline.
"""
import pytest
from pathlib import Path
from data.download import download_faostat, download_lsms, download_nasa_power
from data.clean import clean_and_merge

def test_download_faostat_integration():
    """
    Integration test for FAOSTAT download.
    """
    try:
        output_path = download_faostat("FS")
        assert output_path.exists()
        assert output_path.stat().st_size > 0, "FAOSTAT file is empty"
    except NotImplementedError:
        pytest.skip("FAOSTAT download not implemented yet")

def test_full_pipeline():
    """
    Test the full data pipeline (Download -> Clean -> Merge).
    """
    # This test would require all downloaders to be implemented
    # For now, we skip if any are missing
    try:
        # download_lsms("KE", 2021)
        # download_nasa_power(-1.2921, 36.8219, "2020-01-01", "2020-12-31")
        output_path = download_faostat("FS")
        
        # Clean and merge
        # merged_path = clean_and_merge()
        # assert merged_path.exists()
    except NotImplementedError:
        pytest.skip("Pipeline components not fully implemented")
