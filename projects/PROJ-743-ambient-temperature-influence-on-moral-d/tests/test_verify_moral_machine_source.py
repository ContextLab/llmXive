import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from verify_moral_machine_source import validate_schema, REQUIRED_COLUMNS

class TestVerifyMoralMachineSource:
    
    def test_validate_schema_pass(self):
        """Test that a dataframe with correct columns passes validation."""
        df = pd.DataFrame({
            'latitude': [51.5],
            'longitude': [-0.1],
            'timestamp': ['2016-01-01'],
            'response_time': [1500.0],
            'country': ['UK'],
            'dilemma_id': ['d1']
        })
        
        # Mock logger
        import logging
        logger = logging.getLogger("test")
        
        # Should return True
        assert validate_schema(logger, df) is True

    def test_validate_schema_missing_column(self):
        """Test that a dataframe with missing columns fails validation."""
        df = pd.DataFrame({
            'latitude': [51.5],
            'longitude': [-0.1],
            'timestamp': ['2016-01-01'],
            # Missing response_time, country, dilemma_id
        })
        
        import logging
        logger = logging.getLogger("test")
        
        assert validate_schema(logger, df) is False

    def test_validate_schema_empty_dataframe(self):
        """Test that an empty dataframe fails validation."""
        df = pd.DataFrame(columns=list(REQUIRED_COLUMNS.keys()))
        
        import logging
        logger = logging.getLogger("test")
        
        assert validate_schema(logger, df) is False
