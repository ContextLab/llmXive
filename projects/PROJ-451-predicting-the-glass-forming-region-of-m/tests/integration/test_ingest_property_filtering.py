"""
Integration test for property filtering in ingestion pipeline.

Verifies that:
1. Rows with missing elemental properties are correctly dropped
2. The output file is created at the expected path
3. Logging occurs for dropped counts
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.ingest import filter_by_properties
from utils.io import get_processed_data_path, save_csv, load_csv

class TestPropertyFiltering:
    """Test cases for property filtering functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()
        self.original_processed_path = get_processed_data_path()
        
        # Mock the processed data path
        processed_mock = Path(self.temp_dir) / "processed"
        processed_mock.mkdir(parents=True, exist_ok=True)
        
        # Patch the function temporarily
        import utils.io
        self.original_get_path = utils.io.get_processed_data_path
        utils.io.get_processed_data_path = lambda: processed_mock
        
    def teardown_method(self):
        """Clean up test fixtures."""
        # Restore original function
        import utils.io
        utils.io.get_processed_data_path = self.original_get_path
        
        # Remove temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_filter_drops_missing_electronegativity(self):
        """Test that rows with missing electronegativity are dropped."""
        # Create test data with missing electronegativity
        data = {
            'composition': ['Zr50Cu50', 'Cu64Zr36', 'Pd40Ni40P20', 'Fe80B20'],
            'phase': ['amorphous', 'crystalline', 'amorphous', 'crystalline'],
            'electronegativity': [1.5, None, 2.1, 1.8],  # One missing
            'atomic_radius': [160.0, 128.0, 137.0, 126.0],
            'valence_electrons': [4, 11, 10, 8]
        }
        df = pd.DataFrame(data)
        
        # Apply filtering
        result = filter_by_properties(df)
        
        # Verify: Row with missing electronegativity should be dropped
        assert len(result) == 3, f"Expected 3 rows, got {len(result)}"
        assert 'Cu64Zr36' not in result['composition'].values, "Row with missing electronegativity should be dropped"
        
        # Verify all remaining rows have non-null electronegativity
        assert result['electronegativity'].notna().all(), "All remaining rows should have non-null electronegativity"
    
    def test_filter_drops_missing_multiple_properties(self):
        """Test that rows with missing any critical property are dropped."""
        data = {
            'composition': ['Zr50Cu50', 'Cu64Zr36', 'Pd40Ni40P20', 'Fe80B20', 'Ti50Ni50'],
            'phase': ['amorphous', 'crystalline', 'amorphous', 'crystalline', 'amorphous'],
            'electronegativity': [1.5, 1.8, None, 1.8, 1.5],  # One missing
            'atomic_radius': [160.0, None, 137.0, 126.0, 145.0],  # One missing
            'valence_electrons': [4, 11, 10, 8, 10]
        }
        df = pd.DataFrame(data)
        
        result = filter_by_properties(df)
        
        # Verify: 2 rows should be dropped (missing electronegativity or atomic_radius)
        assert len(result) == 3, f"Expected 3 rows, got {len(result)}"
    
    def test_filter_keeps_complete_rows(self):
        """Test that rows with all properties are kept."""
        data = {
            'composition': ['Zr50Cu50', 'Cu64Zr36', 'Pd40Ni40P20'],
            'phase': ['amorphous', 'crystalline', 'amorphous'],
            'electronegativity': [1.5, 1.8, 2.1],
            'atomic_radius': [160.0, 128.0, 137.0],
            'valence_electrons': [4, 11, 10]
        }
        df = pd.DataFrame(data)
        
        result = filter_by_properties(df)
        
        # Verify: All rows should be kept
        assert len(result) == 3, f"Expected 3 rows, got {len(result)}"
    
    def test_filter_creates_output_file(self):
        """Test that the output file is created."""
        data = {
            'composition': ['Zr50Cu50', 'Cu64Zr36'],
            'phase': ['amorphous', 'crystalline'],
            'electronegativity': [1.5, 1.8],
            'atomic_radius': [160.0, 128.0],
            'valence_electrons': [4, 11]
        }
        df = pd.DataFrame(data)
        
        result = filter_by_properties(df)
        
        # Verify output file exists
        output_path = get_processed_data_path() / "filtered_properties.csv"
        assert output_path.exists(), f"Output file not created at {output_path}"
        
        # Verify file content
        saved_df = load_csv(output_path)
        assert len(saved_df) == len(result), "Saved file does not match result"
    
    def test_filter_empty_dataframe(self):
        """Test that empty dataframe is handled correctly."""
        df = pd.DataFrame()
        result = filter_by_properties(df)
        assert result.empty, "Empty dataframe should remain empty"
    
    def test_filter_no_critical_columns(self):
        """Test behavior when no critical property columns exist."""
        data = {
            'composition': ['Zr50Cu50', 'Cu64Zr36'],
            'phase': ['amorphous', 'crystalline']
        }
        df = pd.DataFrame(data)
        
        # Should not raise an error, just return the dataframe unchanged
        result = filter_by_properties(df)
        assert len(result) == 2, "DataFrame should be unchanged when no critical columns exist"
    
    def test_filter_log_count(self):
        """Test that logging occurs for dropped counts."""
        import logging
        from io import StringIO
        
        # Set up log capture
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.INFO)
        logger = logging.getLogger('scripts.ingest')
        logger.addHandler(handler)
        
        data = {
            'composition': ['Zr50Cu50', 'Cu64Zr36', 'Pd40Ni40P20'],
            'phase': ['amorphous', 'crystalline', 'amorphous'],
            'electronegativity': [1.5, None, 2.1],
            'atomic_radius': [160.0, 128.0, 137.0],
            'valence_electrons': [4, 11, 10]
        }
        df = pd.DataFrame(data)
        
        filter_by_properties(df)
        
        # Check log output
        log_contents = log_stream.getvalue()
        assert "Property filtering" in log_contents, "Property filtering should be logged"
        assert "dropped" in log_contents.lower(), "Dropped count should be logged"
        
        logger.removeHandler(handler)