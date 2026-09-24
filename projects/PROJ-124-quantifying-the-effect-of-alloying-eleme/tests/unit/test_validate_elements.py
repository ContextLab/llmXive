import pytest
import pandas as pd
import logging
from pathlib import Path
import sys
import os

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.validate import validate_elements, main
from utils.logger import get_logger

class TestValidateElements:
    """
    Unit tests for the validate_elements function (T016).
    
    Tests verify:
    1. Correct identification of rows with unknown elements.
    2. Correct filtering of valid rows.
    3. Proper logging of warnings for excluded elements.
    4. Accurate statistics reporting.
    """
    
    def test_all_known_elements(self, tmp_path):
        """Test that rows with only known elements are kept."""
        # Setup test data
        data = {
            'composition': ['Fe50Ni30Co20', 'Al60Cu20Zr20', 'Mg50Ca30Zn20'],
            'value': [1, 2, 3]
        }
        df = pd.DataFrame(data)
        
        # Mock logger to capture warnings
        logger = get_logger("test_validate_all_known")
        logger.setLevel(logging.WARNING)
        
        # Run validation
        filtered_df, stats = validate_elements(df, logger)
        
        # Assertions
        assert len(filtered_df) == 3, "All rows should be kept when elements are known."
        assert stats['excluded_rows'] == 0, "No rows should be excluded."
        assert stats['valid_rows'] == 3, "All rows should be valid."
        assert len(stats['excluded_compositions']) == 0, "No compositions should be in excluded list."
    
    def test_unknown_elements_excluded(self, tmp_path):
        """Test that rows with unknown elements are excluded and logged."""
        # Setup test data with an unknown element 'X' (not in abundant set)
        data = {
            'composition': ['Fe50Ni30Co20', 'Xy40Zr30Ti30', 'Al60Cu20Zr20'],
            'value': [1, 2, 3]
        }
        df = pd.DataFrame(data)
        
        # Capture logs
        import io
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setLevel(logging.WARNING)
        logger = get_logger("test_validate_unknown")
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
        
        # Run validation
        filtered_df, stats = validate_elements(df, logger)
        
        # Assertions
        assert len(filtered_df) == 2, "One row with unknown element should be excluded."
        assert stats['excluded_rows'] == 1, "Exactly one row should be excluded."
        assert stats['valid_rows'] == 2, "Two rows should be valid."
        assert 'Xy' in stats['unknown_elements_found'], "Unknown element 'Xy' should be detected."
        assert 'Xy40Zr30Ti30' in stats['excluded_compositions'], "Invalid composition should be in excluded list."
        
        # Check log content
        log_contents = log_stream.getvalue()
        assert "Excluding row" in log_contents, "Log should contain exclusion warning."
        assert "Xy" in log_contents, "Log should mention the unknown element."
    
    def test_multiple_unknown_elements(self, tmp_path):
        """Test handling of multiple unknown elements in different rows."""
        data = {
            'composition': ['Fe50Ni50', 'Au50Xy50', 'Ag50Zz50', 'Pt50Pd50'],
            'value': [1, 2, 3, 4]
        }
        df = pd.DataFrame(data)
        
        logger = get_logger("test_validate_multi_unknown")
        logger.setLevel(logging.WARNING)
        
        filtered_df, stats = validate_elements(df, logger)
        
        assert len(filtered_df) == 2, "Two rows with unknown elements should be excluded."
        assert stats['excluded_rows'] == 2, "Two rows should be excluded."
        assert 'Xy' in stats['unknown_elements_found'], "Xy should be detected."
        assert 'Zz' in stats['unknown_elements_found'], "Zz should be detected."
        assert 'Au50Xy50' in stats['excluded_compositions'], "First invalid composition."
        assert 'Ag50Zz50' in stats['excluded_compositions'], "Second invalid composition."
    
    def test_mixed_case_composition_parsing(self, tmp_path):
        """Test that composition parsing handles standard element symbols correctly."""
        # Standard element symbols: Fe, Ni, Co, Al, Cu, Zr, Mg, Ca, Zn, Ti
        data = {
            'composition': ['Fe50Ni30Co20', 'Al60Cu20Zr20', 'Mg50Ca30Zn20', 'Ti80Ni20'],
            'value': [1, 2, 3, 4]
        }
        df = pd.DataFrame(data)
        
        logger = get_logger("test_validate_mixed")
        
        filtered_df, stats = validate_elements(df, logger)
        
        assert len(filtered_df) == 4, "All standard elements should be recognized."
        assert stats['excluded_rows'] == 0, "No rows should be excluded."
    
    def test_empty_dataframe(self, tmp_path):
        """Test handling of an empty dataframe."""
        df = pd.DataFrame(columns=['composition', 'value'])
        
        logger = get_logger("test_validate_empty")
        
        filtered_df, stats = validate_elements(df, logger)
        
        assert len(filtered_df) == 0, "Empty dataframe should remain empty."
        assert stats['total_rows'] == 0, "Total rows should be 0."
        assert stats['excluded_rows'] == 0, "Excluded rows should be 0."
        assert stats['valid_rows'] == 0, "Valid rows should be 0."
    
    def test_log_verification(self, tmp_path, caplog):
        """Test that specific warnings are logged for excluded rows."""
        data = {
            'composition': ['Fe50Ni50', 'UnknownElement100'],
            'value': [1, 2]
        }
        df = pd.DataFrame(data)
        
        logger = get_logger("test_validate_log")
        logger.setLevel(logging.WARNING)
        
        with caplog.at_level(logging.WARNING):
            validate_elements(df, logger)
        
        # Check that specific log messages were generated
        assert any("Excluding row" in record.message for record in caplog.records), \
            "Should log exclusion message."
        assert any("UnknownElement" in record.message for record in caplog.records), \
            "Should log the unknown element name."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])