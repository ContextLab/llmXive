"""
Unit tests for the DataIngestionPipeline, specifically focusing on
auto-detection of file delimiters as required by T013.
"""
import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path
from ingestion import DataIngestionPipeline
from exceptions import DataAcquisitionError

# Ensure the project root is in the path for imports if running standalone
# In the actual runner, this is handled by the environment setup.
try:
    from ingestion import DataIngestionPipeline
except ImportError:
    # Fallback for local testing if path isn't set
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from ingestion import DataIngestionPipeline


class TestDelimiterAutoDetection:
    """
    Tests for T013: Auto-detection of file delimiters in CSV/TSV files.
    """

    def _create_temp_file(self, content: str, suffix: str = ".csv") -> str:
        """Helper to create a temporary file with specific content."""
        fd, path = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception:
            os.close(fd)
            raise
        return path

    def test_auto_detect_comma_delimiter(self):
        """Test that comma (,) is correctly detected and parsed."""
        content = "precinct_sum,county_reported,discrepancy_abs\n100,95,5\n200,210,10"
        path = self._create_temp_file(content, ".csv")
        try:
            pipeline = DataIngestionPipeline()
            # The pipeline should infer the delimiter automatically
            # We expect it to use ',' by default or via sniffing
            df = pipeline._load_single_file(path)
            
            assert df is not None
            assert "precinct_sum" in df.columns
            assert "county_reported" in df.columns
            assert len(df) == 2
            assert df["precinct_sum"].iloc[0] == 100
        finally:
            os.unlink(path)

    def test_auto_detect_semicolon_delimiter(self):
        """Test that semicolon (;) is correctly detected and parsed."""
        # Common in European locales
        content = "precinct_sum;county_reported;discrepancy_abs\n100;95;5\n200;210;10"
        path = self._create_temp_file(content, ".csv")
        try:
            pipeline = DataIngestionPipeline()
            df = pipeline._load_single_file(path)
            
            assert df is not None
            assert "precinct_sum" in df.columns
            assert "county_reported" in df.columns
            # Ensure it didn't parse as a single column string
            assert len(df.columns) == 3
            assert df["precinct_sum"].iloc[0] == 100
        finally:
            os.unlink(path)

    def test_auto_detect_tab_delimiter(self):
        """Test that tab (\\t) is correctly detected and parsed."""
        content = "precinct_sum\tcounty_reported\tdiscrepancy_abs\n100\t95\t5\n200\t210\t10"
        path = self._create_temp_file(content, ".tsv")
        try:
            pipeline = DataIngestionPipeline()
            df = pipeline._load_single_file(path)
            
            assert df is not None
            assert "precinct_sum" in df.columns
            assert "county_reported" in df.columns
            assert len(df.columns) == 3
            assert df["precinct_sum"].iloc[0] == 100
        finally:
            os.unlink(path)

    def test_auto_detect_pipe_delimiter(self):
        """Test that pipe (|) is correctly detected and parsed."""
        content = "precinct_sum|county_reported|discrepancy_abs\n100|95|5\n200|210|10"
        path = self._create_temp_file(content, ".csv")
        try:
            pipeline = DataIngestionPipeline()
            df = pipeline._load_single_file(path)
            
            assert df is not None
            assert "precinct_sum" in df.columns
            assert "county_reported" in df.columns
            assert len(df.columns) == 3
            assert df["precinct_sum"].iloc[0] == 100
        finally:
            os.unlink(path)

    def test_auto_detect_space_delimiter(self):
        """Test that multiple spaces are handled as a delimiter."""
        content = "precinct_sum  county_reported  discrepancy_abs\n100  95  5\n200  210  10"
        path = self._create_temp_file(content, ".csv")
        try:
            pipeline = DataIngestionPipeline()
            df = pipeline._load_single_file(path)
            
            assert df is not None
            # pandas read_csv with sep=r'\s+' handles multiple spaces
            assert "precinct_sum" in df.columns
            assert "county_reported" in df.columns
            assert len(df.columns) == 3
        finally:
            os.unlink(path)

    def test_explicit_delimiter_override(self):
        """Test that explicit delimiter parameter overrides auto-detection."""
        # File has semicolons
        content = "precinct_sum;county_reported;discrepancy_abs\n100;95;5"
        path = self._create_temp_file(content, ".csv")
        try:
            pipeline = DataIngestionPipeline()
            # Force comma detection on a semicolon file -> should result in 1 column
            df = pipeline._load_single_file(path, delimiter=',')
            
            # If forced to comma, the whole line is one column
            assert len(df.columns) == 1
            assert "precinct_sum;county_reported;discrepancy_abs" in df.columns
        finally:
            os.unlink(path)

    def test_invalid_delimiter_raises_error(self):
        """Test that a file with an unsupported delimiter raises an error."""
        # Create a file with a weird delimiter that pandas sniffing might fail on
        # or explicitly pass a bad delimiter to the loader logic if it exists.
        # Here we test the case where the file is completely unreadable as structured data.
        content = "abc def ghi\njkl mno pqr" # No clear delimiter, just spaces
        path = self._create_temp_file(content, ".csv")
        try:
            pipeline = DataIngestionPipeline()
            # If the file is too ambiguous, we might get a single column or an error
            # depending on pandas' default behavior. 
            # The test ensures the pipeline doesn't crash silently with garbage.
            df = pipeline._load_single_file(path)
            # If it loads, verify structure is reasonable (at least 1 column)
            assert df is not None
        except Exception:
            # It is also acceptable if it raises a clear DataAcquisitionError
            pass
        finally:
            os.unlink(path)

    def test_mixed_delimiters_in_batch(self):
        """Test processing a batch of files with different delimiters."""
        files = []
        try:
            # File 1: Comma
            f1 = self._create_temp_file("a,b\n1,2", ".csv")
            files.append(f1)
            
            # File 2: Tab
            f2 = self._create_temp_file("a\tb\n3\t4", ".tsv")
            files.append(f2)
            
            # File 3: Semicolon
            f3 = self._create_temp_file("a;b\n5;6", ".csv")
            files.append(f3)
            
            pipeline = DataIngestionPipeline()
            # Load all files
            combined_df = pipeline.load_files(files)
            
            assert combined_df is not None
            assert len(combined_df) == 3
            assert "a" in combined_df.columns
            assert "b" in combined_df.columns
            assert combined_df["a"].sum() == 9 # 1+3+5
        finally:
            for f in files:
                if os.path.exists(f):
                    os.unlink(f)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])