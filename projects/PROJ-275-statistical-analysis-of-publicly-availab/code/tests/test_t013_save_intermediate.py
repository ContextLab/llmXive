import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging
import tempfile
import shutil

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_ingestion import save_intermediate_results

class TestT013SaveIntermediate:
    @pytest.fixture
    def sample_dataframe(self):
        """Create a sample dataframe with required columns and >= 500 rows."""
        data = {
            'title': [f'Movie {i}' for i in range(600)],
            'release_date': pd.date_range(start='2020-01-01', periods=600, freq='D'),
            'opening_weekend_revenue': np.random.randint(100000, 10000000, 600),
            'sentiment_score': np.random.uniform(-1, 1, 600),
            'genre': ['Action', 'Comedy', 'Drama'] * 200
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for data/processed and data/logs."""
        base_dir = Path(tempfile.mkdtemp())
        processed_dir = base_dir / "data" / "processed"
        logs_dir = base_dir / "data" / "logs"
        processed_dir.mkdir(parents=True)
        logs_dir.mkdir(parents=True)
        return base_dir, processed_dir, logs_dir

    def test_save_intermediate_creates_parquet(self, sample_dataframe, temp_dirs):
        """Test that the function creates the parquet file."""
        base_dir, processed_dir, logs_dir = temp_dirs
        
        # Patch ensure_directories to use temp dir
        with patch('data_ingestion.ensure_directories') as mock_ensure:
            # Mock the path logic inside the function to use temp dirs
            # This is tricky because the function uses hardcoded paths relative to root.
            # A better approach is to patch the Path construction or run in a temp cwd.
            # For this test, we will assume the function respects the environment or we mock the file write.
            pass

        # Simpler test: Check logic with a mock logger and verify file creation
        # We need to run in a temp directory to avoid polluting the real project structure
        original_cwd = os.getcwd()
        try:
            os.chdir(base_dir)
            # Re-import or reload to pick up new cwd if necessary, but paths are relative to cwd
            # The function uses Path("data/processed") which is relative to cwd.
            
            logger = logging.getLogger("TestLogger")
            logger.setLevel(logging.INFO)
            
            # Mock the ensure_directories to point to our temp dirs if needed, 
            # but since we changed cwd, "data/processed" is now temp_dir/data/processed
            # which exists.
            
            save_intermediate_results(sample_dataframe, logger)
            
            output_path = processed_dir / "merged_clean.parquet"
            assert output_path.exists(), f"Parquet file not created at {output_path}"
            
            # Verify content
            loaded_df = pd.read_parquet(output_path)
            assert len(loaded_df) == 600
            assert 'title' in loaded_df.columns
            assert 'opening_weekend_revenue' in loaded_df.columns
            
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(base_dir)

    def test_save_intermediate_logs_count(self, sample_dataframe, temp_dirs):
        """Test that the function logs row counts to ingestion_log.txt."""
        base_dir, processed_dir, logs_dir = temp_dirs
        log_file_path = logs_dir / "ingestion_log.txt"
        
        original_cwd = os.getcwd()
        try:
            os.chdir(base_dir)
            logger = logging.getLogger("TestLogger2")
            logger.setLevel(logging.INFO)
            
            save_intermediate_results(sample_dataframe, logger)
            
            assert log_file_path.exists(), "Log file not created"
            
            with open(log_file_path, 'r') as f:
                content = f.read()
            
            assert "Row Count: 600" in content
            assert "T013" in content
            
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(base_dir)

    def test_save_intermediate_fails_on_missing_column(self, temp_dirs):
        """Test that the function raises ValueError if a required column is missing."""
        base_dir, processed_dir, logs_dir = temp_dirs
        bad_df = pd.DataFrame({'title': ['A'], 'other': [1]})
        
        original_cwd = os.getcwd()
        try:
            os.chdir(base_dir)
            logger = logging.getLogger("TestLogger3")
            
            with pytest.raises(ValueError, match="Missing required columns"):
                save_intermediate_results(bad_df, logger)
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(base_dir)

    def test_save_intermediate_fails_on_low_row_count(self, temp_dirs):
        """Test that the function raises ValueError if row count < 500."""
        base_dir, processed_dir, logs_dir = temp_dirs
        small_df = pd.DataFrame({
            'title': [f'Movie {i}' for i in range(100)],
            'release_date': pd.date_range(start='2020-01-01', periods=100, freq='D'),
            'opening_weekend_revenue': [1000]*100,
            'sentiment_score': [0.5]*100,
            'genre': ['Action']*100
        })
        
        original_cwd = os.getcwd()
        try:
            os.chdir(base_dir)
            logger = logging.getLogger("TestLogger4")
            
            with pytest.raises(ValueError, match="Row count.*less than required 500"):
                save_intermediate_results(small_df, logger)
        finally:
            os.chdir(original_cwd)
            shutil.rmtree(base_dir)
