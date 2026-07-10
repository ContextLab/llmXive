"""
Integration test for download and merge pipeline.

This test verifies that the full data pipeline (Download -> Clean -> Merge)
executes successfully and produces a valid output file.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data.download import download_faostat, download_lsms, download_nasa_power
from data.clean import clean_and_merge
from utils.config import get_raw_data_dir, get_processed_data_dir

def test_download_faostat_integration():
    """
    Integration test for FAOSTAT download.
    Verifies that the downloader fetches real data and saves it to disk.
    """
    try:
        # Download Food Security indicator (FS)
        output_path = download_faostat("FS")
        
        # Verify file exists and has content
        assert output_path.exists(), f"FAOSTAT output file not created at {output_path}"
        assert output_path.stat().st_size > 0, "FAOSTAT file is empty"
        
        # Verify it's a valid parquet file
        df = pd.read_parquet(output_path)
        assert len(df) > 0, "FAOSTAT dataframe is empty"
        assert "Country" in df.columns or "country" in df.columns, "Missing Country column"
        
    except NotImplementedError:
        pytest.skip("FAOSTAT download not implemented yet")
    except Exception as e:
        pytest.fail(f"FAOSTAT download integration test failed: {str(e)}")

def test_download_lsms_integration():
    """
    Integration test for LSMS download (Kenya 2021).
    """
    try:
        # Test with Kenya, 2021
        output_path = download_lsms("KE", 2021)
        
        # Verify file exists and has content
        assert output_path.exists(), f"LSMS output file not created at {output_path}"
        assert output_path.stat().st_size > 0, "LSMS file is empty"
        
        # Verify it's a valid parquet file
        df = pd.read_parquet(output_path)
        assert len(df) > 0, "LSMS dataframe is empty"
        
    except NotImplementedError:
        pytest.skip("LSMS download not implemented yet")
    except Exception as e:
        pytest.fail(f"LSMS download integration test failed: {str(e)}")

def test_full_pipeline():
    """
    Test the full data pipeline (Download -> Clean -> Merge).
    This is the primary integration test for User Story 1.
    """
    try:
        raw_dir = get_raw_data_dir()
        processed_dir = get_processed_data_dir()
        
        # Ensure directories exist
        raw_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Download FAOSTAT data
        print("Downloading FAOSTAT data...")
        faostat_path = download_faostat("FS")
        assert faostat_path.exists(), "FAOSTAT download failed to create output"
        
        # Step 2: Download LSMS data (Kenya 2021 as a minimal test)
        print("Downloading LSMS data...")
        lsms_path = download_lsms("KE", 2021)
        assert lsms_path.exists(), "LSMS download failed to create output"
        
        # Step 3: Clean and merge
        print("Running clean and merge pipeline...")
        merged_path = clean_and_merge()
        
        # Verify merged output
        assert merged_path.exists(), f"Merged dataset not created at {merged_path}"
        assert merged_path.stat().st_size > 0, "Merged dataset is empty"
        
        # Load and validate merged data
        merged_df = pd.read_parquet(merged_path)
        
        # Basic validation checks
        assert len(merged_df) > 0, "Merged dataframe is empty"
        assert "country" in merged_df.columns or "Country" in merged_df.columns, "Missing country column"
        assert "year" in merged_df.columns or "Year" in merged_df.columns, "Missing year column"
        
        # Check for key expected columns (food security indicators)
        # The exact column names may vary based on data sources
        assert len(merged_df.columns) > 5, "Merged dataframe has too few columns"
        
        print(f"Pipeline test successful! Output: {merged_path}")
        print(f"Dataset shape: {merged_df.shape}")
        print(f"Columns: {list(merged_df.columns[:10])}...")
        
    except NotImplementedError as e:
        pytest.skip(f"Pipeline component not implemented: {str(e)}")
    except Exception as e:
        pytest.fail(f"Full pipeline integration test failed: {str(e)}")

def test_data_integrity():
    """
    Test that downloaded data maintains integrity through the pipeline.
    """
    try:
        # Download fresh data
        faostat_path = download_faostat("FS")
        lsms_path = download_lsms("KE", 2021)
        
        # Run clean and merge
        merged_path = clean_and_merge()
        
        # Load and check for nulls in critical columns
        df = pd.read_parquet(merged_path)
        
        # Check for excessive missing values in key predictors
        critical_cols = [col for col in df.columns if col.lower() in ['food_security', 'income', 'yield']]
        if critical_cols:
            missing_ratio = df[critical_cols].isnull().mean().mean()
            assert missing_ratio < 0.5, f"Too many missing values in critical columns: {missing_ratio:.2%}"
        
    except NotImplementedError:
        pytest.skip("Data integrity test skipped - components not implemented")
    except Exception as e:
        pytest.fail(f"Data integrity test failed: {str(e)}")