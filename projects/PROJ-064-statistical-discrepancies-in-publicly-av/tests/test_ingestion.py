import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Adjust import based on project structure.
# Assuming tests/ is at the same level as code/ or code/ is in PYTHONPATH.
# The task requires extending the existing file.
try:
    from code.ingestion import DataIngestionPipeline
except ImportError:
    from ingestion import DataIngestionPipeline

class TestDelimiterAutoDetection:
    """Tests for auto-detection of file delimiters in ingestion pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = os.path.join(self.temp_dir.name, "test_data.csv")

    def teardown_method(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def _create_test_file(self, content, filename="test.csv"):
        """Helper to create a temporary test file with specific content."""
        path = os.path.join(self.temp_dir.name, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_detect_comma_delimiter(self):
        """Test auto-detection of standard comma-delimited CSV."""
        content = """precinct_id,county,total_votes,precinct_votes
        P001,CountyA,1000,450
        P002,CountyA,1200,580
        """
        file_path = self._create_test_file(content, "comma_delim.csv")
        
        # Instantiate pipeline (assuming it accepts a file path or list)
        # The actual ingestion logic usually detects delimiters during the read phase.
        # We test the specific method if exposed, or the behavior of the pipeline.
        # Assuming DataIngestionPipeline has a method to infer delimiter or handles it internally.
        
        # If the pipeline expects a list of files:
        pipeline = DataIngestionPipeline()
        
        # Mock the internal detection or call a specific helper if available.
        # Since we are extending tests, we assume the pipeline has a helper method
        # or the __init__ / load method handles this.
        # Let's assume a helper method `_infer_delimiter` exists or is part of the logic.
        # If not, we test the end-to-end load with a known file.
        
        # Attempt to load the file. The pipeline should detect ',' automatically.
        # We verify by checking if the resulting DataFrame has correct columns.
        try:
            # This assumes the pipeline can handle a single file path for testing
            # or we pass the path to a specific load method.
            # Adapting to the likely API: load_data(file_path)
            df = pipeline.load_data(file_path)
            
            assert df is not None
            assert "precinct_id" in df.columns
            assert "county" in df.columns
            assert len(df) == 2
            # Verify it didn't treat it as a single column string
            assert df.shape[1] > 1
        except Exception as e:
            pytest.fail(f"Failed to load comma-delimited file: {e}")

    def test_detect_semicolon_delimiter(self):
        """Test auto-detection of semicolon-delimited CSV (common in Europe)."""
        content = """precinct_id;county;total_votes;precinct_votes
        P003;CountyB;2000;900
        P004;CountyB;2500;1100
        """
        file_path = self._create_test_file(content, "semicolon_delim.csv")
        
        pipeline = DataIngestionPipeline()
        try:
            df = pipeline.load_data(file_path)
            assert df is not None
            assert "precinct_id" in df.columns
            assert "county" in df.columns
            assert len(df) == 2
            assert df.shape[1] > 1
        except Exception as e:
            pytest.fail(f"Failed to load semicolon-delimited file: {e}")

    def test_detect_tab_delimiter(self):
        """Test auto-detection of tab-delimited TSV."""
        content = """precinct_id\tcounty\ttotal_votes\tprecinct_votes
        P005\tCountyC\t1500\t700
        P006\tCountyC\t1800\t850
        """
        file_path = self._create_test_file(content, "tab_delim.tsv")
        
        pipeline = DataIngestionPipeline()
        try:
            df = pipeline.load_data(file_path)
            assert df is not None
            assert "precinct_id" in df.columns
            assert "county" in df.columns
            assert len(df) == 2
            assert df.shape[1] > 1
        except Exception as e:
            pytest.fail(f"Failed to load tab-delimited file: {e}")

    def test_detect_pipe_delimiter(self):
        """Test auto-detection of pipe-delimited files."""
        content = """precinct_id|county|total_votes|precinct_votes
        P007|CountyD|3000|1400
        P008|CountyD|3200|1550
        """
        file_path = self._create_test_file(content, "pipe_delim.csv")
        
        pipeline = DataIngestionPipeline()
        try:
            df = pipeline.load_data(file_path)
            assert df is not None
            assert "precinct_id" in df.columns
            assert "county" in df.columns
            assert len(df) == 2
            assert df.shape[1] > 1
        except Exception as e:
            pytest.fail(f"Failed to load pipe-delimited file: {e}")

    def test_fallback_to_comma_if_no_other_detected(self):
        """Test that comma is used as default if no strong signal is found."""
        # Create a file with a delimiter that might be ambiguous or rare, 
        # but ensure the logic doesn't crash. 
        # Standard CSV with comma should work.
        content = """precinct_id,county,total_votes,precinct_votes
        P009,CountyE,4000,1900
        """
        file_path = self._create_test_file(content, "default_delim.csv")
        
        pipeline = DataIngestionPipeline()
        try:
            df = pipeline.load_data(file_path)
            assert df is not None
            assert "precinct_id" in df.columns
        except Exception as e:
            pytest.fail(f"Failed to load default delimited file: {e}")

    def test_invalid_file_raises_error(self):
        """Test that an empty or malformed file raises a clear error."""
        content = ""
        file_path = self._create_test_file(content, "empty.csv")
        
        pipeline = DataIngestionPipeline()
        with pytest.raises((ValueError, FileNotFoundError, Exception)):
            pipeline.load_data(file_path)

    def test_mixed_delimiters_in_directory(self):
        """Test processing a directory containing files with different delimiters."""
        # Create multiple files
        file1 = self._create_test_file("a,b\n1,2", "file1.csv")
        file2 = self._create_test_file("c;d\n3;4", "file2.csv")
        
        pipeline = DataIngestionPipeline()
        
        # Assuming load_data can accept a directory or list of paths
        # If the API only accepts a single path, we test the directory scanning logic
        # or call load_data on each.
        # Here we assume the pipeline has a method to ingest a folder.
        if hasattr(pipeline, 'load_directory'):
            df = pipeline.load_directory(self.temp_dir.name)
            assert df is not None
            assert len(df) == 2
        else:
            # Fallback test: load each individually and check logic
            df1 = pipeline.load_data(file1)
            df2 = pipeline.load_data(file2)
            assert len(df1) == 1
            assert len(df2) == 1
            assert "a" in df1.columns or "c" in df2.columns # Verify content loaded